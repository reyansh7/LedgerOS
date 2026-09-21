"""Dashboard statistics and live summary endpoints."""

from __future__ import annotations

from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models.reconciliation import ExceptionCase, ReconciliationMatch, ReconciliationRun
from core.models.governance import ApprovalRequest, AuditTrailEvent

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Latest run
    latest_run = (
        await db.execute(select(ReconciliationRun).order_by(desc(ReconciliationRun.started_at)).limit(1))
    ).scalar_one_or_none()

    # Total open exceptions
    exceptions_count = (
        await db.execute(select(func.count(ExceptionCase.case_id)).where(ExceptionCase.status != "RESOLVED"))
    ).scalar() or 0

    # Total amount at risk
    amount_at_risk = (
        await db.execute(
            select(func.sum(ExceptionCase.amount_at_risk)).where(ExceptionCase.status != "RESOLVED")
        )
    ).scalar() or Decimal("0.0")

    # Total reconciled financial volume from matched transaction pairs
    total_reconciled_volume = (
        await db.execute(select(func.sum(ReconciliationMatch.amount1)))
    ).scalar() or Decimal("0.0")

    # Pending approvals count
    pending_approvals = (
        await db.execute(select(func.count(ApprovalRequest.approval_id)).where(ApprovalRequest.status == "PENDING"))
    ).scalar() or 0

    # Recent Audit Log Activity
    recent_events = (
        await db.execute(select(AuditTrailEvent).order_by(desc(AuditTrailEvent.timestamp)).limit(8))
    ).scalars().all()

    return {
        "match_rate": float(latest_run.match_rate) if latest_run else 0.0,
        "matched_records": latest_run.matched_records if latest_run else 0,
        "total_records": latest_run.total_records if latest_run else 0,
        "reconciled_volume": float(total_reconciled_volume),
        "open_exceptions": exceptions_count,
        "amount_at_risk": float(amount_at_risk),
        "pending_approvals": pending_approvals,
        "recent_activity": [
            {
                "audit_id": e.audit_id,
                "agent_name": e.agent_name,
                "action_type": e.action_type,
                "case_id": e.case_id,
                "decision": e.decision,
                "timestamp": e.timestamp,
                "hash": e.hash_digest[:12] + "...",
            }
            for e in recent_events
        ],
    }
