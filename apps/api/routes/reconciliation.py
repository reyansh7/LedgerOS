"""Reconciliation triggers and matches endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models.reconciliation import ReconciliationMatch, ReconciliationRun
from core.reconciliation.engine import reconciliation_engine

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.post("/run")
async def run_reconciliation():
    """Trigger the deterministic multi-stage reconciliation engine."""
    res = reconciliation_engine.run()
    return res


@router.get("/runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    runs = (await db.execute(select(ReconciliationRun).order_by(desc(ReconciliationRun.started_at)).limit(10))).scalars().all()
    return [
        {
            "run_id": r.run_id,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "matched_records": r.matched_records,
            "total_records": r.total_records,
            "match_rate": float(r.match_rate),
            "total_exceptions": r.total_exceptions,
            "amount_at_risk": float(r.amount_at_risk),
            "status": r.status,
        }
        for r in runs
    ]


@router.get("/matches")
async def list_matches(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    matches = (
        await db.execute(
            select(ReconciliationMatch)
            .order_by(desc(ReconciliationMatch.matched_at))
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "match_id": m.match_id,
            "run_id": m.run_id,
            "match_type": m.match_type,
            "entity1": f"{m.entity1_type}:{m.entity1_id}",
            "entity2": f"{m.entity2_type}:{m.entity2_id}",
            "amount1": float(m.amount1),
            "amount2": float(m.amount2),
            "variance": float(m.variance),
            "confidence": float(m.confidence),
            "matched_at": m.matched_at,
        }
        for m in matches
    ]
