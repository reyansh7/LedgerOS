"""Objective benchmark metrics calculation against FinRCA hidden ground truth."""

from __future__ import annotations

from typing import Any, Dict, List
from evaluation.ground_truth import GroundTruthCase


def compute_benchmark_metrics(
    detected_exceptions: list[dict[str, Any]],
    ground_truth_cases: list[GroundTruthCase],
    matched_records_count: int,
) -> dict[str, Any]:
    """Calculate detection recall, precision, false reconciliation rate, and category accuracy."""
    gt_by_primary: dict[str, GroundTruthCase] = {
        case.primary_entity_id: case for case in ground_truth_cases
    }
    gt_by_case_id: dict[str, GroundTruthCase] = {
        case.case_id: case for case in ground_truth_cases
    }

    total_gt = len(ground_truth_cases)
    tp_cases: set[str] = set()
    category_matches: int = 0
    fp_count: int = 0

    detected_by_category: dict[str, int] = {}
    gt_by_category: dict[str, int] = {}
    for case in ground_truth_cases:
        gt_by_category[case.failure_type] = gt_by_category.get(case.failure_type, 0) + 1

    for exc in detected_exceptions:
        entity_id = exc.get("primary_entity_id")
        f_type = exc.get("failure_type")
        detected_by_category[f_type] = detected_by_category.get(f_type, 0) + 1

        matched_case = gt_by_primary.get(entity_id)
        if matched_case:
            tp_cases.add(matched_case.case_id)
            if matched_case.failure_type == f_type or f_type in matched_case.failure_type:
                category_matches += 1
        else:
            # Also check if primary_entity matches any affected entity in ground truth
            found = False
            for case in ground_truth_cases:
                affected_ids = [a["id"] for a in case.affected_entities] + case.evidence_ids
                if entity_id in affected_ids:
                    tp_cases.add(case.case_id)
                    found = True
                    if case.failure_type == f_type:
                        category_matches += 1
                    break
            if not found:
                fp_count += 1

    true_positives = len(tp_cases)
    false_negatives = max(0, total_gt - true_positives)

    recall = (true_positives / total_gt * 100.0) if total_gt > 0 else 0.0
    precision = (true_positives / (true_positives + fp_count) * 100.0) if (true_positives + fp_count) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    total_ops = matched_records_count + len(detected_exceptions)
    match_rate = (matched_records_count / total_ops * 100.0) if total_ops > 0 else 0.0
    # False reconciliation rate: Erroneous matches (target < 0.05%)
    false_rec_rate = (false_negatives / total_ops * 100.0) if total_ops > 0 else 0.0

    return {
        "benchmark_ground_truth_total": total_gt,
        "true_positives_detected": true_positives,
        "false_negatives": false_negatives,
        "false_positives": fp_count,
        "detection_recall_pct": round(recall, 2),
        "detection_precision_pct": round(precision, 2),
        "detection_f1_score": round(f1, 2),
        "match_rate_pct": round(match_rate, 2),
        "false_reconciliation_rate_pct": round(false_rec_rate, 4),
        "category_accuracy_pct": round((category_matches / true_positives * 100.0), 2) if true_positives > 0 else 0.0,
        "ground_truth_by_category": gt_by_category,
        "detected_by_category": detected_by_category,
    }
