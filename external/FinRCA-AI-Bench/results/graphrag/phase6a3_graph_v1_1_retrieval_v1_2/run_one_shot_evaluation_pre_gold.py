#!/usr/bin/env python3
"""Phase 6A.3 Graph v1.1 clean one-shot evaluation runner.

This module separates real-input orchestration from the frozen, synthetically
tested statistical core in evaluate_one_shot.py.

Development state:
    PRE_GOLD_ORCHESTRATION_ONLY

At this stage there is intentionally no validation-gold loader and no
evaluation entry point.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
RETRIEVAL = OUTPUT / "retrieval"

if str(OUTPUT) not in sys.path:
    sys.path.insert(0, str(OUTPUT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import evaluate_one_shot as core

from src.rag.corpus import load_persisted_corpus
from src.rag.tokens import percentile


# ---------------------------------------------------------------------------
# Frozen scientific constants
# ---------------------------------------------------------------------------

RUN_ID = "phase6a3_graph_v1_1_retrieval_v1_2_20260816T034800Z"

BOOTSTRAP_SEED = 20260809
BOOTSTRAP_RESAMPLES = 10_000

EXPECTED_CASE_COUNT = 416
EXPECTED_RESOLVED_ROOT_COUNT = 430
EXPECTED_CANDIDATE_PATH_COUNT = 13_371
EXPECTED_CANDIDATE_RECORD_COUNT = 8_369
EXPECTED_SELECTED_RECORD_COUNT = 8_336
EXPECTED_RECORD_DROP_COUNT = 33
EXPECTED_BANK_TRANSACTION_CASE_COUNT = 26
EXPECTED_CORPUS_DOCUMENT_COUNT = 155_391
MAX_SELECTED_RECORDS = 40

CORE_PATH = OUTPUT / "evaluate_one_shot.py"
CORE_SHA256 = (
    "80a58d398b0f76c6191ee319b5bdfdeff68a6aa7d302f5829cd8456c0229a4b9"
)

METRIC_SPEC = OUTPUT / "EVALUATION_METRIC_SPEC.md"
PREREGISTRATION = OUTPUT / "evaluation_preregistration.json"

PRE_GOLD_MANIFEST = RETRIEVAL / "final_pre_gold_manifest.json"
PRE_GOLD_HASH_INVENTORY = RETRIEVAL / "final_pre_gold_hashes.json"

ANCHORS_PATH = RETRIEVAL / "anchor_resolutions.jsonl"
CANDIDATE_PATHS_PATH = RETRIEVAL / "candidate_paths.jsonl"
CANDIDATE_RECORDS_PATH = RETRIEVAL / "candidate_records.jsonl"
SELECTED_PATHS_PATH = RETRIEVAL / "selected_paths.jsonl"
SELECTED_RECORDS_PATH = RETRIEVAL / "selected_records.jsonl"
DROP_LEDGER_PATH = RETRIEVAL / "drop_ledger.jsonl"

GRAMMAR_PATH = (
    ROOT
    / "results/graphrag/registry_freeze_v1_1/"
    / "graph_traversal_grammar_v1_1.json"
)

SELECTION_POLICY_PATH = (
    ROOT
    / "results/graphrag/evidence_selection_freeze_v1_1/"
    / "evidence_selection_policy_v1_1.json"
)

CORPUS_DIR = (
    ROOT
    / "results/rag/"
    / "phase5_rag_index_v1_0_20260810T000000Z/"
    / "corpus"
)

CORPUS_DOCUMENTS_PATH = CORPUS_DIR / "documents.jsonl"
CORPUS_METADATA_PATH = CORPUS_DIR / "metadata.jsonl"
CORPUS_RECORD_IDS_PATH = CORPUS_DIR / "record_ids.txt"

ROUTES_PATH = (
    ROOT
    / "results/rag/"
    / "phase5_rag_validation_routes_v1_0_20260812T040938Z/"
    / "validation_routes.jsonl"
)

RELATIONAL_PATH = (
    ROOT
    / "results/graphrag/"
    / "phase6a_graph_retrieval_v1_0/"
    / "ablations/relational_rag_results.jsonl"
)


EXPECTED_HASHES = {
    CORE_PATH:
        CORE_SHA256,

    METRIC_SPEC:
        "2862be9a1242178af029f0582a1777749ef476b80a7ccd8b114e58aafd6340c3",

    PREREGISTRATION:
        "74b07ce84050ee9ac55c6f7397c81cfa0b08d507cd6f7d65a0604c11e7772991",

    PRE_GOLD_MANIFEST:
        "0c4ec3125a9af91a1ec2e9ee1b7b71bf6105e712a49c1e1413a137a40421fa6f",

    PRE_GOLD_HASH_INVENTORY:
        "fdba4cab1ca00d83ca42bb2b3e3962aebc31b185a89e952b0fc9a6ea17b415d8",

    CANDIDATE_PATHS_PATH:
        "eab6e5524334001cbb285dbe1cb5367daa70fe008836a9df5ac99fedef695c03",

    CANDIDATE_RECORDS_PATH:
        "4c960019afebaa179f6ef213bd9771c36c82f652dc60b0b1ac1f20f24eff955c",

    SELECTED_PATHS_PATH:
        "7c50a3569920124286ad1866af28155d6ba25d7e77d6480aaf0627f7c8cd0561",

    SELECTED_RECORDS_PATH:
        "e8335a880b0cf57820f58c233f4558b9f4df111f6739f8c13ca7bc04eb994cbd",

    GRAMMAR_PATH:
        "2222def5dc3fd18628731949697087c6c96d7cdf1bb6c4cf2d16a1a58da6c8dc",

    SELECTION_POLICY_PATH:
        "cad5f2298d9dad62599cfe592304c08cf8808441586fb865d1f4824b3054ea1b",

    CORPUS_DOCUMENTS_PATH:
        "43fe8841d3cbfc64c403349c2336c631c9f6ca9dc35f3e86af1c4ae993441b8c",

    CORPUS_METADATA_PATH:
        "e30183ea1e17af182ad24a3177e776a869ed55718872ba6cc1a169506b4f96fb",

    CORPUS_RECORD_IDS_PATH:
        "1850249832dbb9c75ddddfa8e82615dd1db138cdd83cb2dc455029035e1b0058",

    ROUTES_PATH:
        "08ceeaf3a7c569ca94a87b0c0830d0fb90784daac66dd959de3fee1561b94b44",

    RELATIONAL_PATH:
        "3921c2bbc17373b3dc237dafb8f6f17327e655842acf0ecbbcbc6c23966c58f5",
}


# ---------------------------------------------------------------------------
# Deterministic IO
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def metadata(path: Path) -> dict[str, Any]:
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))

    return rows


# ---------------------------------------------------------------------------
# Frozen non-gold verification
# ---------------------------------------------------------------------------

def verify_expected_hashes() -> list[dict[str, Any]]:
    checks = []

    for path, expected in sorted(
        EXPECTED_HASHES.items(),
        key=lambda item: str(item[0]),
    ):
        if not path.is_file():
            raise RuntimeError(
                f"missing frozen input: {path}"
            )

        observed = sha256_file(path)

        row = {
            "path":
                path.relative_to(ROOT).as_posix(),
            "expected_sha256": expected,
            "observed_sha256": observed,
            "status":
                "PASS"
                if observed == expected
                else "FAIL",
        }

        if observed != expected:
            raise RuntimeError(
                "frozen input hash mismatch: "
                + json.dumps(
                    row,
                    sort_keys=True,
                )
            )

        checks.append(row)

    return checks


def verify_pre_gold_inventory() -> dict[str, Any]:
    inventory = load_json(
        PRE_GOLD_HASH_INVENTORY
    )

    checks = []

    for name, expected in sorted(
        inventory["artifacts"].items()
    ):
        path = OUTPUT / name

        if not path.is_file():
            raise RuntimeError(
                f"missing pre-gold artifact: {name}"
            )

        observed = metadata(path)

        passed = (
            observed["sha256"]
            == expected["sha256"]
            and observed["bytes"]
            == expected["bytes"]
        )

        row = {
            "path": name,
            "expected": expected,
            "observed": observed,
            "status":
                "PASS" if passed else "FAIL",
        }

        if not passed:
            raise RuntimeError(
                "pre-gold inventory mismatch: "
                f"{name}"
            )

        checks.append(row)

    return {
        "status": "PASS",
        "check_count": len(checks),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Frozen non-gold real-input loading
# ---------------------------------------------------------------------------

def load_non_gold_inputs() -> dict[str, Any]:
    anchors = load_jsonl(ANCHORS_PATH)
    candidate_paths = load_jsonl(
        CANDIDATE_PATHS_PATH
    )
    candidate_records = load_jsonl(
        CANDIDATE_RECORDS_PATH
    )
    selected_records = load_jsonl(
        SELECTED_RECORDS_PATH
    )
    drop_ledger = load_jsonl(
        DROP_LEDGER_PATH
    )
    routes = load_jsonl(ROUTES_PATH)
    relational_rows = load_jsonl(
        RELATIONAL_PATH
    )

    if len(anchors) != EXPECTED_CASE_COUNT:
        raise RuntimeError(
            f"anchor case count mismatch: "
            f"{len(anchors)}"
        )

    if (
        len(candidate_paths)
        != EXPECTED_CANDIDATE_PATH_COUNT
    ):
        raise RuntimeError(
            "candidate path count mismatch: "
            f"{len(candidate_paths)}"
        )

    if (
        len(candidate_records)
        != EXPECTED_CANDIDATE_RECORD_COUNT
    ):
        raise RuntimeError(
            "candidate record count mismatch: "
            f"{len(candidate_records)}"
        )

    if (
        len(selected_records)
        != EXPECTED_SELECTED_RECORD_COUNT
    ):
        raise RuntimeError(
            "selected record count mismatch: "
            f"{len(selected_records)}"
        )

    if len(routes) != EXPECTED_CASE_COUNT:
        raise RuntimeError(
            f"route count mismatch: {len(routes)}"
        )

    if (
        len(relational_rows)
        != EXPECTED_CASE_COUNT
    ):
        raise RuntimeError(
            "Relational-RAG row count mismatch: "
            f"{len(relational_rows)}"
        )

    anchor_by_id = {
        str(row["case_id"]): row
        for row in anchors
    }

    route_by_id = {
        str(row["case_id"]): row
        for row in routes
    }

    relational_source_by_id = {
        str(row["case_id"]): row
        for row in relational_rows
    }

    if (
        len(anchor_by_id) != EXPECTED_CASE_COUNT
        or len(route_by_id) != EXPECTED_CASE_COUNT
        or len(relational_source_by_id)
        != EXPECTED_CASE_COUNT
    ):
        raise RuntimeError(
            "duplicate case IDs in frozen inputs"
        )

    if not (
        set(anchor_by_id)
        == set(route_by_id)
        == set(relational_source_by_id)
    ):
        raise RuntimeError(
            "anchor/route/relational case "
            "universes differ"
        )

    if not all(
        str(row["status"]) == "SUCCESS"
        for row in relational_rows
    ):
        raise RuntimeError(
            "Relational-RAG contains "
            "non-SUCCESS row"
        )

    candidate_by_case: dict[str, list[str]] = (
        defaultdict(list)
    )

    for row in candidate_records:
        candidate_by_case[
            str(row["case_id"])
        ].append(str(row["record_id"]))

    candidate_by_case = {
        case_id: sorted(set(values))
        for case_id, values
        in candidate_by_case.items()
    }

    selected_rows_by_case: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for row in selected_records:
        selected_rows_by_case[
            str(row["case_id"])
        ].append(row)

    selected_by_case: dict[str, list[str]] = {}

    for case_id, rows in (
        selected_rows_by_case.items()
    ):
        ordered = sorted(
            rows,
            key=lambda row:
                int(row["selected_record_rank"]),
        )

        ranks = [
            int(row["selected_record_rank"])
            for row in ordered
        ]

        if ranks != list(
            range(1, len(ordered) + 1)
        ):
            raise RuntimeError(
                "selected ranks are not "
                f"contiguous for {case_id}"
            )

        ids = [
            str(row["record_id"])
            for row in ordered
        ]

        if len(ids) != len(set(ids)):
            raise RuntimeError(
                "duplicate selected record for "
                f"{case_id}"
            )

        if len(ids) > MAX_SELECTED_RECORDS:
            raise RuntimeError(
                "Graph selected-record cap "
                f"exceeded for {case_id}"
            )

        selected_by_case[case_id] = ids

    relational_by_case = {
        case_id: [
            str(record_id)
            for record_id
            in row["retrieved_record_ids"]
        ]
        for case_id, row
        in relational_source_by_id.items()
    }

    if any(
        len(values) > MAX_SELECTED_RECORDS
        for values
        in relational_by_case.values()
    ):
        raise RuntimeError(
            "Relational-RAG exceeds "
            "40-record maximum"
        )

    if not (
        set(candidate_by_case)
        == set(selected_by_case)
        == set(route_by_id)
    ):
        raise RuntimeError(
            "candidate/selected/route case "
            "universes differ"
        )

    for case_id in sorted(route_by_id):
        if not (
            set(selected_by_case[case_id])
            <= set(candidate_by_case[case_id])
        ):
            raise RuntimeError(
                "selected records are not a "
                f"candidate subset for {case_id}"
            )

    record_drops = [
        row
        for row in drop_ledger
        if str(row["entry_type"]) == "RECORD"
    ]

    if (
        len(record_drops)
        != EXPECTED_RECORD_DROP_COUNT
    ):
        raise RuntimeError(
            "record-drop count mismatch: "
            f"{len(record_drops)}"
        )

    if any(
        int(
            row[
                "best_structural_selection_tier"
            ]
        ) != 5
        for row in record_drops
    ):
        raise RuntimeError(
            "non-Tier-5 record drop observed"
        )

    if any(
        str(row["primary_drop_reason"])
        !=
        "CONTEXT_AFTER_BACKBONE_BUDGET_EXHAUSTED"
        for row in record_drops
    ):
        raise RuntimeError(
            "unexpected record-drop reason"
        )

    resolved_root_count = sum(
        len(row["resolved_record_ids"])
        for row in anchors
    )

    if (
        resolved_root_count
        != EXPECTED_RESOLVED_ROOT_COUNT
    ):
        raise RuntimeError(
            "resolved root count mismatch: "
            f"{resolved_root_count}"
        )

    route_counts = Counter(
        str(row["primary_entity_type"])
        for row in routes
    )

    expected_route_counts = {
        "bank_transaction": 26,
        "gl_journal": 14,
        "invoice": 195,
        "payment": 181,
    }

    if dict(sorted(route_counts.items())) != (
        expected_route_counts
    ):
        raise RuntimeError(
            "route-type distribution mismatch: "
            f"{dict(sorted(route_counts.items()))}"
        )

    corpus = load_persisted_corpus(
        CORPUS_DIR
    )

    if (
        len(corpus.documents)
        != EXPECTED_CORPUS_DOCUMENT_COUNT
    ):
        raise RuntimeError(
            "corpus document count mismatch: "
            f"{len(corpus.documents)}"
        )

    document_by_id = {
        document.record_id: document
        for document in corpus.documents
    }

    for system_name, by_case in (
        ("candidate", candidate_by_case),
        ("graph_selected", selected_by_case),
        ("relational", relational_by_case),
    ):
        missing = sorted({
            record_id
            for values in by_case.values()
            for record_id in values
            if record_id not in document_by_id
        })

        if missing:
            raise RuntimeError(
                f"{system_name} references "
                "records absent from corpus: "
                f"{missing[:10]}"
            )

    return {
        "anchors": anchors,
        "anchor_by_id": anchor_by_id,
        "candidate_paths": candidate_paths,
        "candidate_records": candidate_records,
        "candidate_by_case": candidate_by_case,
        "selected_records": selected_records,
        "selected_by_case": selected_by_case,
        "record_drops": record_drops,
        "routes": routes,
        "route_by_id": route_by_id,
        "relational_rows": relational_rows,
        "relational_by_case": relational_by_case,
        "documents": corpus.documents,
        "document_by_id": document_by_id,
        "route_counts":
            dict(sorted(route_counts.items())),
        "resolved_root_count":
            resolved_root_count,
    }


# ---------------------------------------------------------------------------
# Gold-free diagnostics that will be used after evidence projection
# ---------------------------------------------------------------------------

def token_distribution(
    values: Sequence[float],
) -> dict[str, float]:
    if not values:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "maximum": 0.0,
        }

    return {
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p75": percentile(values, 0.75),
        "p90": percentile(values, 0.90),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "maximum": max(values),
    }


def required_drop_summary(
    record_drops:
        Sequence[Mapping[str, Any]],
    required_by_case:
        Mapping[str, set[str]],
) -> dict[str, Any]:
    if (
        len(record_drops)
        != EXPECTED_RECORD_DROP_COUNT
    ):
        raise RuntimeError(
            "record drop count differs "
            "from frozen 33"
        )

    matches = []

    for row in sorted(
        record_drops,
        key=lambda value: (
            str(value["case_id"]),
            str(value["record_id"]),
        ),
    ):
        case_id = str(row["case_id"])
        record_id = str(row["record_id"])

        if case_id not in required_by_case:
            raise RuntimeError(
                f"unknown drop-ledger case: "
                f"{case_id}"
            )

        if record_id in required_by_case[case_id]:
            matches.append({
                "case_id": case_id,
                "record_id": record_id,
                "node_type":
                    str(row["node_type"]),
                "minimum_reachable_depth":
                    int(
                        row[
                            "minimum_reachable_depth"
                        ]
                    ),
                "selection_tier":
                    int(
                        row[
                            "best_structural_selection_tier"
                        ]
                    ),
                "selection_tier_name":
                    str(
                        row[
                            "best_structural_selection_tier_name"
                        ]
                    ),
                "primary_drop_reason":
                    str(
                        row[
                            "primary_drop_reason"
                        ]
                    ),
            })

    return {
        "total_structurally_dropped_records":
            len(record_drops),
        "required_dropped_record_count":
            len(matches),
        "unique_cases_with_required_drop":
            len({
                row["case_id"]
                for row in matches
            }),
        "required_dropped_by_node_type":
            dict(sorted(Counter(
                row["node_type"]
                for row in matches
            ).items())),
        "required_dropped_by_minimum_reachable_depth":
            dict(sorted(Counter(
                str(
                    row[
                        "minimum_reachable_depth"
                    ]
                )
                for row in matches
            ).items())),
        "required_dropped_by_selection_tier":
            dict(sorted(Counter(
                str(row["selection_tier"])
                for row in matches
            ).items())),
        "records": matches,
    }


def per_anchor_summary(
    route_by_id:
        Mapping[str, Mapping[str, Any]],
    graph_metrics:
        Mapping[str, Mapping[str, Any]],
    relational_metrics:
        Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    case_ids = core._assert_same_cases(
        graph_metrics,
        relational_metrics,
    )

    if set(case_ids) != set(route_by_id):
        raise RuntimeError(
            "route universe differs from "
            "metric universe"
        )

    output = {}

    for anchor_type in sorted({
        str(
            route_by_id[case_id][
                "primary_entity_type"
            ]
        )
        for case_id in case_ids
    }):
        ids = [
            case_id
            for case_id in case_ids
            if str(
                route_by_id[case_id][
                    "primary_entity_type"
                ]
            ) == anchor_type
        ]

        graph_recall = [
            float(
                graph_metrics[case_id][
                    "document_recall"
                ]
            )
            for case_id in ids
        ]

        relational_recall = [
            float(
                relational_metrics[case_id][
                    "document_recall"
                ]
            )
            for case_id in ids
        ]

        deltas = [
            graph - relational
            for graph, relational
            in zip(
                graph_recall,
                relational_recall,
            )
        ]

        outcomes = Counter()

        for graph, relational in zip(
            graph_recall,
            relational_recall,
        ):
            if graph > relational:
                outcomes["GRAPH_BETTER"] += 1
            elif graph < relational:
                outcomes["GRAPH_WORSE"] += 1
            else:
                outcomes["EQUAL"] += 1

        output[anchor_type] = {
            "case_count": len(ids),

            "graph_selected_macro_recall":
                statistics.fmean(graph_recall),

            "relational_macro_recall":
                statistics.fmean(
                    relational_recall
                ),

            "paired_recall_difference_graph_minus_relational":
                statistics.fmean(deltas),

            "graph_full_evidence_coverage":
                statistics.fmean([
                    float(
                        graph_metrics[case_id][
                            "full_evidence_coverage"
                        ]
                    )
                    for case_id in ids
                ]),

            "relational_full_evidence_coverage":
                statistics.fmean([
                    float(
                        relational_metrics[case_id][
                            "full_evidence_coverage"
                        ]
                    )
                    for case_id in ids
                ]),

            "better_equal_worse": {
                "GRAPH_BETTER":
                    outcomes["GRAPH_BETTER"],
                "EQUAL":
                    outcomes["EQUAL"],
                "GRAPH_WORSE":
                    outcomes["GRAPH_WORSE"],
            },
        }

    return output


def bank_transaction_summary(
    route_by_id:
        Mapping[str, Mapping[str, Any]],
    required_by_case:
        Mapping[str, set[str]],
    candidate_by_case:
        Mapping[str, Sequence[str]],
    selected_by_case:
        Mapping[str, Sequence[str]],
    candidate_metrics:
        Mapping[str, Mapping[str, Any]],
    graph_metrics:
        Mapping[str, Mapping[str, Any]],
    relational_metrics:
        Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    ids = sorted(
        case_id
        for case_id, route
        in route_by_id.items()
        if str(
            route["primary_entity_type"]
        ) == "bank_transaction"
    )

    if (
        len(ids)
        != EXPECTED_BANK_TRANSACTION_CASE_COUNT
    ):
        raise RuntimeError(
            "bank_transaction case count "
            f"mismatch: {len(ids)}"
        )

    candidate_missing = []
    top40_missing = []

    for case_id in ids:
        required = set(
            required_by_case[case_id]
        )
        candidate = set(
            candidate_by_case[case_id]
        )
        selected = set(
            selected_by_case[case_id]
        )

        for record_id in sorted(
            required - candidate
        ):
            candidate_missing.append({
                "case_id": case_id,
                "record_id": record_id,
            })

        for record_id in sorted(
            (required & candidate) - selected
        ):
            top40_missing.append({
                "case_id": case_id,
                "record_id": record_id,
            })

    return {
        "case_count": len(ids),

        "candidate_pool_macro_recall":
            statistics.fmean([
                float(
                    candidate_metrics[case_id][
                        "document_recall"
                    ]
                )
                for case_id in ids
            ]),

        "graph_selected_macro_recall":
            statistics.fmean([
                float(
                    graph_metrics[case_id][
                        "document_recall"
                    ]
                )
                for case_id in ids
            ]),

        "relational_macro_recall":
            statistics.fmean([
                float(
                    relational_metrics[case_id][
                        "document_recall"
                    ]
                )
                for case_id in ids
            ]),

        "graph_full_evidence_coverage":
            statistics.fmean([
                float(
                    graph_metrics[case_id][
                        "full_evidence_coverage"
                    ]
                )
                for case_id in ids
            ]),

        "relational_full_evidence_coverage":
            statistics.fmean([
                float(
                    relational_metrics[case_id][
                        "full_evidence_coverage"
                    ]
                )
                for case_id in ids
            ]),

        "required_records_absent_from_graph_candidate_pool": {
            "record_incidence_count":
                len(candidate_missing),
            "unique_case_count":
                len({
                    row["case_id"]
                    for row in candidate_missing
                }),
            "records":
                candidate_missing,
        },

        "required_records_present_in_candidate_pool_but_absent_after_top40": {
            "record_incidence_count":
                len(top40_missing),
            "unique_case_count":
                len({
                    row["case_id"]
                    for row in top40_missing
                }),
            "records":
                top40_missing,
        },

        "causal_relation_gap_claimed": False,
    }


if __name__ == "__main__":
    raise SystemExit(
        "PRE-GOLD DEVELOPMENT STATE ONLY. "
        "Validation-gold execution is not implemented."
    )
