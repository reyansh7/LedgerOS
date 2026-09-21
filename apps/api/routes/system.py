"""System Control Room, Connector Discovery, Guardrails, and Decision Receipts."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models.reconciliation import ExceptionCase, ReconciliationMatch, ReconciliationRun
from core.models.governance import ApprovalRequest, AuditTrailEvent
from core.adapters.registry import adapter_registry
from core.policies.engine import policy_engine
from core.audit.logger import audit_logger
from core.governance.guardrails import get_active_guardrails
from core.governance.receipts import decision_receipt_service

router = APIRouter(prefix="/system", tags=["System & Governance"])


@router.get("/control-room")
async def get_control_room_status(db: AsyncSession = Depends(get_db)):
    """System-level operational telemetry and health status across all engines and connectors."""
    # 1. Database Health
    db_start = time.perf_counter()
    try:
        total_exceptions = (
            await db.execute(select(func.count(ExceptionCase.case_id)))
        ).scalar() or 0
        db_latency = round((time.perf_counter() - db_start) * 1000.0, 2)
        db_status = "HEALTHY"
    except Exception as e:
        db_latency = 0.0
        db_status = "OFFLINE"
        total_exceptions = 0

    # 2. Reconciliation Engine Health
    latest_run = (
        await db.execute(select(ReconciliationRun).order_by(ReconciliationRun.started_at.desc()).limit(1))
    ).scalar_one_or_none()
    rec_status = "HEALTHY" if latest_run else "IDLE"

    # 3. Audit Ledger Integrity
    audit_check = audit_logger.verify_chain()
    audit_status = "HEALTHY" if audit_check["valid"] else "DEGRADED"

    # 4. Approvals
    pending_approvals = (
        await db.execute(select(func.count(ApprovalRequest.approval_id)).where(ApprovalRequest.status == "PENDING"))
    ).scalar() or 0

    # 5. Connector Statuses
    connectors_summary = adapter_registry.get_connectors_status()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "HEALTHY" if (db_status == "HEALTHY" and audit_check["valid"]) else "DEGRADED",
        "components": {
            "reconciliation_engine": {
                "name": "Deterministic 5-Stage Matcher",
                "status": rec_status,
                "last_run": latest_run.started_at if latest_run else None,
                "matched_records": latest_run.matched_records if latest_run else 0,
                "match_rate": float(latest_run.match_rate) if latest_run else 0.0,
            },
            "agent_orchestrator": {
                "name": "LangGraph Causal Investigator",
                "status": "HEALTHY",
                "model_routing": "Deterministic StateGraph + Groq LLM",
                "checkpoints": "Synchronous MemorySaver",
            },
            "policy_engine": {
                "name": "Deterministic Financial Policy Gate",
                "status": "HEALTHY",
                "version": policy_engine.version,
                "rules_loaded": len(policy_engine.rules.get("thresholds", {})),
            },
            "approval_service": {
                "name": "Human-in-the-Loop Governance",
                "status": "HEALTHY",
                "pending_approvals": pending_approvals,
            },
            "audit_ledger": {
                "name": "Immutable SHA-256 Chained Ledger",
                "status": audit_status,
                "verified_blocks": audit_check.get("verified_blocks", 0),
                "is_chain_valid": audit_check["valid"],
            },
            "database": {
                "name": "Enterprise Operational Store",
                "status": db_status,
                "latency_ms": db_latency,
            },
        },
        "connectors": connectors_summary,
        "active_guardrails_count": len(get_active_guardrails()),
    }


@router.get("/connectors")
async def list_connectors():
    """Returns registered enterprise connectors, supported financial capabilities, and health."""
    return adapter_registry.get_connectors_status()


@router.get("/guardrails")
async def list_guardrails():
    """Returns all enforced operational and security guardrails."""
    return get_active_guardrails()


@router.get("/receipts/{case_id}")
async def get_decision_receipt(case_id: str):
    """Generates an immutable, explainable Decision Receipt for any financial case."""
    receipt = decision_receipt_service.generate_receipt_for_case(case_id)
    if not receipt:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return receipt.to_dict()
