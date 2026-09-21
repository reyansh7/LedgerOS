"""Benchmark evaluation endpoints evaluating against FinRCA ground truth."""

from __future__ import annotations

from fastapi import APIRouter, Query
from evaluation.runner import evaluation_runner

router = APIRouter(prefix="/evaluations", tags=["Evaluations & Benchmarks"])


@router.get("/run")
async def run_evaluation(split: str | None = Query(None, description="Optional split: train, validation, test")):
    """Runs ground-truth evaluation and returns precision, recall, and false reconciliation rates."""
    metrics = evaluation_runner.run_benchmark(split=split)
    return metrics
