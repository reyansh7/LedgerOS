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

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
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
from src.rag.evaluation import aggregate_retrieval, retrieval_case_metrics
from src.rag.evidence import resolve_evidence
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


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )


def write_jsonl(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        for row in rows:
            handle.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )


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


# ---------------------------------------------------------------------------
# Final one-shot scientific-integrity boundaries
# ---------------------------------------------------------------------------

VALIDATION_GOLD_PATH = (
    ROOT
    / "data/benchmark/validation/rca_ground_truth.jsonl"
)

EVALUATION_DIR = OUTPUT / "evaluation"

GOLD_ACCESS_SENTINEL = (
    EVALUATION_DIR / "gold_access_started.json"
)


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_authorized_validation_projection(
    path: Path,
) -> list[dict[str, Any]]:
    """Read once and retain only preregistered evidence fields."""
    rows = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line in handle:
            if not line.strip():
                continue

            source = json.loads(line)

            rows.append({
                "case_id":
                    str(source["case_id"]),
                "evidence_ids": [
                    str(value)
                    for value
                    in source.get(
                        "evidence_ids",
                        [],
                    )
                ],
                "evidence_required": [
                    str(value)
                    for value
                    in source.get(
                        "evidence_required",
                        [],
                    )
                ],
            })

    return rows


def assert_one_shot_not_started(
    evaluation_dir: Path,
) -> None:
    """Fail closed if this scientific run has already begun evaluation."""
    if not evaluation_dir.exists():
        return

    files = [
        path
        for path in evaluation_dir.rglob("*")
        if path.is_file()
    ]

    if files:
        raise RuntimeError(
            "evaluation artifacts already exist; "
            "same-run one-shot evaluation rerun is prohibited"
        )


def write_gold_access_sentinel(
    path: Path,
    evaluator_freeze_manifest_sha256: str,
) -> None:
    """Persist fail-closed state before real validation-gold access."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if path.exists():
        raise RuntimeError(
            "gold-access sentinel already exists; "
            "same-run evaluation rerun is prohibited"
        )

    value = {
        "artifact_type":
            "phase6a3_graph_v1_1_gold_access_sentinel",
        "artifact_version": "1.0",
        "status":
            "GOLD_ACCESS_STARTED_FAIL_CLOSED",
        "run_id": RUN_ID,
        "created_at_utc": utc_now(),
        "metric_spec_sha256":
            EXPECTED_HASHES[METRIC_SPEC],
        "preregistration_sha256":
            EXPECTED_HASHES[PREREGISTRATION],
        "pre_gold_manifest_sha256":
            EXPECTED_HASHES[PRE_GOLD_MANIFEST],
        "evaluator_freeze_manifest_sha256":
            evaluator_freeze_manifest_sha256,
        "same_run_rerun_permitted": False,
        "heldout_gold_opened": False,
    }

    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )



# ---------------------------------------------------------------------------
# Complete preregistered in-memory evaluation
# ---------------------------------------------------------------------------

def compute_evaluation(
    evidence_projection: Sequence[Mapping[str, Any]],
    inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Compute all preregistered retrieval metrics from one in-memory projection."""
    route_by_id = inputs["route_by_id"]
    document_by_id = inputs["document_by_id"]

    truth_by_id = {
        str(row["case_id"]): row
        for row in evidence_projection
    }

    if len(truth_by_id) != EXPECTED_CASE_COUNT:
        raise RuntimeError(
            "validation evidence projection must contain "
            f"{EXPECTED_CASE_COUNT} unique cases"
        )

    if set(truth_by_id) != set(route_by_id):
        raise RuntimeError(
            "validation evidence and frozen route case universes differ"
        )

    case_ids = sorted(route_by_id)

    resolved = {
        case_id: resolve_evidence(
            truth_by_id[case_id],
            inputs["documents"],
        )
        for case_id in case_ids
    }

    required_by_case = {
        case_id: set(
            resolved[case_id].required_record_ids
        )
        for case_id in case_ids
    }

    candidate_metrics = {}
    graph_metrics = {}
    relational_metrics = {}

    for case_id in case_ids:
        candidate_metrics[case_id] = retrieval_case_metrics(
            resolved[case_id],
            inputs["candidate_by_case"][case_id],
            document_by_id,
        )

        graph_metrics[case_id] = retrieval_case_metrics(
            resolved[case_id],
            inputs["selected_by_case"][case_id],
            document_by_id,
        )

        relational_metrics[case_id] = retrieval_case_metrics(
            resolved[case_id],
            inputs["relational_by_case"][case_id],
            document_by_id,
        )

    candidate_aggregate = aggregate_retrieval(
        [candidate_metrics[c] for c in case_ids]
    )
    graph_aggregate = aggregate_retrieval(
        [graph_metrics[c] for c in case_ids]
    )
    relational_aggregate = aggregate_retrieval(
        [relational_metrics[c] for c in case_ids]
    )

    paired_recall = core.paired_recall_summary(
        {
            c: float(graph_metrics[c]["document_recall"])
            for c in case_ids
        },
        {
            c: float(relational_metrics[c]["document_recall"])
            for c in case_ids
        },
    )

    paired_full = core.paired_full_evidence_summary(
        {
            c: bool(graph_metrics[c]["full_evidence_coverage"])
            for c in case_ids
        },
        {
            c: bool(relational_metrics[c]["full_evidence_coverage"])
            for c in case_ids
        },
    )

    selection_loss = core.candidate_to_selection_summary(
        candidate_metrics,
        graph_metrics,
    )

    minimum_depth = core.minimum_reachable_depths(
        inputs["anchors"],
        inputs["candidate_paths"],
    )

    depth_diagnostics = core.required_depth_diagnostics(
        required_by_case,
        {
            c: set(inputs["selected_by_case"][c])
            for c in case_ids
        },
        {
            c: set(inputs["relational_by_case"][c])
            for c in case_ids
        },
        minimum_depth,
    )

    drop_diagnostics = required_drop_summary(
        inputs["record_drops"],
        required_by_case,
    )

    anchor_metrics = per_anchor_summary(
        route_by_id,
        graph_metrics,
        relational_metrics,
    )

    bank_metrics = bank_transaction_summary(
        route_by_id,
        required_by_case,
        inputs["candidate_by_case"],
        inputs["selected_by_case"],
        candidate_metrics,
        graph_metrics,
        relational_metrics,
    )

    graph_macro = float(
        graph_aggregate["macro"]["document_recall"]
    )
    relational_macro = float(
        relational_aggregate["macro"]["document_recall"]
    )
    candidate_macro = float(
        candidate_aggregate["macro"]["document_recall"]
    )

    paired_delta = float(
        paired_recall[
            "paired_macro_recall_difference_graph_minus_relational"
        ]
    )

    if abs(
        (graph_macro - relational_macro) - paired_delta
    ) > 1e-12:
        raise RuntimeError(
            "macro/paired recall difference identity failed"
        )

    selection_delta = float(
        selection_loss[
            "mean_candidate_to_selection_recall_loss"
        ]
    )

    if abs(
        (candidate_macro - graph_macro) - selection_delta
    ) > 1e-12:
        raise RuntimeError(
            "candidate-to-selection recall-loss identity failed"
        )

    source_tokens = {
        "graph_selected": token_distribution([
            float(
                graph_metrics[c][
                    "retrieved_context_tokens"
                ]
            )
            for c in case_ids
        ]),
        "relational_rag": token_distribution([
            float(
                relational_metrics[c][
                    "retrieved_context_tokens"
                ]
            )
            for c in case_ids
        ]),
    }

    recall_outcome = {
        row["case_id"]: row["outcome"]
        for row in paired_recall["cases"]
    }

    full_outcome = {
        row["case_id"]: row["outcome"]
        for row in paired_full["cases"]
    }

    top40_harmed = {
        row["case_id"]
        for row in selection_loss["harmed_cases"]
    }

    multihop_cases = {
        row["case_id"]
        for row in depth_diagnostics[
            "multi_hop_benefit"
        ]["cases"]
    }

    made_complete_cases = {
        row["case_id"]
        for row in depth_diagnostics[
            "made_complete_by_multi_hop"
        ]["cases"]
    }

    case_level = []

    for case_id in case_ids:
        case_level.append({
            "case_id": case_id,
            "primary_entity_type":
                route_by_id[case_id]["primary_entity_type"],

            "required_record_ids":
                sorted(required_by_case[case_id]),

            "candidate_pool": {
                "record_count":
                    len(inputs["candidate_by_case"][case_id]),
                "document_recall":
                    candidate_metrics[case_id]["document_recall"],
                "full_evidence_coverage":
                    candidate_metrics[case_id][
                        "full_evidence_coverage"
                    ],
                "missing_required_record_ids":
                    candidate_metrics[case_id][
                        "missing_required_record_ids"
                    ],
            },

            "graph_selected_top40": {
                "record_count":
                    len(inputs["selected_by_case"][case_id]),
                "document_recall":
                    graph_metrics[case_id]["document_recall"],
                "full_evidence_coverage":
                    graph_metrics[case_id][
                        "full_evidence_coverage"
                    ],
                "strict_full_contract_coverage":
                    graph_metrics[case_id][
                        "strict_full_contract_coverage"
                    ],
                "missing_required_record_ids":
                    graph_metrics[case_id][
                        "missing_required_record_ids"
                    ],
            },

            "relational_rag": {
                "record_count":
                    len(inputs["relational_by_case"][case_id]),
                "document_recall":
                    relational_metrics[case_id]["document_recall"],
                "full_evidence_coverage":
                    relational_metrics[case_id][
                        "full_evidence_coverage"
                    ],
                "missing_required_record_ids":
                    relational_metrics[case_id][
                        "missing_required_record_ids"
                    ],
            },

            "graph_vs_relational_recall_outcome":
                recall_outcome[case_id],

            "graph_vs_relational_full_evidence_outcome":
                full_outcome[case_id],

            "harmed_by_top40":
                case_id in top40_harmed,

            "multi_hop_benefit":
                case_id in multihop_cases,

            "made_complete_by_multi_hop":
                case_id in made_complete_cases,
        })

    return {
        "artifact_type":
            "phase6a3_graph_v1_1_one_shot_evaluation",
        "artifact_version": "1.0",
        "run_id": RUN_ID,
        "case_count": len(case_ids),

        "graph_candidate_pool": {
            "macro_document_recall":
                candidate_macro,
            "full_evidence_coverage":
                candidate_aggregate["macro"][
                    "full_evidence_coverage"
                ],
            "strict_full_contract_coverage":
                candidate_aggregate["macro"][
                    "strict_full_contract_coverage"
                ],
        },

        "graph_selected_top40": {
            "macro_document_recall":
                graph_macro,
            "full_evidence_coverage":
                graph_aggregate["macro"][
                    "full_evidence_coverage"
                ],
            "strict_full_contract_coverage":
                graph_aggregate["macro"][
                    "strict_full_contract_coverage"
                ],
            "maximum_records_per_case":
                MAX_SELECTED_RECORDS,
        },

        "relational_rag": {
            "macro_document_recall":
                relational_macro,
            "full_evidence_coverage":
                relational_aggregate["macro"][
                    "full_evidence_coverage"
                ],
            "maximum_budget_contract":
                MAX_SELECTED_RECORDS,
            "padding_applied": False,
        },

        "graph_vs_relational": {
            "paired_macro_recall_difference_graph_minus_relational":
                paired_delta,

            "paired_macro_recall_difference_ci":
                paired_recall[
                    "paired_macro_recall_difference_ci"
                ],

            "better_equal_worse":
                paired_recall["better_equal_worse"],

            "full_evidence": {
                key: paired_full[key]
                for key in (
                    "GRAPH_ONLY_FULL",
                    "RELATIONAL_ONLY_FULL",
                    "BOTH_FULL",
                    "NEITHER_FULL",
                    "graph_full_evidence_rate",
                    "relational_full_evidence_rate",
                    "full_evidence_rate_difference_graph_minus_relational",
                    "discordant_pair_count",
                    "mcnemar_exact_two_sided_p_value",
                )
            },
        },

        "candidate_to_selection":
            selection_loss,

        "required_records_among_structural_drops":
            drop_diagnostics,

        "depth_and_multi_hop_diagnostics":
            depth_diagnostics,

        "per_anchor_metrics":
            anchor_metrics,

        "bank_transaction_subset":
            bank_metrics,

        "source_token_distribution":
            source_tokens,

        "latency":
            "NOT_COMPUTED_IN_CLEAN_ONE_SHOT_EVALUATION",

        "case_level_metrics":
            case_level,

        "scientific_interpretation": {
            "retrieval_comparison_only": True,
            "RCA_accuracy_computed": False,
            "causal_relation_importance_claimed": False,
            "graph_redesign_performed": False,
        },
    }



# ---------------------------------------------------------------------------
# Frozen evaluator-stack verification
# ---------------------------------------------------------------------------

EVALUATOR_FREEZE_MANIFEST = (
    OUTPUT / "evaluator_freeze_manifest.json"
)

SYNTHETIC_TEST_RESULTS = (
    OUTPUT / "synthetic_test_results.json"
)

CORE_TEST_PATH = (
    OUTPUT / "test_one_shot_evaluator.py"
)

RUNNER_TEST_PATH = (
    OUTPUT / "test_one_shot_runner.py"
)


def verify_evaluator_freeze(
    expected_manifest_sha256: str,
) -> dict[str, Any]:
    if not EVALUATOR_FREEZE_MANIFEST.is_file():
        raise RuntimeError(
            "missing evaluator_freeze_manifest.json"
        )

    observed_manifest_sha256 = sha256_file(
        EVALUATOR_FREEZE_MANIFEST
    )

    if (
        observed_manifest_sha256
        != expected_manifest_sha256
    ):
        raise RuntimeError(
            "evaluator freeze manifest SHA-256 mismatch: "
            f"expected={expected_manifest_sha256} "
            f"observed={observed_manifest_sha256}"
        )

    manifest = load_json(
        EVALUATOR_FREEZE_MANIFEST
    )

    if (
        manifest.get("status")
        != "FROZEN_BEFORE_GOLD"
    ):
        raise RuntimeError(
            "evaluator freeze status is not "
            "FROZEN_BEFORE_GOLD"
        )

    required_components = {
        "evaluator_core":
            CORE_PATH,
        "one_shot_runner":
            Path(__file__).resolve(),
        "evaluator_core_tests":
            CORE_TEST_PATH,
        "one_shot_runner_tests":
            RUNNER_TEST_PATH,
        "synthetic_test_results":
            SYNTHETIC_TEST_RESULTS,
        "metric_spec":
            METRIC_SPEC,
        "preregistration":
            PREREGISTRATION,
        "rag_corpus_source":
            ROOT / "src/rag/corpus.py",
        "rag_evaluation_source":
            ROOT / "src/rag/evaluation.py",
        "rag_evidence_source":
            ROOT / "src/rag/evidence.py",
        "rag_tokens_source":
            ROOT / "src/rag/tokens.py",
        "rag_config_source":
            ROOT / "src/rag/config.py",
    }

    checks = []

    for name, path in required_components.items():
        entry = manifest.get("components", {}).get(
            name
        )

        if not isinstance(entry, dict):
            raise RuntimeError(
                "freeze manifest missing component: "
                f"{name}"
            )

        expected = str(entry["sha256"])
        observed = sha256_file(path)

        row = {
            "component": name,
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
                "frozen evaluator component changed: "
                f"{name}"
            )

        checks.append(row)

    if (
        manifest.get("bootstrap_seed")
        != BOOTSTRAP_SEED
    ):
        raise RuntimeError(
            "bootstrap seed mismatch in evaluator freeze"
        )

    if (
        manifest.get("bootstrap_resamples")
        != BOOTSTRAP_RESAMPLES
    ):
        raise RuntimeError(
            "bootstrap resample count mismatch "
            "in evaluator freeze"
        )

    if (
        manifest.get("validation_gold_opened")
        is not False
    ):
        raise RuntimeError(
            "freeze manifest does not attest "
            "validation_gold_opened=false"
        )

    if (
        manifest.get("heldout_gold_opened")
        is not False
    ):
        raise RuntimeError(
            "freeze manifest does not attest "
            "heldout_gold_opened=false"
        )

    return {
        "status": "PASS",
        "manifest_sha256":
            observed_manifest_sha256,
        "component_checks": checks,
    }


# ---------------------------------------------------------------------------
# Final artifact writer
# ---------------------------------------------------------------------------

def write_final_outputs(
    result: Mapping[str, Any],
    pre_gold_verification: Mapping[str, Any],
    evaluator_freeze_verification:
        Mapping[str, Any],
    gold_access_started_at: str,
    validation_gold_opened_at: str,
) -> dict[str, str]:
    metrics_path = (
        EVALUATION_DIR / "one_shot_metrics.json"
    )
    cases_path = (
        EVALUATION_DIR / "case_level_metrics.jsonl"
    )
    integrity_path = (
        EVALUATION_DIR / "scientific_integrity.json"
    )
    verification_path = (
        EVALUATION_DIR / "input_verification.json"
    )
    determinism_path = (
        EVALUATION_DIR / "evaluation_determinism.json"
    )

    compact = {
        key: value
        for key, value in result.items()
        if key != "case_level_metrics"
    }

    write_json(metrics_path, compact)

    write_jsonl(
        cases_path,
        result["case_level_metrics"],
    )

    write_json(
        verification_path,
        {
            "status": "PASS",
            "run_id": RUN_ID,
            "validation_gold_opened":
                False,
            "pre_gold_verification":
                pre_gold_verification,
            "evaluator_freeze_verification":
                evaluator_freeze_verification,
        },
    )

    write_json(
        determinism_path,
        {
            "artifact_type":
                "phase6a3_one_shot_evaluation_determinism",
            "artifact_version": "1.0",
            "status": "PASS",
            "run_id": RUN_ID,
            "method":
                "DOUBLE_COMPUTE_FROM_SAME_IN_MEMORY_GOLD_PROJECTION",
            "byte_identical":
                True,
            "bootstrap_seed":
                BOOTSTRAP_SEED,
            "bootstrap_resamples":
                BOOTSTRAP_RESAMPLES,
        },
    )

    write_json(
        integrity_path,
        {
            "artifact_type":
                "phase6a3_graph_v1_1_scientific_integrity",
            "artifact_version": "1.0",
            "status": "PASS",
            "run_id": RUN_ID,

            "gold_access_started_at_utc":
                gold_access_started_at,

            "validation_gold_opened_at_utc":
                validation_gold_opened_at,

            "validation_gold_projection": [
                "case_id",
                "evidence_ids",
                "evidence_required",
            ],

            "validation_gold_visible_to_retriever":
                False,

            "retrieval_modified_after_gold":
                False,

            "selection_modified_after_gold":
                False,

            "relational_rag_rerun":
                False,

            "graph_retraversed_after_gold":
                False,

            "heldout_gold_opened":
                False,

            "LLM_used":
                False,

            "API_calls_made":
                False,

            "embeddings_created":
                False,

            "RCA_accuracy_computed":
                False,

            "same_run_rerun_permitted":
                False,

            "metric_spec_sha256":
                EXPECTED_HASHES[METRIC_SPEC],

            "preregistration_sha256":
                EXPECTED_HASHES[PREREGISTRATION],

            "pre_gold_manifest_sha256":
                EXPECTED_HASHES[
                    PRE_GOLD_MANIFEST
                ],

            "evaluator_freeze_manifest_sha256":
                evaluator_freeze_verification[
                    "manifest_sha256"
                ],
        },
    )

    inventory_path = (
        EVALUATION_DIR
        / "evaluation_artifact_hashes.json"
    )

    output_paths = [
        GOLD_ACCESS_SENTINEL,
        metrics_path,
        cases_path,
        integrity_path,
        verification_path,
        determinism_path,
    ]

    inventory = {
        "artifact_type":
            "phase6a3_one_shot_evaluation_artifact_inventory",
        "artifact_version": "1.0",
        "status": "PASS",
        "run_id": RUN_ID,
        "hash_algorithm": "SHA-256",
        "hash_scope": "RAW_FILE_BYTES",
        "artifacts": {
            path.relative_to(
                OUTPUT
            ).as_posix():
                metadata(path)
            for path in output_paths
        },
        "self_hash_omitted": True,
        "heldout_gold_opened": False,
    }

    write_json(
        inventory_path,
        inventory,
    )

    return {
        "metrics_sha256":
            sha256_file(metrics_path),
        "case_level_metrics_sha256":
            sha256_file(cases_path),
        "scientific_integrity_sha256":
            sha256_file(integrity_path),
        "artifact_inventory_sha256":
            sha256_file(inventory_path),
    }


# ---------------------------------------------------------------------------
# Final CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    mode = parser.add_mutually_exclusive_group(
        required=True
    )

    mode.add_argument(
        "--preflight",
        action="store_true",
    )

    mode.add_argument(
        "--run",
        action="store_true",
    )

    parser.add_argument(
        "--evaluator-freeze-manifest-sha256",
        required=True,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Every check below is non-gold.
    static_hash_checks = verify_expected_hashes()
    pre_gold_inventory = verify_pre_gold_inventory()
    evaluator_freeze = verify_evaluator_freeze(
        args.evaluator_freeze_manifest_sha256
    )
    inputs = load_non_gold_inputs()

    pre_gold_verification = {
        "status": "PASS",
        "static_hash_check_count":
            len(static_hash_checks),
        "static_hash_checks":
            static_hash_checks,
        "pre_gold_inventory":
            pre_gold_inventory,
        "case_count":
            len(inputs["routes"]),
        "resolved_root_count":
            inputs["resolved_root_count"],
        "candidate_path_count":
            len(inputs["candidate_paths"]),
        "candidate_record_count":
            len(inputs["candidate_records"]),
        "selected_record_count":
            len(inputs["selected_records"]),
        "record_drop_count":
            len(inputs["record_drops"]),
        "route_counts":
            inputs["route_counts"],
        "validation_gold_opened":
            False,
        "heldout_gold_opened":
            False,
    }

    if args.preflight:
        print(
            json.dumps(
                {
                    "status":
                        "PASS_FINAL_PRE_GOLD_PREFLIGHT",
                    "run_id":
                        RUN_ID,
                    "validation_gold_opened":
                        False,
                    "heldout_gold_opened":
                        False,
                    "evaluator_freeze_manifest_sha256":
                        evaluator_freeze[
                            "manifest_sha256"
                        ],
                    "case_count":
                        len(inputs["routes"]),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    # From this point onward, failure closes this scientific run.
    assert_one_shot_not_started(
        EVALUATION_DIR
    )

    gold_access_started_at = utc_now()

    write_gold_access_sentinel(
        GOLD_ACCESS_SENTINEL,
        evaluator_freeze[
            "manifest_sha256"
        ],
    )

    try:
        validation_gold_opened_at = utc_now()

        # The only real validation-gold open in this runner.
        projection = (
            load_authorized_validation_projection(
                VALIDATION_GOLD_PATH
            )
        )

        if len(projection) != EXPECTED_CASE_COUNT:
            raise RuntimeError(
                "validation projection row count mismatch: "
                f"{len(projection)}"
            )

        if len({
            row["case_id"]
            for row in projection
        }) != EXPECTED_CASE_COUNT:
            raise RuntimeError(
                "validation projection unique-case "
                "count mismatch"
            )

        # Determinism is tested without reopening gold.
        first = compute_evaluation(
            projection,
            inputs,
        )

        second = compute_evaluation(
            projection,
            inputs,
        )

        if (
            canonical_bytes(first)
            != canonical_bytes(second)
        ):
            raise RuntimeError(
                "one-shot evaluation is not deterministic "
                "from identical in-memory inputs"
            )

        outputs = write_final_outputs(
            first,
            pre_gold_verification,
            evaluator_freeze,
            gold_access_started_at,
            validation_gold_opened_at,
        )

        print(
            json.dumps(
                {
                    "status":
                        "PASS_ONE_SHOT_EVALUATION_COMPLETE",
                    "run_id":
                        RUN_ID,

                    "candidate_pool_macro_recall":
                        first[
                            "graph_candidate_pool"
                        ][
                            "macro_document_recall"
                        ],

                    "graph_selected_recall_at_40":
                        first[
                            "graph_selected_top40"
                        ][
                            "macro_document_recall"
                        ],

                    "graph_full_evidence_coverage":
                        first[
                            "graph_selected_top40"
                        ][
                            "full_evidence_coverage"
                        ],

                    "relational_recall_at_40":
                        first[
                            "relational_rag"
                        ][
                            "macro_document_recall"
                        ],

                    "relational_full_evidence_coverage":
                        first[
                            "relational_rag"
                        ][
                            "full_evidence_coverage"
                        ],

                    "paired_macro_recall_difference":
                        first[
                            "graph_vs_relational"
                        ][
                            "paired_macro_recall_difference_graph_minus_relational"
                        ],

                    "mcnemar_exact_two_sided_p_value":
                        first[
                            "graph_vs_relational"
                        ][
                            "full_evidence"
                        ][
                            "mcnemar_exact_two_sided_p_value"
                        ],

                    **outputs,

                    "heldout_gold_opened":
                        False,
                },
                indent=2,
                sort_keys=True,
            )
        )

    except Exception as exc:
        write_json(
            EVALUATION_DIR
            / "evaluation_failed_after_gold_access.json",
            {
                "artifact_type":
                    "phase6a3_one_shot_evaluation_failure",
                "artifact_version": "1.0",
                "status":
                    "FAIL_CLOSED_AFTER_GOLD_ACCESS",
                "run_id":
                    RUN_ID,
                "created_at_utc":
                    utc_now(),
                "error_type":
                    type(exc).__name__,
                "error_message":
                    str(exc),
                "same_run_rerun_permitted":
                    False,
                "heldout_gold_opened":
                    False,
            },
        )

        raise


if __name__ == "__main__":
    main()
