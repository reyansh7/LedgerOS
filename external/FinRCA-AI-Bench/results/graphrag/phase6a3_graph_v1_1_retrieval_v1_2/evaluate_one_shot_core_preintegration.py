#!/usr/bin/env python3
"""Phase 6A.3 Graph v1.1 one-shot evaluator.

At this stage this file contains only deterministic, gold-free evaluation
primitives. Validation-gold loading is intentionally not implemented yet.
"""

from __future__ import annotations

from collections import Counter
import random
import statistics
from typing import Any, Mapping, Sequence

from scipy.stats import binomtest

from src.rag.tokens import percentile


BOOTSTRAP_SEED = 20260809
BOOTSTRAP_RESAMPLES = 10_000
EXPECTED_CASE_COUNT = 416
MAX_SELECTED_RECORDS = 40


def _assert_same_cases(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> list[str]:
    left_ids = set(left)
    right_ids = set(right)
    if left_ids != right_ids:
        raise RuntimeError(
            "case universes differ: "
            f"left_only={sorted(left_ids - right_ids)} "
            f"right_only={sorted(right_ids - left_ids)}"
        )
    return sorted(left_ids)


def paired_bootstrap_mean(values: Sequence[float]) -> dict[str, float]:
    """Deterministic percentile CI over already-paired case-level values."""
    if not values:
        return {
            "mean": 0.0,
            "lower_95": 0.0,
            "upper_95": 0.0,
            "seed": BOOTSTRAP_SEED,
            "resamples": BOOTSTRAP_RESAMPLES,
        }

    generator = random.Random(BOOTSTRAP_SEED)
    samples: list[float] = []

    for _ in range(BOOTSTRAP_RESAMPLES):
        samples.append(
            statistics.fmean(
                values[generator.randrange(len(values))]
                for _ in range(len(values))
            )
        )

    return {
        "mean": statistics.fmean(values),
        "lower_95": percentile(samples, 0.025),
        "upper_95": percentile(samples, 0.975),
        "seed": BOOTSTRAP_SEED,
        "resamples": BOOTSTRAP_RESAMPLES,
    }


def paired_recall_summary(
    graph_recall: Mapping[str, float],
    relational_recall: Mapping[str, float],
) -> dict[str, Any]:
    """Compare Graph and Relational per-case required-record recall."""
    case_ids = _assert_same_cases(graph_recall, relational_recall)

    graph_values = [float(graph_recall[case_id]) for case_id in case_ids]
    relational_values = [
        float(relational_recall[case_id]) for case_id in case_ids
    ]
    differences = [
        graph - relational
        for graph, relational in zip(graph_values, relational_values)
    ]

    counts = Counter()
    case_rows = []

    for case_id in case_ids:
        graph = float(graph_recall[case_id])
        relational = float(relational_recall[case_id])

        if graph > relational:
            outcome = "GRAPH_BETTER"
        elif graph < relational:
            outcome = "GRAPH_WORSE"
        else:
            outcome = "EQUAL"

        counts[outcome] += 1
        case_rows.append({
            "case_id": case_id,
            "graph_document_recall": graph,
            "relational_document_recall": relational,
            "graph_minus_relational_document_recall": graph - relational,
            "outcome": outcome,
        })

    graph_macro = statistics.fmean(graph_values) if graph_values else 0.0
    relational_macro = (
        statistics.fmean(relational_values)
        if relational_values else 0.0
    )
    bootstrap = paired_bootstrap_mean(differences)

    return {
        "case_count": len(case_ids),
        "graph_macro_recall": graph_macro,
        "relational_macro_recall": relational_macro,
        "absolute_macro_recall_difference_graph_minus_relational":
            graph_macro - relational_macro,
        "paired_macro_recall_difference_graph_minus_relational":
            statistics.fmean(differences) if differences else 0.0,
        "paired_macro_recall_difference_ci": {
            "lower_95": bootstrap["lower_95"],
            "upper_95": bootstrap["upper_95"],
            "seed": bootstrap["seed"],
            "resamples": bootstrap["resamples"],
        },
        "better_equal_worse": {
            "GRAPH_BETTER": counts["GRAPH_BETTER"],
            "EQUAL": counts["EQUAL"],
            "GRAPH_WORSE": counts["GRAPH_WORSE"],
        },
        "cases": case_rows,
    }


def paired_full_evidence_summary(
    graph_full: Mapping[str, bool],
    relational_full: Mapping[str, bool],
) -> dict[str, Any]:
    """Paired full-evidence comparison with exact two-sided McNemar test."""
    case_ids = _assert_same_cases(graph_full, relational_full)

    counts = Counter()
    case_rows = []

    for case_id in case_ids:
        graph = bool(graph_full[case_id])
        relational = bool(relational_full[case_id])

        if graph and not relational:
            outcome = "GRAPH_ONLY_FULL"
        elif relational and not graph:
            outcome = "RELATIONAL_ONLY_FULL"
        elif graph and relational:
            outcome = "BOTH_FULL"
        else:
            outcome = "NEITHER_FULL"

        counts[outcome] += 1
        case_rows.append({
            "case_id": case_id,
            "graph_full_evidence_coverage": graph,
            "relational_full_evidence_coverage": relational,
            "outcome": outcome,
        })

    graph_only = counts["GRAPH_ONLY_FULL"]
    relational_only = counts["RELATIONAL_ONLY_FULL"]
    discordant = graph_only + relational_only

    p_value = (
        float(
            binomtest(
                min(graph_only, relational_only),
                discordant,
                0.5,
            ).pvalue
        )
        if discordant
        else 1.0
    )

    graph_rate = (
        sum(bool(graph_full[case_id]) for case_id in case_ids) / len(case_ids)
        if case_ids else 0.0
    )
    relational_rate = (
        sum(bool(relational_full[case_id]) for case_id in case_ids)
        / len(case_ids)
        if case_ids else 0.0
    )

    return {
        "case_count": len(case_ids),
        "GRAPH_ONLY_FULL": graph_only,
        "RELATIONAL_ONLY_FULL": relational_only,
        "BOTH_FULL": counts["BOTH_FULL"],
        "NEITHER_FULL": counts["NEITHER_FULL"],
        "graph_full_evidence_rate": graph_rate,
        "relational_full_evidence_rate": relational_rate,
        "full_evidence_rate_difference_graph_minus_relational":
            graph_rate - relational_rate,
        "discordant_pair_count": discordant,
        "mcnemar_exact_two_sided_p_value": p_value,
        "cases": case_rows,
    }


def candidate_to_selection_summary(
    candidate_metrics: Mapping[str, Mapping[str, Any]],
    selected_metrics: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Measure recall lost between frozen candidate pool and frozen selection."""
    case_ids = _assert_same_cases(candidate_metrics, selected_metrics)

    losses: list[float] = []
    harmed_cases = []

    for case_id in case_ids:
        candidate = candidate_metrics[case_id]
        selected = selected_metrics[case_id]

        candidate_recall = float(candidate["document_recall"])
        selected_recall = float(selected["document_recall"])
        loss = candidate_recall - selected_recall

        if loss < 0:
            raise RuntimeError(
                f"selected recall exceeds candidate recall for {case_id}"
            )

        losses.append(loss)

        if loss > 0:
            candidate_missing = set(
                candidate["missing_required_record_ids"]
            )
            selected_missing = set(
                selected["missing_required_record_ids"]
            )
            required_lost_by_selection = sorted(
                selected_missing - candidate_missing
            )

            harmed_cases.append({
                "case_id": case_id,
                "candidate_document_recall": candidate_recall,
                "selected_document_recall": selected_recall,
                "recall_loss": loss,
                "required_record_ids_lost_by_selection":
                    required_lost_by_selection,
            })

    return {
        "case_count": len(case_ids),
        "mean_candidate_to_selection_recall_loss":
            statistics.fmean(losses) if losses else 0.0,
        "cases_with_positive_loss": sum(value > 0 for value in losses),
        "cases_with_zero_loss": sum(value == 0 for value in losses),
        "maximum_loss": max(losses, default=0.0),
        "harmed_cases": harmed_cases,
    }


def minimum_reachable_depths(
    anchor_rows: Sequence[Mapping[str, Any]],
    candidate_paths: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], int]:
    """Derive minimum hop depth from frozen candidate paths only."""
    depth: dict[tuple[str, str], int] = {}

    for row in anchor_rows:
        case_id = str(row["case_id"])
        for record_id in row["resolved_record_ids"]:
            depth[(case_id, str(record_id))] = 0

    for path in candidate_paths:
        case_id = str(path["case_id"])
        records = [str(value) for value in path["record_id_sequence"]]

        if int(path["depth"]) != len(records) - 1:
            raise RuntimeError(
                f"candidate path depth/record sequence mismatch: "
                f"{path['path_id']}"
            )

        for hop_depth, record_id in enumerate(records):
            key = (case_id, record_id)
            previous = depth.get(key)
            if previous is None or hop_depth < previous:
                depth[key] = hop_depth

    return depth


def required_depth_diagnostics(
    required_by_case: Mapping[str, set[str]],
    graph_selected_by_case: Mapping[str, set[str]],
    relational_by_case: Mapping[str, set[str]],
    minimum_depth: Mapping[tuple[str, str], int],
) -> dict[str, Any]:
    """Depth-2/depth-3 and selected multi-hop evidence diagnostics."""
    case_ids = _assert_same_cases(
        required_by_case,
        graph_selected_by_case,
    )
    _assert_same_cases(required_by_case, relational_by_case)

    depth_2_only = []
    depth_3_only = []
    graph_only_multihop = []
    multihop_benefit_cases = []
    made_complete_cases = []

    for case_id in case_ids:
        required = set(required_by_case[case_id])
        graph_selected = set(graph_selected_by_case[case_id])
        relational = set(relational_by_case[case_id])

        for record_id in sorted(required):
            key = (case_id, record_id)

            if key not in minimum_depth:
                continue

            value = minimum_depth[key]
            row = {
                "case_id": case_id,
                "record_id": record_id,
                "minimum_reachable_depth": value,
                "selected_by_graph": record_id in graph_selected,
            }

            if value == 2:
                depth_2_only.append(row)
            elif value == 3:
                depth_3_only.append(row)

            if (
                value >= 2
                and record_id in graph_selected
                and record_id not in relational
            ):
                graph_only_multihop.append(row)

        required_selected_multihop = sorted(
            record_id
            for record_id in required
            if record_id in graph_selected
            and minimum_depth.get((case_id, record_id), -1) >= 2
        )

        if required_selected_multihop:
            multihop_benefit_cases.append({
                "case_id": case_id,
                "required_multihop_record_ids":
                    required_selected_multihop,
            })

        depth_1_selected = {
            record_id
            for record_id in graph_selected
            if minimum_depth.get((case_id, record_id), -1) <= 1
        }

        graph_full = required <= graph_selected
        depth_1_full = required <= depth_1_selected

        if graph_full and not depth_1_full:
            involved = sorted(required - depth_1_selected)
            made_complete_cases.append({
                "case_id": case_id,
                "required_multihop_record_ids": involved,
                "required_depth_2_record_ids": [
                    record_id
                    for record_id in involved
                    if minimum_depth.get((case_id, record_id)) == 2
                ],
                "required_depth_3_record_ids": [
                    record_id
                    for record_id in involved
                    if minimum_depth.get((case_id, record_id)) == 3
                ],
            })

    return {
        "depth_2_only_required_evidence": {
            "required_record_incidence_count": len(depth_2_only),
            "unique_case_count":
                len({row["case_id"] for row in depth_2_only}),
            "selected_incidence_count":
                sum(row["selected_by_graph"] for row in depth_2_only),
            "records": depth_2_only,
        },
        "depth_3_only_required_evidence": {
            "required_record_incidence_count": len(depth_3_only),
            "unique_case_count":
                len({row["case_id"] for row in depth_3_only}),
            "selected_incidence_count":
                sum(row["selected_by_graph"] for row in depth_3_only),
            "records": depth_3_only,
        },
        "graph_only_depth_ge_2_required_evidence": {
            "required_record_incidence_count":
                len(graph_only_multihop),
            "unique_case_count":
                len({row["case_id"] for row in graph_only_multihop}),
            "depth_2_count":
                sum(
                    row["minimum_reachable_depth"] == 2
                    for row in graph_only_multihop
                ),
            "depth_3_count":
                sum(
                    row["minimum_reachable_depth"] == 3
                    for row in graph_only_multihop
                ),
            "records": graph_only_multihop,
        },
        "multi_hop_benefit": {
            "case_count": len(multihop_benefit_cases),
            "cases": multihop_benefit_cases,
        },
        "made_complete_by_multi_hop": {
            "case_count": len(made_complete_cases),
            "cases": made_complete_cases,
        },
    }


if __name__ == "__main__":
    raise SystemExit(
        "Evaluation execution is not authorized yet. "
        "Freeze and test the gold-free evaluator first."
    )
