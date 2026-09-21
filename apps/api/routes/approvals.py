"""Human-in-the-loop approval workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models.governance import ApprovalRequest, AgentAction
from core.models.reconciliation import ExceptionCase
from core.audit.logger import audit_logger
from core.governance.rbac import Permission
from apps.api.auth import require_permission, UserIdentity
from agents.tools.action_tools import (
    execute_void_invoice,
    execute_recovery_case,
    execute_simulated_refund,
)

router = APIRouter(prefix="/approvals", tags=["Human Approvals"])


class ApprovalActionPayload(BaseModel):
    verdict: str  # APPROVED, REJECTED
    reviewer: str = "Finance Controller"
    comment: str | None = None


@router.get("")
async def list_pending_approvals(db: AsyncSession = Depends(get_db)):
    reqs = (
        await db.execute(
            select(ApprovalRequest)
            .order_by(desc(ApprovalRequest.created_at))
        )
    ).scalars().all()
    return [
        {
            "approval_id": r.approval_id,
            "action_id": r.action_id,
            "case_id": r.case_id,
            "action_type": r.action_type,
            "amount": float(r.amount),
            "currency": r.currency,
            "reason": r.reason,
            "policy_citation": r.policy_citation,
            "status": r.status,
            "created_at": r.created_at,
            "reviewed_by": r.reviewed_by,
            "review_comment": r.review_comment,
        }
        for r in reqs
    ]


@router.post("/{approval_id}/action")
async def review_approval(
    approval_id: str,
    payload: ApprovalActionPayload,
    user: UserIdentity = Depends(require_permission(Permission.APPROVE_ACTION)),
    db: AsyncSession = Depends(get_db),
):
    req = (
        await db.execute(select(ApprovalRequest).where(ApprovalRequest.approval_id == approval_id))
    ).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    timestamp = datetime.now(timezone.utc).isoformat()
    req.status = payload.verdict.upper()
    req.reviewed_by = user.email or user.user_id or payload.reviewer
    req.review_comment = payload.comment
    req.reviewed_at = timestamp

    # Execute action if approved
    execution_result = {}
    execution_outcome = "REJECTED"
    if req.status == "APPROVED":
        if req.action_type == "VOID_INVOICE":
            execution_result = execute_void_invoice(req.case_id.replace("EXC_F01_", ""), payload.comment or "Manager approved void")
        elif req.action_type == "SIMULATE_REFUND":
            execution_result = execute_simulated_refund(req.case_id, float(req.amount), payload.comment or "Manager approved refund")
        else:
            execution_result = execute_recovery_case(req.case_id, float(req.amount), payload.comment or "Manager approved recovery")

        v_status = execution_result.get("verification_status", "VERIFIED")
        if not execution_result.get("success", False) or v_status == "VERIFICATION_FAILED":
            execution_outcome = "VERIFICATION_FAILED"
        else:
            execution_outcome = "SUCCESS"

        # Resolve associated exception case
        case = (await db.execute(select(ExceptionCase).where(ExceptionCase.case_id == req.case_id))).scalar_one_or_none()
        if case:
            case.status = "RESOLVED" if execution_outcome == "SUCCESS" else "VERIFICATION_FAILED"

    # Log to immutable audit ledger
    audit_logger.log_event(
        agent_name="human_approver",
        action_type=req.action_type,
        case_id=req.case_id,
        input_payload={"approval_id": approval_id, "reviewer": payload.reviewer, "comment": payload.comment},
        evidence_ids=[req.case_id],
        decision=req.status,
        policy_code=req.policy_citation,
        confidence_score=1.0,
        human_approval=True,
        human_reviewer=payload.reviewer,
        execution_result=execution_outcome,
    )

    await db.commit()
    return {
        "approval_id": approval_id,
        "status": req.status,
        "reviewed_at": timestamp,
        "execution_result": execution_result,
    }
