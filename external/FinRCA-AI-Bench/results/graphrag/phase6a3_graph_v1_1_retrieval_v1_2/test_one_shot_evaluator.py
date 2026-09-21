from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "evaluate_one_shot.py"

spec = importlib.util.spec_from_file_location(
    "phase6a3_one_shot_evaluator",
    MODULE_PATH,
)
assert spec is not None
assert spec.loader is not None

evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


def test_paired_recall_summary() -> None:
    graph = {
        "c1": 1.0,
        "c2": 0.5,
        "c3": 0.0,
        "c4": 1.0,
    }
    relational = {
        "c1": 0.5,
        "c2": 0.5,
        "c3": 1.0,
        "c4": 1.0,
    }

    result = evaluator.paired_recall_summary(graph, relational)

    assert result["case_count"] == 4
    assert result["graph_macro_recall"] == pytest.approx(0.625)
    assert result["relational_macro_recall"] == pytest.approx(0.75)
    assert (
        result["absolute_macro_recall_difference_graph_minus_relational"]
        == pytest.approx(-0.125)
    )
    assert (
        result["paired_macro_recall_difference_graph_minus_relational"]
        == pytest.approx(-0.125)
    )

    assert result["better_equal_worse"] == {
        "GRAPH_BETTER": 1,
        "EQUAL": 2,
        "GRAPH_WORSE": 1,
    }

    ci = result["paired_macro_recall_difference_ci"]
    assert ci["seed"] == 20260809
    assert ci["resamples"] == 10_000
    assert ci["lower_95"] <= -0.125 <= ci["upper_95"]


def test_bootstrap_is_deterministic() -> None:
    values = [1.0, 0.5, 0.0, -0.5, -1.0]

    first = evaluator.paired_bootstrap_mean(values)
    second = evaluator.paired_bootstrap_mean(values)

    assert first == second


def test_case_universe_mismatch_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="case universes differ"):
        evaluator.paired_recall_summary(
            {"c1": 1.0},
            {"c2": 1.0},
        )


def test_paired_full_evidence_summary() -> None:
    graph = {
        "c1": True,
        "c2": False,
        "c3": True,
        "c4": False,
    }
    relational = {
        "c1": False,
        "c2": True,
        "c3": True,
        "c4": False,
    }

    result = evaluator.paired_full_evidence_summary(
        graph,
        relational,
    )

    assert result["case_count"] == 4
    assert result["GRAPH_ONLY_FULL"] == 1
    assert result["RELATIONAL_ONLY_FULL"] == 1
    assert result["BOTH_FULL"] == 1
    assert result["NEITHER_FULL"] == 1
    assert result["discordant_pair_count"] == 2

    assert result["graph_full_evidence_rate"] == pytest.approx(0.5)
    assert result["relational_full_evidence_rate"] == pytest.approx(0.5)
    assert (
        result["full_evidence_rate_difference_graph_minus_relational"]
        == pytest.approx(0.0)
    )

    # One discordant success in each direction => exact p = 1.
    assert result["mcnemar_exact_two_sided_p_value"] == pytest.approx(1.0)


def test_candidate_to_selection_loss() -> None:
    candidate = {
        "c1": {
            "document_recall": 1.0,
            "missing_required_record_ids": [],
        },
        "c2": {
            "document_recall": 0.5,
            "missing_required_record_ids": ["r4"],
        },
    }

    selected = {
        "c1": {
            "document_recall": 0.5,
            "missing_required_record_ids": ["r2"],
        },
        "c2": {
            "document_recall": 0.5,
            "missing_required_record_ids": ["r4"],
        },
    }

    result = evaluator.candidate_to_selection_summary(
        candidate,
        selected,
    )

    assert result["case_count"] == 2
    assert (
        result["mean_candidate_to_selection_recall_loss"]
        == pytest.approx(0.25)
    )
    assert result["cases_with_positive_loss"] == 1
    assert result["cases_with_zero_loss"] == 1
    assert result["maximum_loss"] == pytest.approx(0.5)

    assert result["harmed_cases"] == [
        {
            "case_id": "c1",
            "candidate_document_recall": 1.0,
            "selected_document_recall": 0.5,
            "recall_loss": 0.5,
            "required_record_ids_lost_by_selection": ["r2"],
        }
    ]


def test_selection_recall_cannot_exceed_candidate_recall() -> None:
    candidate = {
        "c1": {
            "document_recall": 0.5,
            "missing_required_record_ids": ["r2"],
        },
    }
    selected = {
        "c1": {
            "document_recall": 1.0,
            "missing_required_record_ids": [],
        },
    }

    with pytest.raises(
        RuntimeError,
        match="selected recall exceeds candidate recall",
    ):
        evaluator.candidate_to_selection_summary(
            candidate,
            selected,
        )


def test_minimum_reachable_depths() -> None:
    anchors = [
        {
            "case_id": "c1",
            "resolved_record_ids": ["a1"],
        }
    ]

    candidate_paths = [
        {
            "case_id": "c1",
            "path_id": "p1",
            "depth": 1,
            "record_id_sequence": ["a1", "r1"],
        },
        {
            "case_id": "c1",
            "path_id": "p2",
            "depth": 3,
            "record_id_sequence": ["a1", "r2", "r3", "r4"],
        },
        {
            # r3 is also reachable at depth 2, so minimum must remain 2.
            "case_id": "c1",
            "path_id": "p3",
            "depth": 2,
            "record_id_sequence": ["a1", "x1", "r3"],
        },
    ]

    depths = evaluator.minimum_reachable_depths(
        anchors,
        candidate_paths,
    )

    assert depths[("c1", "a1")] == 0
    assert depths[("c1", "r1")] == 1
    assert depths[("c1", "r2")] == 1
    assert depths[("c1", "r3")] == 2
    assert depths[("c1", "r4")] == 3


def test_required_depth_diagnostics() -> None:
    required = {
        "c1": {"a1", "r2", "r3"},
        "c2": {"a2", "r4"},
    }

    graph_selected = {
        "c1": {"a1", "r2", "r3"},
        "c2": {"a2", "r4"},
    }

    relational = {
        "c1": {"a1", "r2"},
        "c2": {"a2"},
    }

    minimum_depth = {
        ("c1", "a1"): 0,
        ("c1", "r2"): 2,
        ("c1", "r3"): 3,
        ("c2", "a2"): 0,
        ("c2", "r4"): 1,
    }

    result = evaluator.required_depth_diagnostics(
        required,
        graph_selected,
        relational,
        minimum_depth,
    )

    depth2 = result["depth_2_only_required_evidence"]
    assert depth2["required_record_incidence_count"] == 1
    assert depth2["unique_case_count"] == 1
    assert depth2["selected_incidence_count"] == 1

    depth3 = result["depth_3_only_required_evidence"]
    assert depth3["required_record_incidence_count"] == 1
    assert depth3["unique_case_count"] == 1
    assert depth3["selected_incidence_count"] == 1

    graph_only = result["graph_only_depth_ge_2_required_evidence"]
    assert graph_only["required_record_incidence_count"] == 1
    assert graph_only["unique_case_count"] == 1
    assert graph_only["depth_2_count"] == 0
    assert graph_only["depth_3_count"] == 1

    multihop = result["multi_hop_benefit"]
    assert multihop["case_count"] == 1
    assert multihop["cases"][0]["case_id"] == "c1"

    complete = result["made_complete_by_multi_hop"]
    assert complete["case_count"] == 1
    assert complete["cases"][0]["case_id"] == "c1"
    assert complete["cases"][0]["required_depth_2_record_ids"] == ["r2"]
    assert complete["cases"][0]["required_depth_3_record_ids"] == ["r3"]


def test_candidate_path_shape_mismatch_fails_closed() -> None:
    anchors = [
        {
            "case_id": "c1",
            "resolved_record_ids": ["a1"],
        }
    ]

    paths = [
        {
            "case_id": "c1",
            "path_id": "bad",
            "depth": 2,
            "record_id_sequence": ["a1", "r1"],
        }
    ]

    with pytest.raises(
        RuntimeError,
        match="candidate path depth/record sequence mismatch",
    ):
        evaluator.minimum_reachable_depths(
            anchors,
            paths,
        )
