#!/usr/bin/env python3
"""Freeze the resumed Phase 6A.3 retrieval interface before gold access.

This stage only verifies and copies immutable pre-gold structural outputs.  It
does not import an evaluator, read gold, compute metrics, or rerun traversal or
selection.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
RETRIEVAL = OUTPUT / "retrieval"
BLOCKED = ROOT / "results/graphrag/phase6a3_graph_v1_1_retrieval_v1_0"
BLOCKED_RETRIEVAL = BLOCKED / "retrieval"
GRAMMAR_FREEZE = ROOT / "results/graphrag/registry_freeze_v1_1"
SELECTION_FREEZE = ROOT / "results/graphrag/evidence_selection_freeze_v1_1"

RUN_ID = "phase6a3_graph_v1_1_retrieval_v1_2_20260816T034800Z"
PRE_GOLD_FREEZE_COMPLETED_AT_UTC = "2026-08-16T03:48:00Z"

PINNED = {
    BLOCKED / "phase6a3_artifact_hashes.json": "631398728da8eb5b3d1fdb959282affb1e61fa428c50be8054f867f93329ce46",
    BLOCKED_RETRIEVAL / "retrieval_pre_gold_manifest.json": "23e7421e63634ec5989201933969c870c219ad4b0c350e8db7d68c4c9e2d338d",
    BLOCKED_RETRIEVAL / "candidate_paths.jsonl": "eab6e5524334001cbb285dbe1cb5367daa70fe008836a9df5ac99fedef695c03",
    BLOCKED_RETRIEVAL / "candidate_records.jsonl": "4c960019afebaa179f6ef213bd9771c36c82f652dc60b0b1ac1f20f24eff955c",
    BLOCKED / "RANKING_POLICY_COMPATIBILITY_REVIEW.md": "06f3b7da1a3717387258a81f0cf0bddeb61783b0a78f9654a92bdd5fe529a110",
    BLOCKED / "scientific_integrity.json": "433c15ae3541797408fec8eecf52229488131a65c9276dfa9e32d189be02b9d3",
    GRAMMAR_FREEZE / "graph_traversal_grammar_v1_1.json": "2222def5dc3fd18628731949697087c6c96d7cdf1bb6c4cf2d16a1a58da6c8dc",
    GRAMMAR_FREEZE / "graph_v1_1_freeze_hashes.json": "9c5e57374928e2f3f0c6bb503f85aaf8c4cd4db7654eae70787a0e7a6351d29c",
    GRAMMAR_FREEZE / "GRAPH_V1_1_TYPED_GRAMMAR_FREEZE_REVIEW.md": "012d75ab2ba71f9745a9e5668a015925435a8dddfc26ea9e02fea9a1d7545232",
    SELECTION_FREEZE / "evidence_selection_policy_v1_1_draft.json": "db509ca1442b832b0c8b4bc401b8902cfec8f4fbd337a00f4ec12a62bf8cfcf8",
    SELECTION_FREEZE / "evidence_selection_policy_v1_1.json": "cad5f2298d9dad62599cfe592304c08cf8808441586fb865d1f4824b3054ea1b",
    SELECTION_FREEZE / "policy_preregistration_manifest.json": "8271c15c39c6d2a85f25aacb306a3d31e14898fee368615b402ee01ffa3bdb61",
    SELECTION_FREEZE / "evidence_selection_freeze_hashes_v1_1.json": "34b665c70db0a13ea03f4969bc37c335d4df11d6d2a3c9f73c30dcb7a4137cd0",
}

SOURCE_COPY_MAP = {
    BLOCKED_RETRIEVAL / "anchor_resolutions.jsonl": RETRIEVAL / "anchor_resolutions.jsonl",
    BLOCKED_RETRIEVAL / "candidate_paths.jsonl": RETRIEVAL / "candidate_paths.jsonl",
    BLOCKED_RETRIEVAL / "candidate_records.jsonl": RETRIEVAL / "candidate_records.jsonl",
    SELECTION_FREEZE / "selection/selected_paths_pre_gold.jsonl": RETRIEVAL / "selected_paths.jsonl",
    SELECTION_FREEZE / "selection/selected_records_pre_gold.jsonl": RETRIEVAL / "selected_records.jsonl",
    SELECTION_FREEZE / "selection/drop_ledger_pre_gold.jsonl": RETRIEVAL / "drop_ledger.jsonl",
    SELECTION_FREEZE / "selection/selection_results_pre_gold.jsonl": RETRIEVAL / "retrieval_results.jsonl",
}

SERIALIZATION = {
    "encoding": "UTF-8",
    "json": "sort_keys=true, indent=2, ensure_ascii=false, one trailing LF",
    "jsonl": "copied as immutable raw bytes from frozen parent outputs",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def verify_inventory(
    inventory_path: Path,
    artifact_base: Path,
    *,
    artifact_field: str = "artifacts",
) -> list[dict[str, Any]]:
    inventory = load_json(inventory_path)
    checks = []
    for name, expected in sorted(inventory[artifact_field].items()):
        path = artifact_base / name
        observed = metadata(path)
        checks.append({
            "path": rel(path),
            "authority": rel(inventory_path),
            "expected": expected,
            "observed": observed,
            "status": "PASS" if observed == expected else "FAIL",
        })
    return checks


def main() -> None:
    RETRIEVAL.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []

    for path, expected in sorted(PINNED.items(), key=lambda item: item[0].as_posix()):
        observed = sha256_file(path)
        checks.append({
            "path": rel(path), "authority": "PROMPT_PINNED",
            "expected_sha256": expected, "observed_sha256": observed,
            "status": "PASS" if observed == expected else "FAIL",
        })

    blocked_inventory = load_json(BLOCKED / "phase6a3_artifact_hashes.json")
    for field, base in (
        ("implementation_source_artifacts", ROOT),
        ("output_artifacts", BLOCKED),
    ):
        for name, expected in sorted(blocked_inventory[field].items()):
            path = base / name
            observed = metadata(path)
            checks.append({
                "path": rel(path), "authority": "PHASE6A3_ROOT_INVENTORY",
                "expected": expected, "observed": observed,
                "status": "PASS" if observed == expected else "FAIL",
            })

    blocked_nested = load_json(BLOCKED_RETRIEVAL / "retrieval_pre_gold_hashes.json")
    for name, expected in sorted(blocked_nested["artifacts"].items()):
        path = BLOCKED / name
        observed = metadata(path)
        checks.append({
            "path": rel(path), "authority": "PHASE6A3_PRE_GOLD_INVENTORY",
            "expected": expected, "observed": observed,
            "status": "PASS" if observed == expected else "FAIL",
        })

    grammar_inventory = load_json(GRAMMAR_FREEZE / "graph_v1_1_freeze_hashes.json")
    for name, expected in sorted(grammar_inventory["artifacts"].items()):
        path = GRAMMAR_FREEZE / name
        observed = metadata(path)
        checks.append({
            "path": rel(path), "authority": "GRAPH_V1_1_FREEZE_INVENTORY",
            "expected": expected, "observed": observed,
            "status": "PASS" if observed == expected else "FAIL",
        })
    expected = grammar_inventory["analysis_script"]
    path = GRAMMAR_FREEZE / expected["path"]
    observed = metadata(path)
    checks.append({
        "path": rel(path), "authority": "GRAPH_V1_1_FREEZE_INVENTORY",
        "expected": {"bytes": expected["bytes"], "sha256": expected["sha256"]},
        "observed": observed,
        "status": "PASS" if observed == {"bytes": expected["bytes"], "sha256": expected["sha256"]} else "FAIL",
    })

    selection_inventory = load_json(SELECTION_FREEZE / "evidence_selection_freeze_hashes_v1_1.json")
    for name, expected in sorted(selection_inventory["artifacts"].items()):
        path = SELECTION_FREEZE / name
        observed = metadata(path)
        checks.append({
            "path": rel(path), "authority": "EVIDENCE_SELECTION_FREEZE_INVENTORY",
            "expected": expected, "observed": observed,
            "status": "PASS" if observed == expected else "FAIL",
        })
    expected = selection_inventory["analysis_script"]
    path = SELECTION_FREEZE / expected["path"]
    observed = metadata(path)
    checks.append({
        "path": rel(path), "authority": "EVIDENCE_SELECTION_FREEZE_INVENTORY",
        "expected": {"bytes": expected["bytes"], "sha256": expected["sha256"]},
        "observed": observed,
        "status": "PASS" if observed == {"bytes": expected["bytes"], "sha256": expected["sha256"]} else "FAIL",
    })
    for name, expected in sorted(selection_inventory["implementation_sources"].items()):
        path = ROOT / name
        observed = metadata(path)
        checks.append({
            "path": rel(path), "authority": "EVIDENCE_SELECTION_FREEZE_INVENTORY",
            "expected": expected, "observed": observed,
            "status": "PASS" if observed == expected else "FAIL",
        })

    failures = [row for row in checks if row["status"] != "PASS"]
    if failures:
        raise RuntimeError("pre-gold parent lineage failure: " + json.dumps(failures, sort_keys=True))

    for source, destination in SOURCE_COPY_MAP.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if destination.read_bytes() != source.read_bytes():
            raise RuntimeError(f"raw-byte copy mismatch: {source}")

    anchors = load_jsonl(RETRIEVAL / "anchor_resolutions.jsonl")
    candidate_paths = load_jsonl(RETRIEVAL / "candidate_paths.jsonl")
    candidate_records = load_jsonl(RETRIEVAL / "candidate_records.jsonl")
    selected_paths = load_jsonl(RETRIEVAL / "selected_paths.jsonl")
    selected_records = load_jsonl(RETRIEVAL / "selected_records.jsonl")
    drop_ledger = load_jsonl(RETRIEVAL / "drop_ledger.jsonl")
    retrieval_results = load_jsonl(RETRIEVAL / "retrieval_results.jsonl")
    grammar = load_json(GRAMMAR_FREEZE / "graph_traversal_grammar_v1_1.json")

    anchor_keys = {
        (row["case_id"], record_id)
        for row in anchors for record_id in row["resolved_record_ids"]
    }
    candidate_path_ids = {row["path_id"] for row in candidate_paths}
    candidate_record_keys = {(row["case_id"], row["record_id"]) for row in candidate_records}
    selected_path_ids = {row["path_id"] for row in selected_paths}
    selected_record_keys = {(row["case_id"], row["record_id"]) for row in selected_records}
    transition_ids = {row["transition_id"] for row in grammar["transitions"]}
    selected_transition_ids = {
        transition_id for row in selected_paths for transition_id in row["transition_id_sequence"]
    }
    selected_relations = {
        relation_id for row in selected_paths for relation_id in row["relation_id_sequence"]
    }
    selected_path_nodes = {
        node_type for row in selected_paths for node_type in row["node_type_sequence"]
    }
    selected_per_case = Counter(row["case_id"] for row in selected_records)
    selected_record_ids_by_case: dict[str, set[str]] = {}
    for row in selected_records:
        selected_record_ids_by_case.setdefault(row["case_id"], set()).add(row["record_id"])

    structural = [
        ("VALIDATION_CASE_COUNT", len(anchors) == len(retrieval_results) == 416, len(anchors)),
        ("RESOLVED_ROOT_COUNT", len(anchor_keys) == 430, len(anchor_keys)),
        ("CANDIDATE_PATH_COUNT", len(candidate_paths) == 13371, len(candidate_paths)),
        ("CANDIDATE_RECORD_COUNT", len(candidate_records) == 8369, len(candidate_records)),
        ("CANDIDATE_DEPTH_COUNTS", Counter(row["depth"] for row in candidate_paths) == {1: 3332, 2: 4477, 3: 5562}, dict(Counter(row["depth"] for row in candidate_paths))),
        ("SELECTED_PATH_COUNT", len(selected_paths) == 10558, len(selected_paths)),
        ("SELECTED_RECORD_COUNT", len(selected_records) == 8336, len(selected_records)),
        ("DROP_LEDGER_PARTITION", len(drop_ledger) == 2846, len(drop_ledger)),
        ("SELECTED_RECORD_CAP", max(selected_per_case.values()) <= 40, max(selected_per_case.values())),
        ("UNIQUE_SELECTED_RECORDS", len(selected_record_keys) == len(selected_records), len(selected_record_keys)),
        ("ALL_ANCHORS_RETAINED", anchor_keys <= selected_record_keys, len(anchor_keys - selected_record_keys)),
        ("SELECTED_RECORDS_FROM_CANDIDATES", selected_record_keys <= candidate_record_keys, len(selected_record_keys - candidate_record_keys)),
        ("SELECTED_PATHS_FROM_CANDIDATES", selected_path_ids <= candidate_path_ids, len(selected_path_ids - candidate_path_ids)),
        ("SELECTED_TRANSITIONS_FROM_GRAMMAR", selected_transition_ids <= transition_ids, len(selected_transition_ids - transition_ids)),
        ("NO_VENDOR_EMPLOYEE_PATH_ENTRY", not ({"VENDOR", "EMPLOYEE"} & selected_path_nodes), sorted({"VENDOR", "EMPLOYEE"} & selected_path_nodes)),
        ("NO_PAYMENT_BANK", "PAYMENT_CANDIDATE_BANK_TRANSACTION" not in selected_relations, False),
        ("NO_BANK_STATEMENT_MEMBERSHIP", "BANK_STATEMENT_CONTAINS_TRANSACTION" not in selected_relations, False),
        ("NO_GL_JOURNAL", "GL_JOURNAL" not in selected_path_nodes, False),
        ("NO_PARTIAL_ATOMIC_ADMISSION", sum(row["partial_atomic_path_admission_count"] for row in retrieval_results) == 0, 0),
        ("DETERMINISM_PARENT_PASS", load_json(SELECTION_FREEZE / "selection_determinism_validation.json")["status"] == "PASS", "PASS"),
        ("SEMANTIC_POLICY_DIFF_ZERO", load_json(SELECTION_FREEZE / "selection_policy_semantic_diff.json")["semantic_policy_diff_count"] == 0, 0),
        (
            "POST_CUTOFF_ACCEPTED_EVIDENCE_ZERO",
            load_json(BLOCKED / "implementation/preflight_validation.json")["topology_regression"]["accepted_post_cutoff_traversal_count"] == 0,
            load_json(BLOCKED / "implementation/preflight_validation.json")["topology_regression"]["accepted_post_cutoff_traversal_count"],
        ),
    ]
    structural_rows = [
        {"check_id": check_id, "status": "PASS" if passed else "FAIL", "evidence": evidence}
        for check_id, passed, evidence in structural
    ]
    if any(row["status"] != "PASS" for row in structural_rows):
        raise RuntimeError("final pre-gold structural gate failed")

    references = {
        "artifact_type": "phase6a3_resume_candidate_parent_references",
        "artifact_version": "1.1",
        "status": "FROZEN_PARENT_REFERENCE",
        "created_at_utc": PRE_GOLD_FREEZE_COMPLETED_AT_UTC,
        "parent_candidate_run": rel(BLOCKED),
        "candidate_paths": {
            "parent_path": rel(BLOCKED_RETRIEVAL / "candidate_paths.jsonl"),
            "copied_path": rel(RETRIEVAL / "candidate_paths.jsonl"),
            **metadata(RETRIEVAL / "candidate_paths.jsonl"),
        },
        "candidate_records": {
            "parent_path": rel(BLOCKED_RETRIEVAL / "candidate_records.jsonl"),
            "copied_path": rel(RETRIEVAL / "candidate_records.jsonl"),
            **metadata(RETRIEVAL / "candidate_records.jsonl"),
        },
        "literal_raw_byte_copies_created": True,
    }
    write_json(RETRIEVAL / "candidate_artifact_references.json", references)

    validation = {
        "artifact_type": "phase6a3_resume_final_pre_gold_freeze_validation",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": PRE_GOLD_FREEZE_COMPLETED_AT_UTC,
        "run_id": RUN_ID,
        "parent_lineage_check_count": len(checks),
        "parent_lineage_failure_count": 0,
        "parent_lineage_checks": checks,
        "structural_gate_check_count": len(structural_rows),
        "structural_gate_failure_count": 0,
        "structural_gate_checks": structural_rows,
        "source_copy_raw_bytes_identical": True,
        "retrieval_recomputed": False,
        "selection_recomputed": False,
        "validation_gold_opened": False,
        "heldout_gold_opened": False,
        "VALIDATION_GOLD_ACCESS_AUTHORIZED_FOR_OFFLINE_EVALUATOR": True,
    }
    write_json(RETRIEVAL / "pre_gold_freeze_validation.json", validation)

    selected_paths_meta = metadata(RETRIEVAL / "selected_paths.jsonl")
    selected_records_meta = metadata(RETRIEVAL / "selected_records.jsonl")
    drop_meta = metadata(RETRIEVAL / "drop_ledger.jsonl")
    results_meta = metadata(RETRIEVAL / "retrieval_results.jsonl")
    manifest = {
        "artifact_type": "phase6a3_resume_final_pre_gold_manifest",
        "artifact_version": "1.1",
        "status": "FROZEN_BEFORE_VALIDATION_GOLD",
        "retrieval_status": "FROZEN_BEFORE_VALIDATION_GOLD",
        "created_at_utc": PRE_GOLD_FREEZE_COMPLETED_AT_UTC,
        "pre_gold_freeze_completed_at_utc": PRE_GOLD_FREEZE_COMPLETED_AT_UTC,
        "run_id": RUN_ID,
        "parent_candidate_run": "phase6a3_graph_v1_1_retrieval_v1_0",
        "parent_candidate_run_path": rel(BLOCKED),
        "parent_candidate_run_hash_inventory": {"path": rel(BLOCKED / "phase6a3_artifact_hashes.json"), **metadata(BLOCKED / "phase6a3_artifact_hashes.json")},
        "graph_v1_1_grammar_hash": PINNED[GRAMMAR_FREEZE / "graph_traversal_grammar_v1_1.json"],
        "candidate_paths_hash": PINNED[BLOCKED_RETRIEVAL / "candidate_paths.jsonl"],
        "candidate_records_hash": PINNED[BLOCKED_RETRIEVAL / "candidate_records.jsonl"],
        "evidence_selection_policy_hash": PINNED[SELECTION_FREEZE / "evidence_selection_policy_v1_1.json"],
        "evidence_selection_hash_inventory": {"path": rel(SELECTION_FREEZE / "evidence_selection_freeze_hashes_v1_1.json"), **metadata(SELECTION_FREEZE / "evidence_selection_freeze_hashes_v1_1.json")},
        "anchor_resolutions_hash": sha256_file(RETRIEVAL / "anchor_resolutions.jsonl"),
        "selected_paths_hash": selected_paths_meta["sha256"],
        "selected_records_hash": selected_records_meta["sha256"],
        "drop_ledger_hash": drop_meta["sha256"],
        "retrieval_results_hash": results_meta["sha256"],
        "validation_case_count": len(anchors),
        "resolved_root_count": len(anchor_keys),
        "candidate_path_count": len(candidate_paths),
        "candidate_record_count": len(candidate_records),
        "selected_path_count": len(selected_paths),
        "selected_record_row_count": len(selected_records),
        "max_selected_records": 40,
        "max_selected_records_observed": max(selected_per_case.values()),
        "all_exact_anchors_retained": True,
        "all_exact_multi_roots_retained": True,
        "partial_atomic_path_violation_count": 0,
        "grammar_changed": False,
        "selection_policy_changed": False,
        "validation_gold_opened": False,
        "heldout_gold_opened": False,
        "retriever_has_gold_interface": False,
        "VALIDATION_GOLD_ACCESS_AUTHORIZED_FOR_OFFLINE_EVALUATOR": True,
    }
    manifest_path = RETRIEVAL / "final_pre_gold_manifest.json"
    write_json(manifest_path, manifest)

    artifact_paths = [
        RETRIEVAL / "anchor_resolutions.jsonl",
        RETRIEVAL / "candidate_paths.jsonl",
        RETRIEVAL / "candidate_records.jsonl",
        RETRIEVAL / "candidate_artifact_references.json",
        RETRIEVAL / "selected_paths.jsonl",
        RETRIEVAL / "selected_records.jsonl",
        RETRIEVAL / "drop_ledger.jsonl",
        RETRIEVAL / "retrieval_results.jsonl",
        RETRIEVAL / "pre_gold_freeze_validation.json",
        manifest_path,
    ]
    hash_inventory_path = RETRIEVAL / "final_pre_gold_hashes.json"
    hash_inventory = {
        "artifact_type": "phase6a3_resume_final_pre_gold_hash_inventory",
        "artifact_version": "1.1",
        "status": "PASS",
        "created_at_utc": PRE_GOLD_FREEZE_COMPLETED_AT_UTC,
        "hash_algorithm": "SHA-256",
        "hash_scope": "RAW_FILE_BYTES",
        "artifacts": {path.relative_to(OUTPUT).as_posix(): metadata(path) for path in artifact_paths},
        "freeze_script": {"path": Path(__file__).name, **metadata(Path(__file__))},
        "candidate_parent_references": references,
        "self_hash_omitted": True,
        "self_hash_omission_reason": "Raw self-hash is circular; it is externally recorded before first gold access.",
        "serialization": SERIALIZATION,
        "pre_gold_retrieval_frozen": True,
        "validation_gold_opened": False,
        "heldout_gold_opened": False,
    }
    write_json(hash_inventory_path, hash_inventory)

    for name, expected in hash_inventory["artifacts"].items():
        if metadata(OUTPUT / name) != expected:
            raise RuntimeError(f"post-write pre-gold hash mismatch: {name}")
    if metadata(Path(__file__)) != {key: hash_inventory["freeze_script"][key] for key in ("bytes", "sha256")}:
        raise RuntimeError("freeze script changed during finalization")

    print(json.dumps({
        "status": "FROZEN_BEFORE_VALIDATION_GOLD",
        "run_id": RUN_ID,
        "pre_gold_freeze_completed_at_utc": PRE_GOLD_FREEZE_COMPLETED_AT_UTC,
        "final_pre_gold_manifest_sha256": sha256_file(manifest_path),
        "final_pre_gold_hash_inventory_sha256": sha256_file(hash_inventory_path),
        "selected_paths_sha256": selected_paths_meta["sha256"],
        "selected_records_sha256": selected_records_meta["sha256"],
        "validation_gold_access_authorized_for_offline_evaluator": True,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
