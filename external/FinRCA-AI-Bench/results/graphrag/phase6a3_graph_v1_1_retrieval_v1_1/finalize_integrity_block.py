#!/usr/bin/env python3
"""Finalize a transparent Phase 6A.3 scientific-integrity block.

This program does not read validation or held-out artifacts and does not run
the evaluator.  It records a previously reported pre-freeze byte-access
incident, revokes the evaluation gate, and closes the artifact inventory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
RETRIEVAL = OUTPUT / "retrieval"
EVALUATION = OUTPUT / "evaluation"

RUN_ID = "phase6a3_graph_v1_1_retrieval_v1_1_20260816T011400Z"
FINALIZED_AT_UTC = "2026-08-16T01:19:00Z"
PRE_GOLD_FREEZE_COMPLETED_AT_UTC = "2026-08-16T01:14:00Z"
PRE_GOLD_MANIFEST_SHA256 = "e0139ab40956cd9fa548b6218087be990a70dda414e8f5300a52e26ce88b2661"
PRE_GOLD_HASH_INVENTORY_SHA256 = "18994f6b4f4785b0b7532a78d2d95b010e0b483140f57455e2e4175580ec2df7"
FINAL_RECOMMENDATION = "RECOMMEND BLOCK — PHASE 6A.3 SCIENTIFIC INTEGRITY OR IMPLEMENTATION FAILURE"


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


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> None:
    if sha256_file(RETRIEVAL / "final_pre_gold_manifest.json") != PRE_GOLD_MANIFEST_SHA256:
        raise RuntimeError("pre-gold manifest changed before incident finalization")
    if sha256_file(RETRIEVAL / "final_pre_gold_hashes.json") != PRE_GOLD_HASH_INVENTORY_SHA256:
        raise RuntimeError("pre-gold hash inventory changed before incident finalization")

    accessed_files = [
        {
            "path": "data/benchmark/validation/case_ids.txt",
            "operation": ["SHA256_RAW_BYTE_HASH", "NEWLINE_COUNT"],
            "reported_sha256_prefix": "fcfab5e4",
            "reported_line_count": 416,
        },
        {
            "path": "data/benchmark/validation/rca_ground_truth.jsonl",
            "operation": ["SHA256_RAW_BYTE_HASH", "NEWLINE_COUNT"],
            "reported_sha256_prefix": "de77604e",
            "reported_line_count": 416,
        },
        {
            "path": "data/benchmark/validation/case_entity_records.jsonl",
            "operation": ["SHA256_RAW_BYTE_HASH", "NEWLINE_COUNT"],
            "reported_sha256_prefix": "bc3f76bf",
            "reported_line_count": 2680,
        },
        {
            "path": "data/benchmark/validation/failure_manifest.csv",
            "operation": ["SHA256_RAW_BYTE_HASH", "NEWLINE_COUNT"],
            "reported_sha256_prefix": "4450ca6a",
            "reported_line_count": 417,
        },
        {
            "path": "data/benchmark/validation/benchmark_questions.jsonl",
            "operation": ["SHA256_RAW_BYTE_HASH", "NEWLINE_COUNT"],
            "reported_sha256_prefix": "d1b57b2d",
            "reported_line_count": 2080,
        },
    ]
    incident = {
        "artifact_type": "phase6a3_resume_gold_access_integrity_incident",
        "artifact_version": "1.0",
        "status": "SCIENTIFIC_INTEGRITY_FAILURE",
        "recorded_at_utc": FINALIZED_AT_UTC,
        "run_id": RUN_ID,
        "incident_id": "INCIDENT_PRE_FREEZE_VALIDATION_BYTE_ACCESS_001",
        "summary": "A delegated path-mapping audit ran shasum and wc -l over five validation artifacts before the final pre-gold freeze/gate announcement.",
        "access_completed_before_pre_gold_freeze": True,
        "pre_gold_freeze_completed_at_utc": PRE_GOLD_FREEZE_COMPLETED_AT_UTC,
        "first_validation_gold_access_at_utc": None,
        "first_validation_gold_access_exact_timestamp_recorded": False,
        "known_temporal_bound": "ACCESS_COMPLETED_BEFORE_2026-08-16T01:14:00Z",
        "accessed_files": accessed_files,
        "semantic_records_printed_or_parsed": False,
        "record_ids_printed_or_parsed": False,
        "labels_or_required_evidence_printed_or_parsed": False,
        "questions_answers_or_expected_outputs_printed_or_parsed": False,
        "hashes_and_line_counts_only_exposed": True,
        "retriever_received_gold_fields": False,
        "retrieval_or_selection_changed_after_access": False,
        "validation_metrics_computed": False,
        "heldout_or_test_bytes_accessed": False,
        "containment_action": "STOP_EVALUATION_REVOKE_GATE_PRESERVE_ARTIFACTS",
        "waiver_applied": False,
    }
    EVALUATION.mkdir(parents=True, exist_ok=True)
    write_json(EVALUATION / "gold_access_integrity_incident.json", incident)

    not_run = {
        "artifact_type": "phase6a3_resume_evaluation_not_run",
        "artifact_version": "1.0",
        "status": "NOT_RUN_SCIENTIFIC_INTEGRITY_BLOCK",
        "created_at_utc": FINALIZED_AT_UTC,
        "run_id": RUN_ID,
        "reason": "Validation artifact bytes were accessed before the final pre-gold freeze, violating the mandatory gate chronology.",
        "retrieval_metrics_computed": False,
        "paired_comparisons_computed": False,
        "bootstrap_computed": False,
        "mcnemar_computed": False,
        "baseline_metrics_opened": False,
        "additional_validation_gold_access_after_incident": False,
        "heldout_gold_opened": False,
        "LLM_used": False,
        "API_calls_made": False,
    }
    write_json(EVALUATION / "evaluation_not_run.json", not_run)

    integrity = {
        "artifact_type": "phase6a3_resume_scientific_integrity",
        "artifact_version": "1.1",
        "status": "FAIL",
        "created_at_utc": FINALIZED_AT_UTC,
        "run_id": RUN_ID,
        "parent_candidate_artifacts_modified": False,
        "graph_modified": False,
        "grammar_modified": False,
        "evidence_selection_policy_modified": False,
        "max_path_depth_modified": False,
        "max_selected_records_modified": False,
        "tie_break_modified": False,
        "transition_class_modified": False,
        "new_relation_created": False,
        "new_node_type_created": False,
        "payment_bank_enabled": False,
        "bank_statement_relation_added": False,
        "gl_journal_added": False,
        "tier_b_enabled": False,
        "semantic_fallback_enabled": False,
        "embedding_created": False,
        "LLM_used": False,
        "API_call_made": False,
        "validation_gold_opened_before_final_pre_gold_freeze": True,
        "validation_gold_semantic_content_exposed": False,
        "validation_gold_visible_to_retriever": False,
        "retrieval_changed_after_gold": False,
        "selection_changed_after_gold": False,
        "ranking_changed_after_gold": False,
        "heldout_gold_opened": False,
        "heldout_labels_opened": False,
        "phase6b_started": False,
        "retrieval_metrics_computed": False,
        "RCA_accuracy_computed": False,
        "PRE_GOLD_RETRIEVAL_FROZEN": True,
        "PRE_GOLD_RETRIEVAL_FREEZE_STRUCTURALLY_VALID": True,
        "PRE_GOLD_MANIFEST_SHA256": PRE_GOLD_MANIFEST_SHA256,
        "PRE_GOLD_HASH_INVENTORY_SHA256": PRE_GOLD_HASH_INVENTORY_SHA256,
        "VALIDATION_GOLD_FIRST_OPENED_AFTER_FREEZE": False,
        "VALIDATION_GOLD_USED_ONLY_BY_OFFLINE_EVALUATOR": False,
        "HELDOUT_GOLD_OPENED": False,
        "RETRIEVAL_CONFIGURATION_CHANGED_AFTER_GOLD": False,
        "VALIDATION_GOLD_ACCESS_AUTHORIZED_FOR_OFFLINE_EVALUATOR": False,
        "previous_pre_gold_manifest_authorization_revoked": True,
        "failure_reason": "INCIDENT_PRE_FREEZE_VALIDATION_BYTE_ACCESS_001",
    }
    write_json(OUTPUT / "scientific_integrity_phase6a3_resume.json", integrity)

    pre_manifest = json.loads((RETRIEVAL / "final_pre_gold_manifest.json").read_text(encoding="utf-8"))
    manifest = {
        "artifact_type": "phase6a3_resume_run_manifest",
        "artifact_version": "1.1",
        "status": "BLOCKED_SCIENTIFIC_INTEGRITY_FAILURE",
        "run_id": RUN_ID,
        "created_at_utc": FINALIZED_AT_UTC,
        "parent_blocked_phase6a3_path": "results/graphrag/phase6a3_graph_v1_1_retrieval_v1_0",
        "parent_blocked_phase6a3_hash": "631398728da8eb5b3d1fdb959282affb1e61fa428c50be8054f867f93329ce46",
        "graph_v1_1_grammar_hash": pre_manifest["graph_v1_1_grammar_hash"],
        "evidence_selection_policy_hash": pre_manifest["evidence_selection_policy_hash"],
        "candidate_paths_hash": pre_manifest["candidate_paths_hash"],
        "candidate_records_hash": pre_manifest["candidate_records_hash"],
        "selected_paths_hash": pre_manifest["selected_paths_hash"],
        "selected_records_hash": pre_manifest["selected_records_hash"],
        "pre_gold_manifest_hash": PRE_GOLD_MANIFEST_SHA256,
        "pre_gold_hash_inventory_hash": PRE_GOLD_HASH_INVENTORY_SHA256,
        "pre_gold_freeze_completed_at_utc": PRE_GOLD_FREEZE_COMPLETED_AT_UTC,
        "validation_split_id": "PHASE5_AUTHORIZED_VALIDATION_ROUTING_SET_416",
        "validation_case_count": 416,
        "resolved_root_count": 430,
        "max_path_depth": 3,
        "max_selected_records": 40,
        "candidate_path_count": 13371,
        "candidate_depth_counts": {"1": 3332, "2": 4477, "3": 5562},
        "cases_over_40": 9,
        "validation_gold_first_access_timestamp": None,
        "validation_gold_first_access_exact_timestamp_recorded": False,
        "validation_gold_access_completed_before_freeze": True,
        "gold_evaluator_version_hash": None,
        "gold_evaluator_status": "NOT_RUN",
        "relational_rag_baseline_artifact_hash": None,
        "relational_rag_baseline_status": "NOT_OPENED_DUE_TO_BLOCK",
        "metric_definitions_version": None,
        "bootstrap_seed_method": None,
        "heldout_gold_opened": False,
        "LLM_used": False,
        "API_calls_made": False,
        "embeddings_created": False,
        "phase6b_started": False,
        "evaluation_authorization_revoked": True,
        "retrieval_metrics_computed": False,
        "final_recommendation": FINAL_RECOMMENDATION,
    }
    write_json(OUTPUT / "phase6a3_resume_run_manifest.json", manifest)

    report = f"""# Phase 6A.3 Graph v1.1 One-Shot Validation Review

## A. Executive finding

The retrieval bundle passed its structural pre-gold freeze, but the one-shot evaluation is blocked. A delegated mapping audit read raw bytes from five validation artifacts with `shasum` and `wc -l` before the final pre-gold gate timestamp. No semantic records or labels were exposed, but the prompt makes any pre-freeze validation-gold access a scientific-integrity failure. No metric was computed.

## B. Experimental preregistration lineage

The blocked candidate run, Graph v1.1 grammar freeze, and evidence-selection freeze all passed complete raw-byte lineage verification. The selector draft/final semantic diff remained zero.

## C. Graph v1.1 frozen grammar verification

PASS: grammar SHA-256 `2222def5dc3fd18628731949697087c6c96d7cdf1bb6c4cf2d16a1a58da6c8dc`; 30 transitions, 15 relation types, depth 3, and all prohibited traversal modes disabled. No grammar byte changed.

## D. Candidate traversal lineage verification

PASS: 416 cases, 430 roots, 13,371 candidate paths (3,332/4,477/5,562 by depth), and 8,369 candidate-record rows were copied byte-for-byte from the immutable parent.

## E. Frozen evidence-selection verification

PASS: final policy SHA-256 `cad5f2298d9dad62599cfe592304c08cf8808441586fb865d1f4824b3054ea1b`; 8,336 selected records; max 40; 430/430 roots retained; zero partial admissions; 33 Tier-5 drops; zero complete-backbone budget drops.

## F. Final pre-gold retrieval freeze

The structural bundle was written and independently verified. Manifest SHA-256: `{PRE_GOLD_MANIFEST_SHA256}`. Pre-gold inventory SHA-256: `{PRE_GOLD_HASH_INVENTORY_SHA256}`. It remains preserved as provenance, but its evaluator authorization is revoked by the subsequently discovered earlier access.

## G. Gold-isolation audit

FAIL. Before `2026-08-16T01:14:00Z`, a delegated mapping audit hashed and line-counted validation `case_ids`, `rca_ground_truth`, `case_entity_records`, `failure_manifest`, and `benchmark_questions`. Output exposed only hashes and line counts; no JSON/CSV rows, IDs, labels, evidence fields, questions, or answers were displayed or parsed. Held-out/test bytes were not read. The exact first-access timestamp was not recorded.

## H. Validation cohort

The intended cohort was the authorized 416-case validation split. Evaluation was not run.

## I. Relational-RAG baseline verification

Not opened after the incident; no baseline metric was copied or computed.

## J. Graph v1.1 candidate-pool metrics

Not computed due to the integrity block.

## K. Graph v1.1 selected Top-40 metrics

Not computed due to the integrity block.

## L. Candidate-vs-selected loss

Structural counts remain frozen (33 dropped records), but gold-dependent selection loss was not computed.

## M. Graph v1.1 vs Relational-RAG

Not computed.

## N. Paired case outcomes

Not computed.

## O. Full-evidence paired outcomes

Not computed.

## P. Statistical uncertainty

No bootstrap, confidence interval, or McNemar test was run.

## Q. Multi-hop evidence contribution

Not computed.

## R. Depth-2 incremental contribution

Not computed.

## S. Depth-3 incremental contribution

Not computed.

## T. Graph-only required evidence

Not computed.

## U. Relational-only required evidence

Not computed.

## V. Transition contribution

No gold-dependent transition contribution was computed.

## W. Path-sequence contribution

No gold-dependent path-sequence contribution was computed.

## X. Path-class contribution

No gold-dependent path-class contribution was computed.

## Y. Selector impact on 9 over-budget cases

Only the preregistered structural result is retained: nine cases were truncated and 33 Tier-5 context records were dropped. Required-gold impact was not computed.

## Z. Anchor-type results

Not computed.

## AA. Invoice cases

Not computed.

## AB. Payment cases

Not computed.

## AC. Bank-transaction cases

Not computed; no relation-gap conclusion was scored.

## AD. GL-journal-route cases

Not computed; no synthetic `GL_JOURNAL` was created.

## AE. Failure attribution

Retrieval failure attribution was not run. The run-level failure is `PRE_FREEZE_VALIDATION_BYTE_ACCESS`.

## AF. Relation gaps

Frozen relation gaps remain unchanged but were not evaluated against gold.

## AG. Record-budget efficiency

The structurally frozen selected-record distribution remains available in the selection freeze; no gold-dependent efficiency metric was computed here.

## AH. Token efficiency

Not computed.

## AI. Latency

Not computed for the resumed evaluation.

## AJ. Determinism

Pre-gold retrieval determinism passed. Evaluation determinism is not applicable because evaluation did not run.

## AK. Tests

The inherited selector suite passed 23/23 and the pre-gold cross-file gate passed. Evaluation tests were not run after the incident.

## AL. Scientific integrity

FAIL. `validation_gold_opened_before_final_pre_gold_freeze=true`; `VALIDATION_GOLD_FIRST_OPENED_AFTER_FREEZE=false`. Retrieval never received gold, no semantic content was exposed, no configuration changed, and held-out gold remained unopened, but the mandatory chronology was violated.

## AM. Known limitations

No retrieval conclusion can be drawn from this attempted one-shot run. The valid pre-gold retrieval files are preserved, but the run cannot satisfy the requested attestation.

## AN. Research interpretation

Scientific success was defined as uncontaminated execution, not as Graph winning. Because that condition failed before scoring, no comparative interpretation is permitted.

## AO. Phase 6B recommendation

Phase 6B is not authorized. A research owner must decide whether a separately governed future evaluation is scientifically permissible; this run cannot be repaired by silently redefining byte access.

{FINAL_RECOMMENDATION}
"""
    report_path = OUTPUT / "PHASE6A3_GRAPH_V1_1_ONE_SHOT_VALIDATION_REVIEW.md"
    report_path.write_text(report, encoding="utf-8", newline="\n")

    inventory_path = OUTPUT / "phase6a3_resume_artifact_hashes.json"
    artifacts = {}
    for path in sorted(OUTPUT.rglob("*")):
        if not path.is_file() or path == inventory_path or path.name.endswith(".pyc"):
            continue
        artifacts[path.relative_to(OUTPUT).as_posix()] = metadata(path)
    inventory = {
        "artifact_type": "phase6a3_resume_artifact_hash_inventory",
        "artifact_version": "1.1",
        "status": "BLOCKED_SCIENTIFIC_INTEGRITY_FAILURE",
        "created_at_utc": FINALIZED_AT_UTC,
        "hash_algorithm": "SHA-256",
        "hash_scope": "RAW_FILE_BYTES",
        "artifacts": artifacts,
        "self_hash_omitted": True,
        "self_hash_omission_reason": "A raw-byte self-hash is circular; report externally.",
        "pre_gold_manifest_sha256": PRE_GOLD_MANIFEST_SHA256,
        "pre_gold_hash_inventory_sha256": PRE_GOLD_HASH_INVENTORY_SHA256,
        "retrieval_metrics_computed": False,
        "heldout_gold_opened": False,
        "scientific_integrity_status": "FAIL",
    }
    write_json(inventory_path, inventory)
    for name, expected in artifacts.items():
        if metadata(OUTPUT / name) != expected:
            raise RuntimeError(f"final artifact changed during inventory: {name}")

    print(json.dumps({
        "status": "BLOCKED_SCIENTIFIC_INTEGRITY_FAILURE",
        "run_id": RUN_ID,
        "pre_gold_manifest_sha256": PRE_GOLD_MANIFEST_SHA256,
        "pre_gold_hash_inventory_sha256": PRE_GOLD_HASH_INVENTORY_SHA256,
        "resume_artifact_inventory_sha256": sha256_file(inventory_path),
        "report_sha256": sha256_file(report_path),
        "retrieval_metrics_computed": False,
        "heldout_gold_opened": False,
        "recommendation": FINAL_RECOMMENDATION,
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
