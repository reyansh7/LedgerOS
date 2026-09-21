"""Audit ledger exploration endpoints."""

from __future__ import annotations

import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models.governance import AuditTrailEvent

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("")
async def list_audit_events(
    agent_name: str | None = None,
    action_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditTrailEvent).order_by(desc(AuditTrailEvent.timestamp))
    if agent_name:
        query = query.where(AuditTrailEvent.agent_name == agent_name)
    if action_type:
        query = query.where(AuditTrailEvent.action_type == action_type)

    events = (await db.execute(query.offset(offset).limit(limit))).scalars().all()
    return [
        {
            "audit_id": e.audit_id,
            "agent_name": e.agent_name,
            "action_type": e.action_type,
            "case_id": e.case_id,
            "decision": e.decision,
            "policy_code": e.policy_code,
            "confidence_score": float(e.confidence_score),
            "human_approval": e.human_approval,
            "human_reviewer": e.human_reviewer,
            "execution_result": e.execution_result,
            "hash_digest": e.hash_digest,
            "previous_hash": e.previous_hash,
            "timestamp": e.timestamp,
        }
        for e in events
    ]


@router.get("/verify")
async def verify_audit_chain():
    """Independently verifies cryptographic SHA-256 hash chaining across the entire audit ledger."""
    from core.audit.logger import audit_logger
    return audit_logger.verify_chain()

