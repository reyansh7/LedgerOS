"""Runs evaluation benchmark and generates performance reports."""

from __future__ import annotations

import json
from typing import Any, Optional
from sqlalchemy import select

from core.database import SyncSessionLocal
from core.models.reconciliation import ExceptionCase, ReconciliationMatch, ReconciliationRun
from evaluation.ground_truth import evaluator_ground_truth
from evaluation.metrics import compute_benchmark_metrics


class EvaluationRunner:
    """Evaluates reconciliation engine performance against the public FinRCA research ground truth."""

    def run_benchmark(self, split: Optional[str] = None) -> dict[str, Any]:
        # 1. Load hidden ground truth (Evaluator only)
        gt_cases = evaluator_ground_truth.all_cases(split=split)
        if not gt_cases:
            evaluator_ground_truth.load()
            gt_cases = evaluator_ground_truth.all_cases(split=split)

        # 2. Query operational exceptions and matches
        with SyncSessionLocal() as session:
            exceptions = session.execute(select(ExceptionCase)).scalars().all()
            matches_count = len(session.execute(select(ReconciliationMatch)).scalars().all())

            exc_dicts = [
                {
                    "case_id": e.case_id,
                    "failure_type": e.failure_type,
                    "primary_entity_id": e.primary_entity_id,
                    "primary_entity_type": e.primary_entity_type,
                    "amount_at_risk": float(e.amount_at_risk),
                    "status": e.status,
                }
                for e in exceptions
            ]

        # 3. Compute objective metrics
        import uuid
        from datetime import datetime, timezone
        metrics = compute_benchmark_metrics(exc_dicts, gt_cases, matches_count)
        metrics["run_id"] = f"EVAL-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:6].upper()}"
        metrics["evaluated_split"] = split or "all"
        metrics["evaluated_subset_name"] = f"LedgerOS Evaluation Subset: {len(gt_cases)} Cases"
        metrics["total_exceptions_in_db"] = len(exc_dicts)
        metrics["total_matches_in_db"] = matches_count

        return metrics


evaluation_runner = EvaluationRunner()

if __name__ == "__main__":
    rep = evaluation_runner.run_benchmark()
    print("Benchmark Evaluation Report against FinRCA Ground Truth:")
    print(f"  Ground Truth Injected Cases: {rep['benchmark_ground_truth_total']}")
    print(f"  True Positives Detected: {rep['true_positives_detected']}")
    print(f"  Detection Recall: {rep['detection_recall_pct']}%")
    print(f"  Match Rate: {rep['match_rate_pct']}%")
    print(f"  False Reconciliation Rate: {rep['false_reconciliation_rate_pct']}%")
    print(f"  Category Classification Accuracy: {rep['category_accuracy_pct']}%")
