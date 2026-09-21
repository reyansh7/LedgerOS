"""Exceptions, AI investigations, and real-time SSE activity streaming."""

from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, SyncSessionLocal
from core.models.reconciliation import ExceptionCase
from core.retrieval.provenance_graph import ProvenanceGraphRetriever
from agents.graph import investigation_graph
from apps.api.sse.manager import sse_manager

router = APIRouter(tags=["Investigations & Exceptions"])


@router.get("/exceptions")
async def list_exceptions(
    failure_type: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(ExceptionCase).order_by(desc(ExceptionCase.created_at))
    if failure_type:
        query = query.where(ExceptionCase.failure_type == failure_type)
    if status:
        query = query.where(ExceptionCase.status == status)

    query = query.offset(offset).limit(limit)
    cases = (await db.execute(query)).scalars().all()
    return [
        {
            "case_id": c.case_id,
            "failure_type": c.failure_type,
            "primary_entity_type": c.primary_entity_type,
            "primary_entity_id": c.primary_entity_id,
            "counterparty_id": c.counterparty_id,
            "amount_at_risk": float(c.amount_at_risk),
            "currency": c.currency,
            "observed_symptom": c.observed_symptom,
            "status": c.status,
            "severity": c.severity,
            "root_cause": c.root_cause,
            "created_at": c.created_at,
        }
        for c in cases
    ]


@router.get("/exceptions/{case_id}")
async def get_exception_detail(case_id: str, db: AsyncSession = Depends(get_db)):
    case = (await db.execute(select(ExceptionCase).where(ExceptionCase.case_id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Exception case not found.")

    with SyncSessionLocal() as sync_session:
        retriever = ProvenanceGraphRetriever(sync_session)
        subgraph = retriever.get_provenance_subgraph(
            primary_entity_type=case.primary_entity_type,
            primary_entity_id=case.primary_entity_id,
            max_hops=3,
        )

    return {
        "case_id": case.case_id,
        "failure_type": case.failure_type,
        "primary_entity_type": case.primary_entity_type,
        "primary_entity_id": case.primary_entity_id,
        "counterparty_id": case.counterparty_id,
        "amount_at_risk": float(case.amount_at_risk),
        "currency": case.currency,
        "observed_symptom": case.observed_symptom,
        "status": case.status,
        "severity": case.severity,
        "root_cause": case.root_cause,
        "recommended_action": case.recommended_action,
        "provenance_subgraph": subgraph,
    }


@router.post("/investigations/{case_id}/start")
async def start_investigation(case_id: str, db: AsyncSession = Depends(get_db)):
    case = (await db.execute(select(ExceptionCase).where(ExceptionCase.case_id == case_id))).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Exception case not found.")

    initial_state = {
        "case_id": case.case_id,
        "failure_type": case.failure_type,
        "primary_entity_type": case.primary_entity_type,
        "primary_entity_id": case.primary_entity_id,
        "amount_at_risk": float(case.amount_at_risk),
        "observed_symptom": case.observed_symptom,
        "activity_log": [],
    }

    # Execute LangGraph investigation
    final_state = investigation_graph.invoke(initial_state)

    # Update case status in DB
    case.status = "AWAITING_APPROVAL" if final_state.get("is_paused_for_approval") else "RESOLVED"
    case.root_cause = final_state.get("root_cause")
    proposed = final_state.get("proposed_action")
    if proposed:
        case.recommended_action = f"{proposed.get('action_type')}: {proposed.get('rationale')}"
    await db.commit()

    # Broadcast completed milestones to SSE channel if active
    for m in final_state.get("activity_log", []):
        await sse_manager.broadcast(case_id, m)

    return {
        "case_id": case_id,
        "status": case.status,
        "root_cause": final_state.get("root_cause"),
        "confidence_score": final_state.get("confidence_score"),
        "policy_verdict": final_state.get("policy_verdict"),
        "is_paused_for_approval": final_state.get("is_paused_for_approval"),
        "approval_id": final_state.get("approval_id"),
        "activity_log": final_state.get("activity_log", []),
    }


@router.get("/investigations/{case_id}/stream")
async def stream_investigation_activity(case_id: str):
    """Server-Sent Events stream for live agent execution milestones."""
    return StreamingResponse(
        sse_manager.subscribe(case_id),
        media_type="text/event-stream",
    )
