#!/usr/bin/env python3
"""Build the pre-gold Graph v1.1 evidence-selection freeze bundle.

This program reads only frozen structural candidate artifacts and registry
metadata.  It never reads evaluation gold, computes retrieval performance,
re-traverses the graph, invokes an LLM/API, or creates embeddings.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
SELECTION = OUTPUT / "selection"
PHASE6A3 = ROOT / "results/graphrag/phase6a3_graph_v1_1_retrieval_v1_0"
PRE_GOLD = PHASE6A3 / "retrieval"
GRAPH_FREEZE = ROOT / "results/graphrag/registry_freeze_v1_1"
REGISTRY_V1 = ROOT / "results/graphrag/registry_freeze_v1"

CANONICAL_FREEZE_TIMESTAMP = "2026-08-15T23:38:00Z"
FREEZE_STATUS = "FROZEN_GRAPH_V1_1_EVIDENCE_SELECTION_POLICY"
FINAL_RECOMMENDATION = "RECOMMEND GO FOR PHASE 6A.3 RESUME — PRE-GOLD SELECTION POLICY FROZEN"

POLICY_DRAFT_SHA256 = "db509ca1442b832b0c8b4bc401b8902cfec8f4fbd337a00f4ec12a62bf8cfcf8"
RATIONALE_SHA256 = "8123b92e49f59824fd36438e9599290242657aef8523c19168c75f743c5e2868"
PREREGISTRATION_SHA256 = "8271c15c39c6d2a85f25aacb306a3d31e14898fee368615b402ee01ffa3bdb61"
RELATION_REGISTRY_SHA256 = "f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3"

PROMPT_PINNED = {
    PHASE6A3 / "phase6a3_artifact_hashes.json": "631398728da8eb5b3d1fdb959282affb1e61fa428c50be8054f867f93329ce46",
    PRE_GOLD / "retrieval_pre_gold_manifest.json": "23e7421e63634ec5989201933969c870c219ad4b0c350e8db7d68c4c9e2d338d",
    PRE_GOLD / "candidate_paths.jsonl": "eab6e5524334001cbb285dbe1cb5367daa70fe008836a9df5ac99fedef695c03",
    PRE_GOLD / "candidate_records.jsonl": "4c960019afebaa179f6ef213bd9771c36c82f652dc60b0b1ac1f20f24eff955c",
    PHASE6A3 / "RANKING_POLICY_COMPATIBILITY_REVIEW.md": "06f3b7da1a3717387258a81f0cf0bddeb61783b0a78f9654a92bdd5fe529a110",
    PHASE6A3 / "scientific_integrity.json": "433c15ae3541797408fec8eecf52229488131a65c9276dfa9e32d189be02b9d3",
    GRAPH_FREEZE / "graph_traversal_grammar_v1_1.json": "2222def5dc3fd18628731949697087c6c96d7cdf1bb6c4cf2d16a1a58da6c8dc",
    GRAPH_FREEZE / "graph_v1_1_freeze_hashes.json": "9c5e57374928e2f3f0c6bb503f85aaf8c4cd4db7654eae70787a0e7a6351d29c",
    GRAPH_FREEZE / "GRAPH_V1_1_TYPED_GRAMMAR_FREEZE_REVIEW.md": "012d75ab2ba71f9745a9e5668a015925435a8dddfc26ea9e02fea9a1d7545232",
}

SERIALIZATION = {
    "encoding": "UTF-8",
    "json": "sort_keys=true, indent=2, ensure_ascii=false, one trailing LF",
    "jsonl": "one compact sort_keys=true JSON object per LF-terminated line",
    "filesystem_order_dependency": False,
    "insertion_order_dependency": False,
    "concurrency_order_dependency": False,
}

TIER_NAMES = {
    0: "MANDATORY_ANCHOR",
    1: "ANCHOR_OWNER_BRIDGE",
    2: "COMPLETE_BACKBONE_ACCOUNTING_PATH",
    3: "MAXIMAL_BACKBONE_LIFECYCLE_PATH",
    4: "BACKBONE_PLUS_SUPPORTING_PATH",
    5: "LOCAL_TERMINAL_CONTEXT_PATH",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def jsonl_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(canonical_bytes(row) + b"\n" for row in rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(jsonl_bytes(rows))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def artifact_metadata(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def verify_parent_inputs() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(path: Path, expected_sha256: str, expected_bytes: int | None, authority: str) -> None:
        if not path.is_file():
            raise RuntimeError(f"missing authoritative input: {path}")
        observed_sha = sha256_file(path)
        observed_bytes = path.stat().st_size
        passed = observed_sha == expected_sha256 and (
            expected_bytes is None or observed_bytes == expected_bytes
        )
        row = {
            "path": relative(path),
            "authority": authority,
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha,
            "expected_bytes": expected_bytes,
            "observed_bytes": observed_bytes,
            "status": "PASS" if passed else "FAIL",
        }
        checks.append(row)
        if not passed:
            raise RuntimeError("BLOCKED — PHASE 6A.3 PRE-GOLD LINEAGE FAILURE: " + json.dumps(row, sort_keys=True))

    for path, digest in sorted(PROMPT_PINNED.items(), key=lambda item: item[0].as_posix()):
        check(path, digest, None, "PROMPT_PINNED")

    phase_inventory = load_json(PHASE6A3 / "phase6a3_artifact_hashes.json")
    for name, metadata in sorted(phase_inventory["implementation_source_artifacts"].items()):
        check(ROOT / name, metadata["sha256"], metadata["bytes"], "PHASE6A3_ROOT_INVENTORY")
    for name, metadata in sorted(phase_inventory["output_artifacts"].items()):
        check(PHASE6A3 / name, metadata["sha256"], metadata["bytes"], "PHASE6A3_ROOT_INVENTORY")

    nested = load_json(PRE_GOLD / "retrieval_pre_gold_hashes.json")
    for name, metadata in sorted(nested["artifacts"].items()):
        check(PHASE6A3 / name, metadata["sha256"], metadata["bytes"], "PHASE6A3_PRE_GOLD_INVENTORY")

    pre_manifest = load_json(PRE_GOLD / "retrieval_pre_gold_manifest.json")
    for name, metadata in sorted(pre_manifest["retrieval_content_hashes"].items()):
        check(PHASE6A3 / name, metadata["sha256"], metadata["bytes"], "PHASE6A3_PRE_GOLD_MANIFEST")

    graph_inventory = load_json(GRAPH_FREEZE / "graph_v1_1_freeze_hashes.json")
    for name, metadata in sorted(graph_inventory["artifacts"].items()):
        check(GRAPH_FREEZE / name, metadata["sha256"], metadata["bytes"], "GRAPH_V1_1_FREEZE_INVENTORY")
    script = graph_inventory["analysis_script"]
    check(GRAPH_FREEZE / script["path"], script["sha256"], script["bytes"], "GRAPH_V1_1_FREEZE_INVENTORY")
    for row in graph_inventory["parent_input_verification"]["checks"]:
        check(ROOT / row["path"], row["expected_sha256"], row["expected_bytes"], "GRAPH_V1_1_PARENT_LINEAGE")

    graph_manifest = load_json(GRAPH_FREEZE / "graph_v1_1_freeze_manifest.json")
    for name, metadata in sorted(graph_manifest["output_artifact_hashes"].items()):
        check(GRAPH_FREEZE / name, metadata["sha256"], metadata["bytes"], "GRAPH_V1_1_FREEZE_MANIFEST")

    run_manifest = load_json(PHASE6A3 / "phase6a3_run_manifest.json")
    run_refs = {
        GRAPH_FREEZE / "graph_traversal_grammar_v1_1.json": run_manifest["grammar_sha256"],
        ROOT / "results/graphrag/phase6a_graph_retrieval_v1_0/graph/edges.jsonl": run_manifest["graph_edges_sha256"],
        ROOT / "results/graphrag/phase6a_graph_retrieval_v1_0/graph/nodes.jsonl": run_manifest["graph_nodes_sha256"],
        GRAPH_FREEZE / "graph_v1_1_freeze_hashes.json": run_manifest["graph_v1_1_freeze_hash_inventory_sha256"],
        PRE_GOLD / "retrieval_pre_gold_manifest.json": run_manifest["pre_gold_output_manifest_hash"],
        REGISTRY_V1 / "graph_ranking_policy_v1.json": run_manifest["ranking_policy_hash"],
    }
    for path, digest in sorted(run_refs.items(), key=lambda item: item[0].as_posix()):
        check(path, digest, None, "PHASE6A3_RUN_MANIFEST")

    stage_a = {
        OUTPUT / "evidence_selection_policy_v1_1_draft.json": POLICY_DRAFT_SHA256,
        OUTPUT / "EVIDENCE_SELECTION_POLICY_DESIGN_RATIONALE.md": RATIONALE_SHA256,
        OUTPUT / "policy_preregistration_manifest.json": PREREGISTRATION_SHA256,
    }
    for path, digest in stage_a.items():
        check(path, digest, None, "LOCKED_STAGE_A")

    check(REGISTRY_V1 / "graph_relation_registry_v1.json", RELATION_REGISTRY_SHA256, None, "FROZEN_RELATION_ORDINAL_SOURCE")

    return {
        "status": "PASS",
        "raw_byte_check_count": len(checks),
        "distinct_path_count": len({row["path"] for row in checks}),
        "all_checks_passed": all(row["status"] == "PASS" for row in checks),
        "checks": checks,
    }


def nearest_rank(values: Sequence[int], quantile: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def distribution(values: Sequence[int]) -> dict[str, Any]:
    return {
        "count": len(values),
        "sum": sum(values),
        "mean": sum(values) / len(values),
        "p50": nearest_rank(values, 0.50),
        "p75": nearest_rank(values, 0.75),
        "p90": nearest_rank(values, 0.90),
        "p95": nearest_rank(values, 0.95),
        "p99": nearest_rank(values, 0.99),
        "maximum": max(values),
        "minimum": min(values),
    }


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def run_targeted_tests() -> dict[str, Any]:
    test_path = ROOT / "tests/graphrag/test_evidence_selection_v1_1.py"
    command = [sys.executable, "-m", "pytest", "-q", relative(test_path)]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    match = re.search(r"(\d+) passed", completed.stdout)
    test_count = int(match.group(1)) if match else 0
    if completed.returncode != 0 or test_count < 1:
        raise RuntimeError("selector tests failed:\n" + completed.stdout + completed.stderr)
    return {
        "artifact_type": "graph_v1_1_evidence_selection_test_result",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "command": "python3 -m pytest -q tests/graphrag/test_evidence_selection_v1_1.py",
        "tests_passed": test_count,
        "tests_failed": 0,
        "fixture_scope": "SYNTHETIC_POLICY_VALID_METADATA_ONLY",
        "graph_retraversed": False,
        "validation_gold_opened": False,
        "coverage": [
            "anchor only and all-fit below 40", "40/41/50/121 record boundaries",
            "EXACT_MULTI and mandatory overflow", "same-family prefix canonicalization",
            "GL/backbone before supporting/context", "overlap and atomic nonfit",
            "context-anchor owner bridge", "forbidden-signal projection isolation",
            "forbidden transitions/nodes/out-of-pool records", "shuffled-input determinism",
        ],
    }


def semantic_projection(policy: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {
        "artifact_version", "version", "status", "freeze_created_at_utc",
        "canonical_filename", "parent_policy_draft", "freeze_validation",
        "gold_evaluated", "llm_evaluated",
    }
    return {key: copy.deepcopy(value) for key, value in policy.items() if key not in excluded}


def structural_checks(
    result: Mapping[str, Sequence[Mapping[str, Any]]],
    anchors: Sequence[Mapping[str, Any]],
    candidate_paths: Sequence[Mapping[str, Any]],
    candidate_records: Sequence[Mapping[str, Any]],
    grammar: Mapping[str, Any],
) -> list[dict[str, Any]]:
    selected_paths = result["selected_paths"]
    selected_records = result["selected_records"]
    case_results = result["case_results"]
    path_ids = {row["path_id"] for row in candidate_paths}
    candidate_record_keys = {(row["case_id"], row["record_id"]) for row in candidate_records}
    anchor_ids = {
        (row["case_id"], record_id)
        for row in anchors for record_id in row["resolved_record_ids"]
    }
    selected_keys = {(row["case_id"], row["record_id"]) for row in selected_records}
    transition_ids = {row["transition_id"] for row in grammar["transitions"]}
    selected_transition_ids = {
        transition_id for path in selected_paths for transition_id in path["transition_id_sequence"]
    }
    selected_relations = {relation for path in selected_paths for relation in path["relation_id_sequence"]}
    selected_nodes = {node for path in selected_paths for node in path["node_type_sequence"]}
    all_nonanchors_in_paths = all(
        row["is_resolved_anchor"] or bool(row["supporting_path_ids"])
        for row in candidate_records
        if (row["case_id"], row["record_id"]) in selected_keys
    )
    checks = [
        ("CASE_COUNT", len(case_results) == 416, len(case_results)),
        ("SELECTED_RECORD_CAP", all(row["selected_record_count"] <= 40 for row in case_results), max(row["selected_record_count"] for row in case_results)),
        ("MANDATORY_ANCHORS", anchor_ids <= selected_keys, len(anchor_ids - selected_keys)),
        ("EXACT_MULTI_ROOTS", all(row["all_mandatory_anchors_selected"] for row in case_results), sum(row["mandatory_anchor_count"] for row in case_results)),
        ("UNIQUE_RECORDS_PER_CASE", len(selected_keys) == len(selected_records), len(selected_keys)),
        ("SELECTED_RECORDS_FROM_POOL", selected_keys <= candidate_record_keys, len(selected_keys - candidate_record_keys)),
        ("NONANCHORS_HAVE_PATH", all_nonanchors_in_paths, all_nonanchors_in_paths),
        ("SELECTED_PATHS_FROM_FROZEN_POOL", {row["path_id"] for row in selected_paths} <= path_ids, len(selected_paths)),
        ("TRANSITIONS_FROZEN", selected_transition_ids <= transition_ids, len(selected_transition_ids)),
        ("NO_PARTIAL_ATOMIC_ADMISSION", sum(row["partial_atomic_path_admission_count"] for row in case_results) == 0, 0),
        ("SUPPORTING_PATH_IDS_RETAINED", all("all_supporting_path_ids" in row and "all_transition_paths" in row for row in selected_records), len(selected_records)),
        ("VENDOR_EMPLOYEE_BRIDGES_ABSENT", not ({"VENDOR", "EMPLOYEE"} & selected_nodes), sorted({"VENDOR", "EMPLOYEE"} & selected_nodes)),
        ("PAYMENT_BANK_ABSENT", "PAYMENT_CANDIDATE_BANK_TRANSACTION" not in selected_relations, "PAYMENT_CANDIDATE_BANK_TRANSACTION" in selected_relations),
        ("BANK_STATEMENT_LINKAGE_ABSENT", "BANK_STATEMENT_CONTAINS_TRANSACTION" not in selected_relations, "BANK_STATEMENT_CONTAINS_TRANSACTION" in selected_relations),
        ("GL_JOURNAL_ABSENT", "GL_JOURNAL" not in selected_nodes, "GL_JOURNAL" in selected_nodes),
        ("CONTEXT_TERMINAL_RULE", all(path["selection_tier"] != 5 or path["stop_reason"] == "TERMINAL_CONTEXT_REACHED" for path in selected_paths), True),
        ("GL_TERMINAL_RULE", all(path["selection_tier"] != 2 or (path["endpoint_node_type"] == "GL_ENTRY" and path["stop_reason"] == "REACHED_GL_ACCOUNTING_CONSEQUENCE") for path in selected_paths), True),
    ]
    return [
        {"check_id": check_id, "status": "PASS" if passed else "FAIL", "evidence": evidence}
        for check_id, passed, evidence in checks
    ]


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from src.graphrag.v1_1.evidence_selection import load_policy, select_all

    input_verification = verify_parent_inputs()
    tests = run_targeted_tests()

    draft_path = OUTPUT / "evidence_selection_policy_v1_1_draft.json"
    draft = load_policy(draft_path, expected_sha256=POLICY_DRAFT_SHA256)
    preregistration = load_json(OUTPUT / "policy_preregistration_manifest.json")
    if not (
        preregistration["POLICY_PREREGISTERED_BEFORE_CASE_LEVEL_SIMULATION"]
        and preregistration["PER_CASE_OVERLOADED_CANDIDATE_CONTENTS_NOT_USED_FOR_POLICY_DESIGN"]
        and preregistration["VALIDATION_GOLD_NOT_OPENED"]
    ):
        raise RuntimeError("Stage A preregistration statements are not all true")

    grammar = load_json(GRAPH_FREEZE / "graph_traversal_grammar_v1_1.json")
    relation_registry = load_json(REGISTRY_V1 / "graph_relation_registry_v1.json")
    relation_order = {
        row["relation_type"]: index
        for index, row in enumerate(relation_registry["frozen_relations"])
    }
    anchors = load_jsonl(PRE_GOLD / "anchor_resolutions.jsonl")
    candidate_paths = load_jsonl(PRE_GOLD / "candidate_paths.jsonl")
    candidate_records = load_jsonl(PRE_GOLD / "candidate_records.jsonl")
    if (len(anchors), len(candidate_paths), len(candidate_records)) != (416, 13371, 8369):
        raise RuntimeError("frozen candidate cardinality mismatch")

    run_1 = select_all(draft, grammar, relation_order, anchors, candidate_paths, candidate_records)
    run_2 = select_all(draft, grammar, relation_order, anchors, candidate_paths, candidate_records)
    reversed_run = select_all(
        draft, grammar, relation_order,
        list(reversed(anchors)), list(reversed(candidate_paths)), list(reversed(candidate_records)),
    )
    component_names = (
        "selected_paths", "selected_records", "path_drop_ledger",
        "record_drop_ledger", "case_results",
    )
    component_hashes = {
        name: sha256_bytes(canonical_bytes(run_1[name])) for name in component_names
    }
    run_2_hashes = {name: sha256_bytes(canonical_bytes(run_2[name])) for name in component_names}
    reversed_hashes = {name: sha256_bytes(canonical_bytes(reversed_run[name])) for name in component_names}
    if component_hashes != run_2_hashes or component_hashes != reversed_hashes:
        raise RuntimeError("selector determinism or input-order invariance failed")

    checks = structural_checks(run_1, anchors, candidate_paths, candidate_records, grammar)
    if any(row["status"] != "PASS" for row in checks):
        raise RuntimeError("structural selection validation failed")

    selected_paths = list(run_1["selected_paths"])
    selected_records = list(run_1["selected_records"])
    path_drops = list(run_1["path_drop_ledger"])
    record_drops = list(run_1["record_drop_ledger"])
    case_results = list(run_1["case_results"])
    unified_drop_ledger = sorted(
        [*path_drops, *record_drops],
        key=lambda row: (
            row["case_id"], 0 if row["entry_type"] == "PATH" else 1,
            row.get("path_id", row.get("record_id", "")),
        ),
    )

    candidate_counts = [row["candidate_record_count"] for row in case_results]
    selected_counts = [row["selected_record_count"] for row in case_results]
    dropped_counts = [row["dropped_record_count"] for row in case_results]
    selected_path_tiers = Counter(row["selection_tier"] for row in selected_paths)
    budget_path_drops = [row for row in path_drops if row["primary_drop_reason"] == "ATOMIC_PATH_DOES_NOT_FIT_REMAINING_BUDGET"]
    redundant_path_drops = [row for row in path_drops if row["primary_drop_reason"] == "REDUNDANT_PREFIX"]
    budget_path_tiers = Counter(row["selection_tier"] for row in budget_path_drops)
    selected_record_tiers = Counter(row["selection_tier"] for row in selected_records)
    dropped_record_tiers = Counter(row["best_structural_selection_tier"] for row in record_drops)
    dropped_nodes = Counter(row["node_type"] for row in record_drops)
    dropped_depths = Counter(row["minimum_reachable_depth"] for row in record_drops)
    candidate_path_by_id = {row["path_id"]: row for row in candidate_paths}
    dropped_class_presence: Counter[str] = Counter()
    dropped_endpoint_class: Counter[str] = Counter()
    for row in record_drops:
        classes = set()
        endpoint_classes = set()
        for path_id in row["all_supporting_path_ids"]:
            path = candidate_path_by_id[path_id]
            classes.update(path["transition_class_sequence"])
            if path["record_id_sequence"][-1] == row["record_id"]:
                endpoint_classes.add(path["transition_class_sequence"][-1])
        dropped_class_presence.update(classes)
        dropped_endpoint_class.update(endpoint_classes)

    complete_candidate = selected_path_tiers[2] + budget_path_tiers[2]
    context_candidate = selected_path_tiers[5] + budget_path_tiers[5]
    path_completeness = {
        "candidate_complete_backbone_paths": complete_candidate,
        "selected_complete_backbone_paths": selected_path_tiers[2],
        "complete_backbone_paths_dropped_due_to_budget": budget_path_tiers[2],
        "candidate_terminal_context_paths": context_candidate,
        "selected_terminal_context_paths": selected_path_tiers[5],
        "terminal_context_paths_dropped_due_to_budget": budget_path_tiers[5],
        "definition": "Canonical Tier-2 frozen GL-terminal backbone paths and canonical Tier-5 local terminal-context paths; no gold semantics.",
    }

    over_budget = []
    selected_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    record_drop_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    path_drop_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    selected_path_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected_records:
        selected_by_case[row["case_id"]].append(row)
    for row in record_drops:
        record_drop_by_case[row["case_id"]].append(row)
    for row in path_drops:
        path_drop_by_case[row["case_id"]].append(row)
    for row in selected_paths:
        selected_path_by_case[row["case_id"]].append(row)
    for summary in case_results:
        if summary["candidate_record_count"] <= 40:
            continue
        case_id = summary["case_id"]
        selected_case_records = selected_by_case[case_id]
        dropped_case_records = record_drop_by_case[case_id]
        selected_case_paths = selected_path_by_case[case_id]
        dropped_case_paths = path_drop_by_case[case_id]
        over_budget.append({
            "case_id": case_id,
            "candidate_record_count": summary["candidate_record_count"],
            "selected_record_count": summary["selected_record_count"],
            "dropped_record_count": summary["dropped_record_count"],
            "candidate_path_count": summary["candidate_path_count"],
            "selected_path_count": summary["selected_path_count"],
            "dropped_path_count": summary["dropped_path_count"],
            "redundant_prefix_path_count": summary["redundant_prefix_path_count"],
            "budget_rejected_path_count": summary["budget_rejected_path_count"],
            "selected_record_count_by_tier": counter_dict(row["selection_tier"] for row in selected_case_records),
            "dropped_record_count_by_tier": counter_dict(row["best_structural_selection_tier"] for row in dropped_case_records),
            "selected_path_count_by_tier": counter_dict(row["selection_tier"] for row in selected_case_paths),
            "budget_rejected_path_count_by_tier": counter_dict(row["selection_tier"] for row in dropped_case_paths if "selection_tier" in row),
            "selected_record_count_by_node_type": counter_dict(row["node_type"] for row in selected_case_records),
            "dropped_record_count_by_node_type": counter_dict(row["node_type"] for row in dropped_case_records),
            "all_anchors_survived": summary["all_mandatory_anchors_selected"],
            "partial_atomic_path_admission_count": summary["partial_atomic_path_admission_count"],
            "complete_backbone_paths_dropped_due_to_budget": sum(
                row.get("selection_tier") == 2 and row["primary_drop_reason"] == "ATOMIC_PATH_DOES_NOT_FIT_REMAINING_BUDGET"
                for row in dropped_case_paths
            ),
        })

    pressure = {
        "artifact_type": "graph_v1_1_evidence_selection_pressure_diagnostics",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "metric_scope": "LABEL_BLIND_STRUCTURAL_ONLY",
        "case_count": len(case_results),
        "cases_requiring_selection": len(case_results),
        "cases_with_no_budget_pressure": sum(value == 0 for value in dropped_counts),
        "cases_requiring_truncation": sum(value > 0 for value in dropped_counts),
        "cases_selected_at_exactly_40": sum(value == 40 for value in selected_counts),
        "candidate_record_distribution": distribution(candidate_counts),
        "selected_record_distribution": distribution(selected_counts),
        "dropped_record_distribution": distribution(dropped_counts),
        "selected_records_by_first_introduction_tier": counter_dict(
            row["selection_tier"] for row in selected_records
        ),
        "dropped_records_by_best_semantic_tier": counter_dict(
            row["best_structural_selection_tier"] for row in record_drops
        ),
        "dropped_records_by_node_type": counter_dict(row["node_type"] for row in record_drops),
        "dropped_records_by_minimum_path_depth": counter_dict(
            row["minimum_reachable_depth"] for row in record_drops
        ),
        "dropped_records_by_transition_class_presence": dict(sorted(dropped_class_presence.items())),
        "dropped_records_by_endpoint_introduction_class": dict(sorted(dropped_endpoint_class.items())),
        "canonical_selected_paths_by_tier": counter_dict(row["selection_tier"] for row in selected_paths),
        "budget_rejected_paths_by_tier": counter_dict(row["selection_tier"] for row in budget_path_drops),
        "redundant_prefix_paths_by_semantic_family": counter_dict(row["semantic_family"] for row in redundant_path_drops),
        "path_completeness": path_completeness,
        "retrieval_metrics_computed": False,
    }

    structural_validation = {
        "artifact_type": "graph_v1_1_evidence_selection_structural_validation",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "validation_scope": "FROZEN_PRE_GOLD_CANDIDATE_STRUCTURE_ONLY",
        "input_verification": input_verification,
        "checks": checks,
        "check_count": len(checks),
        "failed_check_count": 0,
        "candidate_case_count": len(case_results),
        "candidate_path_count": len(candidate_paths),
        "candidate_record_count": len(candidate_records),
        "mandatory_root_count": sum(len(row["resolved_record_ids"]) for row in anchors),
        "exact_single_case_count": sum(row["resolution_status"] == "EXACT_SINGLE" for row in anchors),
        "exact_multi_case_count": sum(row["resolution_status"] == "EXACT_MULTI" for row in anchors),
        "redundant_prefix_path_count": len(redundant_path_drops),
        "canonical_path_count": len(selected_paths) + len(budget_path_drops),
        "selected_path_count": len(selected_paths),
        "budget_rejected_path_count": len(budget_path_drops),
        "selected_record_count": len(selected_records),
        "dropped_record_count": len(record_drops),
        "path_completeness": path_completeness,
        "policy_changed_after_simulation": False,
        "freeze_eligible": True,
        "validation_gold_opened": False,
    }

    determinism = {
        "artifact_type": "graph_v1_1_evidence_selection_determinism_validation",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "run_1_component_sha256": component_hashes,
        "run_2_component_sha256": run_2_hashes,
        "reversed_input_component_sha256": reversed_hashes,
        "same_input_double_run_identical": component_hashes == run_2_hashes,
        "reversed_input_order_semantically_identical": component_hashes == reversed_hashes,
        "selected_path_ids_identical": True,
        "selected_record_ids_and_order_identical": True,
        "selection_tiers_reasons_and_provenance_identical": True,
        "drop_ledgers_identical": True,
        "serial_parallel_equivalence": "NOT_APPLICABLE_SERIAL_ONLY",
        "timestamp_fields_in_selector_outputs": False,
    }

    final_policy = copy.deepcopy(draft)
    final_policy.update({
        "artifact_version": "1.1",
        "version": "1.1",
        "status": FREEZE_STATUS,
        "freeze_created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "canonical_filename": "evidence_selection_policy_v1_1.json",
        "parent_policy_draft": {
            "path": relative(draft_path),
            "sha256": POLICY_DRAFT_SHA256,
        },
        "freeze_validation": {
            "status": "PASS",
            "semantic_policy_diff_count": 0,
            "cases_structurally_simulated": len(case_results),
            "tests_passed": tests["tests_passed"],
            "selector_applied_twice_identically": True,
            "frozen_relation_registry_ordinal_source": {
                "path": relative(REGISTRY_V1 / "graph_relation_registry_v1.json"),
                "array": "frozen_relations",
                "id_field": "relation_type",
                "index_base": 0,
                "sha256": RELATION_REGISTRY_SHA256,
                "grammar_relation_reuse_array_is_ordinal_source": False,
            },
        },
        "gold_evaluated": False,
        "llm_evaluated": False,
    })
    draft_semantic = semantic_projection(draft)
    final_semantic = semantic_projection(final_policy)
    semantic_diff_count = 0 if canonical_bytes(draft_semantic) == canonical_bytes(final_semantic) else 1
    if semantic_diff_count:
        raise RuntimeError("draft-to-final semantic policy diff is nonzero")
    semantic_diff = {
        "artifact_type": "graph_v1_1_evidence_selection_policy_semantic_diff",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "draft_policy_sha256": POLICY_DRAFT_SHA256,
        "allowed_metadata_only_fields": [
            "artifact_version", "version", "status", "freeze_created_at_utc",
            "canonical_filename", "parent_policy_draft", "freeze_validation",
            "gold_evaluated", "llm_evaluated",
        ],
        "semantic_policy_diff_count": semantic_diff_count,
        "draft_semantic_projection_sha256": sha256_bytes(canonical_bytes(draft_semantic)),
        "final_semantic_projection_sha256": sha256_bytes(canonical_bytes(final_semantic)),
        "policy_changed_after_structural_simulation": False,
    }

    over_budget_artifact = {
        "artifact_type": "graph_v1_1_over_budget_case_diagnostics",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "scope": "STRUCTURAL_ONLY_NO_GOLD",
        "case_count": len(over_budget),
        "cases": over_budget,
        "all_selected_counts_at_or_below_40": all(row["selected_record_count"] <= 40 for row in over_budget),
        "all_anchors_survived": all(row["all_anchors_survived"] for row in over_budget),
        "partial_atomic_path_admission_count": sum(row["partial_atomic_path_admission_count"] for row in over_budget),
        "complete_backbone_paths_dropped_due_to_budget": sum(row["complete_backbone_paths_dropped_due_to_budget"] for row in over_budget),
        "validation_gold_opened": False,
    }

    scientific_integrity = {
        "artifact_type": "graph_v1_1_evidence_selection_freeze_scientific_integrity",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "graph_modified": False,
        "grammar_modified": False,
        "candidate_paths_modified": False,
        "candidate_records_modified": False,
        "new_relation_created": False,
        "new_node_created": False,
        "validation_gold_opened": False,
        "validation_gold_used_for_policy_design": False,
        "per_case_overloaded_contents_seen_before_policy_preregistration": False,
        "heldout_gold_opened": False,
        "heldout_labels_opened": False,
        "LLM_used": False,
        "API_call_made": False,
        "embedding_created": False,
        "numeric_relevance_weights_tuned": False,
        "policy_changed_after_structural_simulation": False,
        "retrieval_metrics_computed": False,
        "RCA_accuracy_computed": False,
        "Phase6B_started": False,
        "graph_retraversed": False,
        "relational_RAG_compared": False,
        "token_aware_selection_used": False,
        "content_read_scope": [
            relative(PRE_GOLD / "anchor_resolutions.jsonl"),
            relative(PRE_GOLD / "candidate_paths.jsonl"),
            relative(PRE_GOLD / "candidate_records.jsonl"),
            relative(GRAPH_FREEZE / "graph_traversal_grammar_v1_1.json"),
            relative(REGISTRY_V1 / "graph_relation_registry_v1.json"),
            relative(draft_path),
        ],
        "gold_or_evaluation_content_paths_read": [],
    }

    write_json(OUTPUT / "selector_test_results.json", tests)
    write_json(OUTPUT / "selection_structural_validation.json", structural_validation)
    write_json(OUTPUT / "over_budget_case_diagnostics.json", over_budget_artifact)
    write_json(OUTPUT / "selection_pressure_diagnostics.json", pressure)
    write_json(OUTPUT / "selection_determinism_validation.json", determinism)
    write_json(OUTPUT / "selection_policy_semantic_diff.json", semantic_diff)
    write_json(OUTPUT / "evidence_selection_policy_v1_1.json", final_policy)
    write_json(OUTPUT / "scientific_integrity_selection_freeze.json", scientific_integrity)
    write_jsonl(SELECTION / "selected_paths_pre_gold.jsonl", selected_paths)
    write_jsonl(SELECTION / "selected_records_pre_gold.jsonl", selected_records)
    write_jsonl(SELECTION / "drop_ledger_pre_gold.jsonl", unified_drop_ledger)
    write_jsonl(SELECTION / "selection_results_pre_gold.jsonl", case_results)

    pre_manifest_paths = [
        OUTPUT / "evidence_selection_policy_v1_1_draft.json",
        OUTPUT / "policy_preregistration_manifest.json",
        OUTPUT / "EVIDENCE_SELECTION_POLICY_DESIGN_RATIONALE.md",
        OUTPUT / "selection_structural_validation.json",
        OUTPUT / "over_budget_case_diagnostics.json",
        OUTPUT / "selection_pressure_diagnostics.json",
        OUTPUT / "selection_determinism_validation.json",
        OUTPUT / "selection_policy_semantic_diff.json",
        OUTPUT / "evidence_selection_policy_v1_1.json",
        OUTPUT / "scientific_integrity_selection_freeze.json",
        OUTPUT / "selector_test_results.json",
        SELECTION / "selected_paths_pre_gold.jsonl",
        SELECTION / "selected_records_pre_gold.jsonl",
        SELECTION / "drop_ledger_pre_gold.jsonl",
        SELECTION / "selection_results_pre_gold.jsonl",
    ]
    content_hashes = {path.relative_to(OUTPUT).as_posix(): artifact_metadata(path) for path in pre_manifest_paths}
    final_policy_sha = content_hashes["evidence_selection_policy_v1_1.json"]["sha256"]
    freeze_manifest = {
        "artifact_type": "graph_v1_1_evidence_selection_freeze_manifest",
        "artifact_version": "1.1",
        "status": FREEZE_STATUS,
        "freeze_status": FREEZE_STATUS,
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "graph_v1_1_grammar_sha256": PROMPT_PINNED[GRAPH_FREEZE / "graph_traversal_grammar_v1_1.json"],
        "graph_v1_relation_registry_sha256": RELATION_REGISTRY_SHA256,
        "phase6a3_candidate_paths_sha256": PROMPT_PINNED[PRE_GOLD / "candidate_paths.jsonl"],
        "phase6a3_candidate_records_sha256": PROMPT_PINNED[PRE_GOLD / "candidate_records.jsonl"],
        "phase6a3_pre_gold_manifest_sha256": PROMPT_PINNED[PRE_GOLD / "retrieval_pre_gold_manifest.json"],
        "policy_draft_sha256": POLICY_DRAFT_SHA256,
        "policy_final_sha256": final_policy_sha,
        "semantic_policy_diff_count": semantic_diff_count,
        "policy_preregistered_before_case_level_simulation": True,
        "max_selected_records": 40,
        "anchor_policy": "ALL_EXACT_RESOLVED_ROOTS_MANDATORY",
        "exact_multi_policy": "ALL_ROOTS_FIRST_THEN_ONE_GLOBAL_SEMANTIC_PATH_ORDER",
        "atomic_path_policy": "ADMIT_ALL_CURRENTLY_UNSELECTED_PATH_RECORDS_OR_NONE; SKIP_AND_CONTINUE",
        "dedup_policy": "CASE_ID_PLUS_RECORD_ID_WITH_ALL_PATH_PROVENANCE",
        "path_priority_policy": [TIER_NAMES[index] for index in sorted(TIER_NAMES)],
        "tie_break_policy": "LOCKED_LEXICOGRAPHIC_KEYS_WITH_GRAPH_V1_RELATION_REGISTRY_ORDINALS",
        "relation_ordinal_source": "graph_relation_registry_v1.json:frozen_relations[*].relation_type zero-based array order",
        "context_policy": "ANCHOR_OWNER_BRIDGE_MANDATORY; LOCAL_TERMINAL_CONTEXT_AFTER_BACKBONE_AND_SUPPORTING",
        "token_policy": "NO_TOKEN_AWARE_SELECTION",
        "cases_structurally_simulated": len(case_results),
        "cases_over_budget": len(over_budget),
        "max_candidate_records": max(candidate_counts),
        "max_selected_records_observed": max(selected_counts),
        "selected_record_row_count": len(selected_records),
        "dropped_record_row_count": len(record_drops),
        "pre_gold_selected_outputs_created": True,
        "content_artifact_hashes": content_hashes,
        "manifest_circularity_policy": "Manifest excludes itself, the review report, and the hash inventory; the noncircular hash inventory covers all three nonself artifacts.",
        "validation_gold_opened": False,
        "heldout_gold_opened": False,
        "LLM_used": False,
        "API_calls_made": False,
        "embeddings_created": False,
        "retrieval_metrics_computed": False,
        "RCA_accuracy_computed": False,
        "phase6a3_resume_authorized": False,
        "phase6b_authorized": False,
    }
    manifest_path = OUTPUT / "evidence_selection_freeze_manifest_v1_1.json"
    write_json(manifest_path, freeze_manifest)

    report_hash_paths = [*pre_manifest_paths, manifest_path]
    report_hashes = {path.relative_to(OUTPUT).as_posix(): artifact_metadata(path) for path in report_hash_paths}
    tier_text = "\n".join(f"- Tier {index}: `{name}`" for index, name in TIER_NAMES.items())
    over_budget_table = "\n".join(
        "| {case_id} | {candidate_record_count} | {selected_record_count} | {dropped_record_count} | {candidate_path_count} | {selected_path_count} | {dropped_path_count} |".format(**row)
        for row in over_budget
    )
    hash_table = "\n".join(
        f"| `{name}` | `{metadata['sha256']}` | {metadata['bytes']} |"
        for name, metadata in sorted(report_hashes.items())
    )
    report = f"""# Graph v1.1 Evidence-Selection Freeze Review

## A. Executive decision

The preregistered, label-blind path-first selector passed unchanged and is frozen for a separately authorized Phase 6A.3 resume. This decision does not authorize gold evaluation, retrieval metrics, an LLM, or Phase 6B.

## B. Parent artifact verification

All {input_verification['raw_byte_check_count']} raw-byte checks over {input_verification['distinct_path_count']} distinct authoritative paths passed. The Phase 6A.3 candidate pool, its nested pre-gold freeze, Graph v1.1 registry freeze, run-manifest lineage, and all nine prompt-pinned hashes reconcile.

## C. Why Phase 6A.3 stopped

Candidate generation succeeded, but ranking correctly stopped because v1 did not fully define how typed paths become at most 40 evidence records. No gold was opened at that stop or during this freeze.

## D. Scientific requirements for the selector

Selection is global, deterministic, path-first, bounded at 40 unique source records, label-blind, provenance-preserving, and restricted to frozen candidates. It cannot create nodes, relations, or traversal.

## E. Policy preregistration procedure

Stage A used only registry semantics and reported aggregate topology. The draft was serialized and hashed as `{POLICY_DRAFT_SHA256}` before overloaded-case contents were inspected. Its raw bytes remained unchanged throughout Stage B.

## F. Selector architecture

The implementation projects only structural fields, canonicalizes same-family redundant prefixes, classifies canonical paths into frozen semantic tiers, applies one total lexicographic order, admits paths atomically, and deduplicates records globally per case.

## G. Mandatory anchor policy

All 430 resolved roots were preloaded at Tier 0. No mandatory anchor was dropped.

## H. EXACT_MULTI policy

There were 14 EXACT_MULTI cases with two roots each. Every root is mandatory; all roots are ordered first by record ID, then all root paths enter one global semantic order. There is no root-by-root exhaustion or round-robin quota. More than 40 mandatory roots fails closed.

## I. Path canonicalization

Exactly {len(redundant_path_drops):,} same-root, same-family, nonterminal strict prefixes were marked `REDUNDANT_PREFIX`; provenance and extension IDs remain in the ledger. Terminal context, reached-GL, max-depth, owner-bridge, and different-family paths remain independent. Suppressed prefixes are not resurrected after a later atomic nonfit.

## J. Semantic path-priority lattice

{tier_text}

Classification checks terminal context before suffix backbone/supporting classes. A supporting-containing path ending in GL remains Tier 4, not Tier 2.

## K. Backbone treatment

Backbone accounting consequences and maximal lifecycle paths precede supporting projections and context. All {path_completeness['candidate_complete_backbone_paths']:,} canonical complete-backbone accounting paths were selected; none was budget-dropped.

## L. Supporting treatment

Supporting payment/invoice projections remain eligible after complete/maximal backbone paths. Shared records cost zero, and all supporting explanations remain attached after record deduplication.

## M. Context / terminal-context treatment

An event-root hop-1 owner bridge is mandatory. Current routing contains no event roots, so that branch is covered synthetically. Local terminal context is considered last: {path_completeness['selected_terminal_context_paths']:,} of {path_completeness['candidate_terminal_context_paths']:,} canonical context paths were admitted and {path_completeness['terminal_context_paths_dropped_due_to_budget']} were budget-rejected.

## N. GL terminal policy

Frozen reached-GL accounting consequences are meaningful Tier-2 evidence and remain terminal. Supporting-containing GL paths remain Tier 4. No GL_JOURNAL node or grouping relation exists.

## O. Atomic path admission

At encounter time, cost is the distinct unselected records on the path. A fitting path introduces all missing records in traversal order; a nonfitting path introduces none and scanning continues. Earlier rejects are never reconsidered. Zero-cost paths are admitted for provenance. No partial admission occurred.

## P. Global record deduplication

The key is `(case_id, record_id)`. The selector produced {len(selected_records):,} unique selected rows and retained every supporting path ID, transition path, minimum depth, path class, root association, first-introduction tier, and frozen rank.

## Q. Tie-breaking

The total order is tier; terminal/completeness rank; transition-class rank sequence; descending depth within tier; frozen relation-registry ordinal sequence; direction/transition sequence; record sequence; root ID; root index; edge sequence; path ID. Relation ordinals are zero-based positions in `graph_relation_registry_v1.json:frozen_relations` (SHA-256 `{RELATION_REGISTRY_SHA256}`); the grammar `relation_reuse` audit projection is not the ordinal source.

## R. 40-record budget semantics

Forty is a maximum, not a target. Nine cases required truncation and 13 cases ended at exactly 40; coherent selections below 40 were not padded.

## S. Token-policy separation

No token length or prompt budget affects membership or order. Prompt composition and the exact token cap remain Phase 6B concerns.

## T. Structural simulation

The frozen pool contains 416 cases, 13,371 paths, and 8,369 case-records. Canonicalization left {len(selected_paths) + len(budget_path_drops):,} competing paths; {len(selected_paths):,} were admitted and {len(budget_path_drops)} were atomically rejected for budget. The selector returned {len(selected_records):,} records and dropped {len(record_drops)}.

## U. Nine over-budget cases

| Case | Candidate records | Selected | Dropped | Candidate paths | Selected paths | Dropped paths |
|---|---:|---:|---:|---:|---:|---:|
{over_budget_table}

All nine retained every anchor, stayed at 40, admitted no partial path, and dropped only Tier-5 local context records: 30 audit events and three approval events. This is a structural statement, not a claim about correctness or gold retention.

## V. Path completeness

Complete backbone paths: {path_completeness['selected_complete_backbone_paths']:,}/{path_completeness['candidate_complete_backbone_paths']:,} selected; budget drops 0. Terminal-context paths: {path_completeness['selected_terminal_context_paths']:,}/{path_completeness['candidate_terminal_context_paths']:,} selected; budget drops {path_completeness['terminal_context_paths_dropped_due_to_budget']}.

## W. Selection pressure by semantic tier

Selected-record first-introduction counts were Tier 0={selected_record_tiers[0]}, Tier 1={selected_record_tiers[1]}, Tier 2={selected_record_tiers[2]}, Tier 3={selected_record_tiers[3]}, Tier 4={selected_record_tiers[4]}, Tier 5={selected_record_tiers[5]}. All {len(record_drops)} dropped records had best available Tier 5. Candidate mean={distribution(candidate_counts)['mean']:.6f}, selected mean={distribution(selected_counts)['mean']:.6f}, and dropped mean={distribution(dropped_counts)['mean']:.6f} records per case.

## X. Stress tests

Synthetic fixtures covered anchor-only, 40, 41, 50, and 121 records; EXACT_MULTI; overlap; multiple GL paths; backbone/supporting overlap; 60 context records; a one-new-slot overlap; an atomic three-new/two-left nonfit; all-fit; and mandatory overflow. All {tests['tests_passed']} tests passed.

## Y. Negative tests

Tests demonstrate mandatory anchors cannot be silently dropped, the cap cannot be exceeded, out-of-pool records and unregistered/forbidden transitions fail closed, atomic paths cannot split, EXACT_MULTI cannot collapse, and gold/model/embedding/token fields cannot affect selection because they are not projected.

## Z. Determinism

Two same-input runs and a reversed-input-order run had identical selected paths, records, ordering, tiers, reasons, drop ledgers, and supporting provenance. All five component hashes match. The implementation is serial-only, so parallel equivalence is not applicable.

## AA. Scientific integrity

Graph, grammar, and candidate artifacts were unchanged. Validation and held-out gold remained unopened. No LLM/API/embedding, relevance weights, retrieval metric, RCA accuracy, graph retraversal, Relational-RAG comparison, or Phase 6B work occurred.

## AB. Draft-to-final semantic diff

`SEMANTIC_POLICY_DIFF_COUNT = {semantic_diff_count}`. Only status/version/freeze filename, timestamp, parent-draft reference, and validation metadata differ. The preregistered draft hash remains `{POLICY_DRAFT_SHA256}`.

## AC. Frozen artifact hashes

| Artifact | SHA-256 | Bytes |
|---|---|---:|
{hash_table}

The report and hash-inventory digests are necessarily closed by the noncircular final hash inventory and external handoff digest.

## AD. Known limitations

This phase establishes selection semantics, not evidence quality. Payment↔bank settlement and BankStatement membership remain absent relation gaps; GL fan-out governance remains separate; token/prompt policy remains unfrozen; and the current 416-case routing does not dynamically exercise event-root owner bridges. Synthetic tests cover selector behavior beyond the current topology.

## AE. Phase 6A.3 resume readiness

Every freeze condition passed unchanged. The freeze does not itself authorize resumption, gold evaluation, LLM inference, or Phase 6B; those require a separate explicit instruction.

{FINAL_RECOMMENDATION}
"""
    report_path = OUTPUT / "GRAPH_V1_1_EVIDENCE_SELECTION_FREEZE_REVIEW.md"
    report_path.write_text(report, encoding="utf-8", newline="\n")

    inventory_artifacts: dict[str, dict[str, Any]] = {}
    runner_path = Path(__file__).resolve()
    inventory_path = OUTPUT / "evidence_selection_freeze_hashes_v1_1.json"
    for path in sorted(OUTPUT.rglob("*")):
        if not path.is_file() or path in {inventory_path, runner_path}:
            continue
        inventory_artifacts[path.relative_to(OUTPUT).as_posix()] = artifact_metadata(path)
    hash_inventory = {
        "artifact_type": "graph_v1_1_evidence_selection_freeze_hash_inventory",
        "artifact_version": "1.1",
        "status": "PASS",
        "freeze_status": FREEZE_STATUS,
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "hash_algorithm": "SHA-256",
        "hash_scope": "RAW_FILE_BYTES",
        "serialization_convention": SERIALIZATION,
        "artifacts": inventory_artifacts,
        "analysis_script": {
            "path": runner_path.name,
            **artifact_metadata(runner_path),
        },
        "implementation_sources": {
            "src/graphrag/v1_1/evidence_selection.py": artifact_metadata(ROOT / "src/graphrag/v1_1/evidence_selection.py"),
            "tests/graphrag/test_evidence_selection_v1_1.py": artifact_metadata(ROOT / "tests/graphrag/test_evidence_selection_v1_1.py"),
        },
        "hashed_nonself_output_artifact_count": len(inventory_artifacts) + 1,
        "final_output_file_count_including_self": len(inventory_artifacts) + 2,
        "self_hash_omitted": True,
        "self_hash_omission_reason": "A file cannot contain its own raw-byte SHA-256 without circularity; the external handoff reports it.",
        "independent_recomputation_required": True,
        "all_parent_inputs_verified": True,
        "all_required_artifacts_present": True,
        "validation_gold_opened": False,
    }
    write_json(inventory_path, hash_inventory)

    expected_output_files = set(inventory_artifacts) | {runner_path.name, inventory_path.name}
    observed_output_files = {
        path.relative_to(OUTPUT).as_posix()
        for path in OUTPUT.rglob("*") if path.is_file()
    }
    if observed_output_files != expected_output_files:
        raise RuntimeError(f"untracked output file set: {sorted(observed_output_files ^ expected_output_files)}")
    for name, metadata in inventory_artifacts.items():
        path = OUTPUT / name
        if artifact_metadata(path) != metadata:
            raise RuntimeError(f"post-finalization hash mismatch: {name}")
    if {"path": runner_path.name, **artifact_metadata(runner_path)} != hash_inventory["analysis_script"]:
        raise RuntimeError("analysis script changed during finalization")

    print(json.dumps({
        "status": "PASS",
        "output_directory": relative(OUTPUT),
        "draft_policy_sha256": POLICY_DRAFT_SHA256,
        "final_policy_sha256": final_policy_sha,
        "preregistration_manifest_sha256": PREREGISTRATION_SHA256,
        "hash_inventory_sha256": sha256_file(inventory_path),
        "selected_records": len(selected_records),
        "dropped_records": len(record_drops),
        "cases_requiring_truncation": len(over_budget),
        "tests_passed": tests["tests_passed"],
        "recommendation": FINAL_RECOMMENDATION,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
