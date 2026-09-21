from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "run_one_shot_evaluation.py"

spec = importlib.util.spec_from_file_location(
    "phase6a3_one_shot_runner",
    RUNNER_PATH,
)
assert spec is not None
assert spec.loader is not None

runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_required_drop_summary() -> None:
    drops = []

    for index in range(33):
        drops.append({
            "case_id": "c1" if index == 0 else "c2",
            "record_id": f"r{index}",
            "node_type":
                "AUDIT_EVENT"
                if index < 30
                else "APPROVAL_EVENT",
            "minimum_reachable_depth": 1,
            "best_structural_selection_tier": 5,
            "best_structural_selection_tier_name":
                "LOCAL_TERMINAL_CONTEXT_PATH",
            "primary_drop_reason":
                "CONTEXT_AFTER_BACKBONE_BUDGET_EXHAUSTED",
        })

    required = {
        "c1": {"r0", "not_dropped"},
        "c2": {"r31"},
    }

    result = runner.required_drop_summary(
        drops,
        required,
    )

    assert result["total_structurally_dropped_records"] == 33
    assert result["required_dropped_record_count"] == 2
    assert result["unique_cases_with_required_drop"] == 2

    assert result["required_dropped_by_node_type"] == {
        "APPROVAL_EVENT": 1,
        "AUDIT_EVENT": 1,
    }

    assert result["required_dropped_by_selection_tier"] == {
        "5": 2,
    }


def test_required_drop_summary_requires_33_rows() -> None:
    with pytest.raises(
        RuntimeError,
        match="record drop count differs from frozen 33",
    ):
        runner.required_drop_summary(
            [],
            {"c1": set()},
        )


def test_per_anchor_summary() -> None:
    routes = {
        "c1": {
            "case_id": "c1",
            "primary_entity_type": "invoice",
        },
        "c2": {
            "case_id": "c2",
            "primary_entity_type": "invoice",
        },
        "c3": {
            "case_id": "c3",
            "primary_entity_type": "payment",
        },
    }

    graph = {
        "c1": {
            "document_recall": 1.0,
            "full_evidence_coverage": True,
        },
        "c2": {
            "document_recall": 0.5,
            "full_evidence_coverage": False,
        },
        "c3": {
            "document_recall": 1.0,
            "full_evidence_coverage": True,
        },
    }

    relational = {
        "c1": {
            "document_recall": 0.5,
            "full_evidence_coverage": False,
        },
        "c2": {
            "document_recall": 0.5,
            "full_evidence_coverage": False,
        },
        "c3": {
            "document_recall": 1.0,
            "full_evidence_coverage": True,
        },
    }

    result = runner.per_anchor_summary(
        routes,
        graph,
        relational,
    )

    assert set(result) == {
        "invoice",
        "payment",
    }

    assert result["invoice"]["case_count"] == 2

    assert (
        result["invoice"][
            "graph_selected_macro_recall"
        ]
        == pytest.approx(0.75)
    )

    assert (
        result["invoice"][
            "relational_macro_recall"
        ]
        == pytest.approx(0.5)
    )

    assert (
        result["invoice"][
            "paired_recall_difference_graph_minus_relational"
        ]
        == pytest.approx(0.25)
    )

    assert result["invoice"]["better_equal_worse"] == {
        "GRAPH_BETTER": 1,
        "EQUAL": 1,
        "GRAPH_WORSE": 0,
    }


def test_bank_transaction_summary() -> None:
    routes = {}
    required = {}
    candidate = {}
    selected = {}
    candidate_metrics = {}
    graph_metrics = {}
    relational_metrics = {}

    for index in range(26):
        case_id = f"bank_{index:02d}"

        routes[case_id] = {
            "case_id": case_id,
            "primary_entity_type":
                "bank_transaction",
        }

        required[case_id] = {
            "anchor",
            "required",
        }

        candidate[case_id] = [
            "anchor",
            "required",
        ]

        selected[case_id] = [
            "anchor",
            "required",
        ]

        candidate_metrics[case_id] = {
            "document_recall": 1.0,
        }

        graph_metrics[case_id] = {
            "document_recall": 1.0,
            "full_evidence_coverage": True,
        }

        relational_metrics[case_id] = {
            "document_recall": 0.5,
            "full_evidence_coverage": False,
        }

    # Missing from Graph candidate pool.
    candidate["bank_00"] = ["anchor"]
    selected["bank_00"] = ["anchor"]

    candidate_metrics[
        "bank_00"
    ]["document_recall"] = 0.5

    graph_metrics[
        "bank_00"
    ]["document_recall"] = 0.5

    graph_metrics[
        "bank_00"
    ]["full_evidence_coverage"] = False

    # Candidate contains evidence, but selection loses it.
    selected["bank_01"] = ["anchor"]

    graph_metrics[
        "bank_01"
    ]["document_recall"] = 0.5

    graph_metrics[
        "bank_01"
    ]["full_evidence_coverage"] = False

    result = runner.bank_transaction_summary(
        routes,
        required,
        candidate,
        selected,
        candidate_metrics,
        graph_metrics,
        relational_metrics,
    )

    assert result["case_count"] == 26

    missing_candidate = result[
        "required_records_absent_from_graph_candidate_pool"
    ]

    assert (
        missing_candidate[
            "record_incidence_count"
        ]
        == 1
    )

    assert (
        missing_candidate[
            "unique_case_count"
        ]
        == 1
    )

    assert missing_candidate["records"] == [
        {
            "case_id": "bank_00",
            "record_id": "required",
        }
    ]

    top40_loss = result[
        "required_records_present_in_candidate_pool_but_absent_after_top40"
    ]

    assert (
        top40_loss[
            "record_incidence_count"
        ]
        == 1
    )

    assert (
        top40_loss[
            "unique_case_count"
        ]
        == 1
    )

    assert top40_loss["records"] == [
        {
            "case_id": "bank_01",
            "record_id": "required",
        }
    ]

    assert (
        result["causal_relation_gap_claimed"]
        is False
    )


def test_bank_transaction_requires_26_cases() -> None:
    with pytest.raises(
        RuntimeError,
        match="bank_transaction case count mismatch",
    ):
        runner.bank_transaction_summary(
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        )


def test_token_distribution() -> None:
    result = runner.token_distribution(
        [10, 20, 30, 40],
    )

    assert result["mean"] == pytest.approx(25.0)
    assert result["median"] == pytest.approx(25.0)
    assert result["maximum"] == pytest.approx(40.0)

    assert (
        result["p75"]
        >= result["median"]
    )

    assert (
        result["p95"]
        >= result["p75"]
    )


def test_token_distribution_empty() -> None:
    assert runner.token_distribution([]) == {
        "mean": 0.0,
        "median": 0.0,
        "p75": 0.0,
        "p90": 0.0,
        "p95": 0.0,
        "p99": 0.0,
        "maximum": 0.0,
    }


def test_authorized_gold_projection_strips_all_other_fields(tmp_path) -> None:
    fake_gold = tmp_path / "fake_gold.jsonl"

    fake_gold.write_text(
        '{"case_id":"c1","evidence_ids":["r1"],'
        '"evidence_required":["r2"],'
        '"root_cause_label":"SECRET_LABEL",'
        '"question":"SECRET_QUESTION",'
        '"expected_answer":"SECRET_ANSWER"}\n'
        '{"case_id":"c2","evidence_ids":["r3","r4"],'
        '"evidence_required":[],'
        '"other_private_field":{"x":1}}\n',
        encoding="utf-8",
    )

    rows = runner.load_authorized_validation_projection(
        fake_gold
    )

    assert rows == [
        {
            "case_id": "c1",
            "evidence_ids": ["r1"],
            "evidence_required": ["r2"],
        },
        {
            "case_id": "c2",
            "evidence_ids": ["r3", "r4"],
            "evidence_required": [],
        },
    ]

    for row in rows:
        assert set(row) == {
            "case_id",
            "evidence_ids",
            "evidence_required",
        }


def test_one_shot_guard_rejects_existing_artifacts(tmp_path) -> None:
    evaluation_dir = tmp_path / "evaluation"

    # Clean directory/nonexistent directory is permitted.
    runner.assert_one_shot_not_started(
        evaluation_dir
    )

    evaluation_dir.mkdir()
    (evaluation_dir / "existing.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="same-run one-shot evaluation rerun is prohibited",
    ):
        runner.assert_one_shot_not_started(
            evaluation_dir
        )


def test_gold_access_sentinel_is_fail_closed(tmp_path) -> None:
    sentinel = (
        tmp_path
        / "evaluation"
        / "gold_access_started.json"
    )

    runner.write_gold_access_sentinel(
        sentinel,
        "synthetic_manifest_sha256",
    )

    value = runner.load_json(sentinel)

    assert value["status"] == (
        "GOLD_ACCESS_STARTED_FAIL_CLOSED"
    )
    assert value["same_run_rerun_permitted"] is False
    assert value["heldout_gold_opened"] is False
    assert (
        value["evaluator_freeze_manifest_sha256"]
        == "synthetic_manifest_sha256"
    )

    with pytest.raises(
        RuntimeError,
        match="same-run evaluation rerun is prohibited",
    ):
        runner.write_gold_access_sentinel(
            sentinel,
            "synthetic_manifest_sha256",
        )
