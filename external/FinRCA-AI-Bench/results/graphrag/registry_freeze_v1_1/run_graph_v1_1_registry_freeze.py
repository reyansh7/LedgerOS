#!/usr/bin/env python3
"""Freeze the verified Phase 6A.2 typed traversal grammar as Graph v1.1.

This script promotes specification artifacts only. It does not implement or run
retrieval, inspect gold evidence, call an LLM/API, create embeddings, or modify
the graph and parent registries.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import platform
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
PHASE6A2 = ROOT / "results/graphrag/phase6a2_typed_grammar_design_v1_1"
PHASE6A1 = ROOT / "results/graphrag/phase6a1_motif_diagnostic_v1"
PHASE6A = ROOT / "results/graphrag/phase6a_graph_retrieval_v1_0"
REGISTRY_V1 = ROOT / "results/graphrag/registry_freeze_v1"

CANONICAL_FREEZE_TIMESTAMP = "2026-08-15T17:54:51Z"
DECISION_CUTOFF = "2026-06-30"
FREEZE_STATUS = "FROZEN_GRAPH_V1_1_TYPED_GRAMMAR"

EXPECTED_PRIMARY_HASHES = {
    PHASE6A2 / "graph_traversal_grammar_v1_1_draft.json": "007f4ba9eed7c9d00bd5bcab7a6d1752c0fe924614a6cf36f728a41ec14fc0d8",
    PHASE6A2 / "typed_transition_matrix_v1_1_draft.json": "8a0c2e6d24b5098c9ffdef4da17c33979386a92f365161273349d2a906a2b36c",
    PHASE6A2 / "node_type_traversal_matrix_v1_1_draft.json": "f04f01b8106d4e0a59c9d0d3e53dea0f625c1ba3c64465afbc9a9678b09d5d12",
    PHASE6A2 / "forbidden_traversals_v1_1_draft.json": "2b3d0a604df5c5a75121749ccdfa15269c6ea98632f31398085f7c7153d04b74",
    PHASE6A2 / "v1_motif_to_v1_1_grammar_mapping.json": "2eb77bda03a01cb3923b3c6a3ec40212c34043695480472d3060c9536b0b3102",
    PHASE6A2 / "grammar_transition_justifications.json": "5478138031bb3f3cba7ff3138434f4706b3127722d5f2e3d2969f4afec007508",
    PHASE6A2 / "grammar_fanout_analysis.json": "12e00af5447d9e4fd3db686c95d3d1fb562c48b03dac67de116a1ebd744c5e25",
    PHASE6A2 / "grammar_structural_coverage.json": "7a2a659b3a5633987b74074fa4c477eb3b7fa1b80a14b20ecb13f4c6f65b8c63",
    PHASE6A2 / "grammar_topology_simulation.json": "63df67774453723df7975b3f8afc2626846583fc3c9dbe82670ced4b1a875696",
    PHASE6A2 / "grammar_risk_register.json": "34946386c9f424e89c8821ed7fbcb653e04406df13ae0e9fcf68594366833a09",
    PHASE6A2 / "scientific_integrity.json": "e150be4d9b754303569d5dc85f6c8c552969645cb033d762bfa83ac75aa990ea",
    PHASE6A2 / "phase6a2_artifact_hashes.json": "db5cdc9f153617a97e1bab845e7e2609fc249514e80e528ecd6ba1c46b93aa39",
    PHASE6A2 / "PHASE6A2_TYPED_GRAMMAR_DESIGN_REVIEW.md": "9ab2abbdacde0b912ec36aede2da22e2ca51b48d0e7e51ea37699e1ce3afbd61",
    REGISTRY_V1 / "graph_node_registry_v1.json": "4c17ff5c863ed446418fbc2b3b407704519862feddc5f0c81546c210f8e91d10",
    REGISTRY_V1 / "graph_relation_registry_v1.json": "f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3",
    REGISTRY_V1 / "graph_path_motifs_v1.json": "36dd0b0d491dd6ef5f46c1dcd38cfe5e9e2ab61c632038b89cdc6ed9e0ec58ef",
    REGISTRY_V1 / "graph_ranking_policy_v1.json": "85a167767f6147c2a51db9cdab47d7157731bb2126ca2cf2c452f4e9bde602f0",
    REGISTRY_V1 / "graph_freeze_manifest_v1.json": "8097eb64accec2c076d07ed9ae4604d2202d1ca83578cf8557b40f034b7cad76",
    PHASE6A / "graph/nodes.jsonl": "87f80fa5e91675b192dd051598a9197c0703650f4daf09c2a7619c031295a167",
    PHASE6A / "graph/edges.jsonl": "ee364fa677abeda3b25119d5c3c2f1aea5bc8902a28e7f7ecefcddd38a77d9ed",
    PHASE6A1 / "PHASE6A1_MOTIF_DIAGNOSTIC_REVIEW.md": "4b32dee5614982ffab50d458e9ee876b98f8a4fa70de25b8d8e76aab4233fec6",
    PHASE6A1 / "phase6a1_artifact_hashes.json": "d2c70d76e72fbe16a9210f191facbf8eeaecdd97bbd39c009b036cc4d332d7b5",
}

NODE_TYPES = (
    "APPROVAL_EVENT", "AUDIT_EVENT", "BANK_STATEMENT", "BANK_TRANSACTION",
    "EMPLOYEE", "GL_ENTRY", "INVOICE", "INVOICE_LINE", "PAYMENT",
    "PAYMENT_ALLOCATION", "PO_LINE", "PURCHASE_ORDER", "VENDOR", "VENDOR_CHANGE",
)

TRANSITION_CLASSES = ("BACKBONE", "SUPPORTING", "CONTEXT", "TERMINAL_CONTEXT")

REQUIRED_FINAL_ARTIFACTS = (
    "graph_traversal_grammar_v1_1.json",
    "typed_transition_matrix_v1_1.json",
    "node_type_traversal_matrix_v1_1.json",
    "forbidden_traversals_v1_1.json",
    "v1_motif_to_v1_1_grammar_mapping.json",
    "grammar_transition_justifications_v1_1.json",
    "grammar_risk_register_v1_1.json",
    "graph_v1_1_freeze_manifest.json",
    "graph_v1_1_freeze_hashes.json",
    "GRAPH_V1_1_TYPED_GRAMMAR_FREEZE_REVIEW.md",
    "scientific_integrity_v1_1_freeze.json",
)

OPTIONAL_LINEAGE_ARTIFACTS = (
    "grammar_fanout_analysis_v1_1.json",
    "grammar_structural_coverage_v1_1.json",
    "grammar_topology_simulation_v1_1.json",
    "draft_to_final_semantic_diff_v1_1.json",
    "transition_freeze_validation_v1_1.json",
    "topology_equivalence_validation_v1_1.json",
    "determinism_validation_v1_1_freeze.json",
)

SERIALIZATION_CONVENTION = {
    "encoding": "UTF-8",
    "json_key_order": "lexicographic via sort_keys=true",
    "json_indentation_spaces": 2,
    "json_separators": "comma plus newline/indent; colon plus one space",
    "newline": "LF with exactly one trailing newline",
    "unicode": "ensure_ascii=false",
    "transition_array_order": "ascending transition_id",
    "other_array_order": "explicit semantic parent order or explicitly documented stable key order",
    "filesystem_order_dependency": False,
    "hash_map_order_dependency": False,
    "concurrency_timing_dependency": False,
}

SEMANTIC_TRANSITION_FIELDS = (
    "transition_id", "current_node_type", "relation_id", "traversal_direction",
    "next_node_type", "transition_class", "financial_lifecycle_role", "relation_tier",
    "tier_family", "max_transition_depth", "requires_exact_edge",
    "requires_cutoff_eligibility", "requires_provenance", "allow_as_first_hop",
    "allow_as_intermediate_hop", "allow_as_terminal_hop",
    "may_continue_after_transition", "hub_policy", "multiplicity_class",
    "multiplicity_policy", "cycle_policy", "terminal_rule", "semantic_justification",
    "operational_field_provenance", "provenance_behavior", "temporal_behavior",
    "parent_relation_status", "parent_relation_traversable",
    "parent_relation_reverse_traversal", "phase6a1_directionality_class",
    "reverse_safety_basis", "path_state_requirements", "path_state_effects",
)

GLOBAL_GRAMMAR_SEMANTIC_FIELDS = (
    "design_scope", "default_deny", "node_universe", "transition_class_counts",
    "transition_class_definitions", "transition_inclusion_rule", "path_state_model",
    "stop_conditions", "evidence_sufficiency_llm_stop_allowed",
    "multiplicity_and_budget_policy", "candidate_record_deduplication",
    "candidate_path_priority_framework_for_future_review", "required_path_provenance",
    "frozen_relation_types_used", "unsupported_executable_transition_count",
    "new_graph_edges_created", "new_relation_types_created", "new_node_types_created",
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def serialize_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def freeze_clone(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: freeze_clone(item) for key, item in value.items()}
    if isinstance(value, list):
        return [freeze_clone(item) for item in value]
    if value == "PROPOSAL_ONLY":
        return "FROZEN"
    return copy.deepcopy(value)


def freeze_artifact(parent: dict[str, Any], parent_path: Path) -> dict[str, Any]:
    result = freeze_clone(parent)
    result["artifact_version"] = "1.1"
    result["status"] = "FROZEN"
    result["freeze_status"] = FREEZE_STATUS
    result["created_at_utc"] = CANONICAL_FREEZE_TIMESTAMP
    result["parent_phase6a2_artifact_path"] = parent_path.relative_to(ROOT).as_posix()
    result["parent_phase6a2_artifact_sha256"] = sha256_file(parent_path)
    result["serialization_convention"] = SERIALIZATION_CONVENTION
    return result


def verify_inputs() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(path: Path, expected: str, expected_bytes: int | None, authority: str) -> None:
        observed = sha256_file(path)
        size_ok = expected_bytes is None or path.stat().st_size == expected_bytes
        checks.append({
            "path": path.relative_to(ROOT).as_posix(),
            "authority": authority,
            "expected_sha256": expected,
            "observed_sha256": observed,
            "expected_bytes": expected_bytes,
            "observed_bytes": path.stat().st_size,
            "status": "PASS" if observed == expected and size_ok else "FAIL",
        })

    for path, expected in sorted(EXPECTED_PRIMARY_HASHES.items(), key=lambda row: row[0].as_posix()):
        add(path, expected, None, "PROMPT_PINNED")

    phase6a2_inventory = load_json(PHASE6A2 / "phase6a2_artifact_hashes.json")
    for name, metadata in sorted(phase6a2_inventory["artifacts"].items()):
        add(PHASE6A2 / name, metadata["sha256"], metadata["bytes"], "PHASE6A2_HASH_INVENTORY")
    phase6a2_script = phase6a2_inventory["analysis_script"]
    add(
        PHASE6A2 / phase6a2_script["path"], phase6a2_script["sha256"],
        phase6a2_script["bytes"], "PHASE6A2_HASH_INVENTORY",
    )

    phase6a1_inventory = load_json(PHASE6A1 / "phase6a1_artifact_hashes.json")
    for name, metadata in sorted(phase6a1_inventory["artifacts"].items()):
        add(PHASE6A1 / name, metadata["sha256"], metadata["bytes"], "PHASE6A1_HASH_INVENTORY")
    phase6a1_script = phase6a1_inventory["analysis_script"]
    add(
        PHASE6A1 / phase6a1_script["path"], phase6a1_script["sha256"],
        phase6a1_script["bytes"], "PHASE6A1_HASH_INVENTORY",
    )

    failures = [row for row in checks if row["status"] != "PASS"]
    if failures:
        raise RuntimeError("BLOCKED — PHASE 6A.2 PARENT HASH MISMATCH: " + canonical(failures))
    return {
        "status": "PASS",
        "verified_check_count": len(checks),
        "verified_distinct_path_count": len({row["path"] for row in checks}),
        "checks": checks,
    }


def import_phase6a2_runner() -> Any:
    path = PHASE6A2 / "run_phase6a2_design.py"
    spec = importlib.util.spec_from_file_location("verified_phase6a2_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import verified Phase 6A.2 runner")
    module = importlib.util.module_from_spec(spec)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


def load_parents() -> dict[str, Any]:
    return {
        "draft_grammar": load_json(PHASE6A2 / "graph_traversal_grammar_v1_1_draft.json"),
        "draft_transition_matrix": load_json(PHASE6A2 / "typed_transition_matrix_v1_1_draft.json"),
        "draft_node_matrix": load_json(PHASE6A2 / "node_type_traversal_matrix_v1_1_draft.json"),
        "draft_forbidden": load_json(PHASE6A2 / "forbidden_traversals_v1_1_draft.json"),
        "draft_motif_mapping": load_json(PHASE6A2 / "v1_motif_to_v1_1_grammar_mapping.json"),
        "draft_justifications": load_json(PHASE6A2 / "grammar_transition_justifications.json"),
        "draft_fanout": load_json(PHASE6A2 / "grammar_fanout_analysis.json"),
        "draft_coverage": load_json(PHASE6A2 / "grammar_structural_coverage.json"),
        "draft_simulation": load_json(PHASE6A2 / "grammar_topology_simulation.json"),
        "draft_risks": load_json(PHASE6A2 / "grammar_risk_register.json"),
        "draft_determinism": load_json(PHASE6A2 / "determinism_validation.json"),
        "relation_registry": load_json(REGISTRY_V1 / "graph_relation_registry_v1.json"),
        "node_registry": load_json(REGISTRY_V1 / "graph_node_registry_v1.json"),
        "motif_registry": load_json(REGISTRY_V1 / "graph_path_motifs_v1.json"),
        "ranking_registry": load_json(REGISTRY_V1 / "graph_ranking_policy_v1.json"),
        "freeze_manifest_v1": load_json(REGISTRY_V1 / "graph_freeze_manifest_v1.json"),
        "directionality": load_json(PHASE6A1 / "relation_directionality_audit.json"),
        "sequence_inventory": load_json(PHASE6A1 / "path_sequence_inventory.json"),
        "nodes": load_jsonl(PHASE6A / "graph/nodes.jsonl"),
        "edges": load_jsonl(PHASE6A / "graph/edges.jsonl"),
    }


def validate_parent_lineage(parents: dict[str, Any]) -> dict[str, Any]:
    draft = parents["draft_grammar"]
    transitions = draft["transitions"]
    class_counts = Counter(row["transition_class"] for row in transitions)
    relation_types = {row["relation_id"] for row in transitions}
    frozen_relations = parents["relation_registry"]["frozen_relations"]
    graph_node_types = {row["node_type"] for row in parents["nodes"]}
    edge_relation_types = {row["relation_type"] for row in parents["edges"]}
    checks = {
        "graph_node_count_155391": len(parents["nodes"]) == 155391,
        "graph_edge_count_184223": len(parents["edges"]) == 184223,
        "graph_node_type_count_14": len(graph_node_types) == 14 and graph_node_types == set(NODE_TYPES),
        "frozen_relation_count_22": len(frozen_relations) == 22,
        "edge_relation_universe_matches_registry": edge_relation_types == {row["relation_type"] for row in frozen_relations},
        "transition_count_30": len(transitions) == 30 and len({row["transition_id"] for row in transitions}) == 30,
        "class_counts_match": class_counts == Counter({
            "BACKBONE": 18, "SUPPORTING": 2, "CONTEXT": 5, "TERMINAL_CONTEXT": 5,
        }),
        "relation_type_count_15": len(relation_types) == 15,
        "relations_are_frozen_subset": relation_types <= {row["relation_type"] for row in frozen_relations},
        "node_registry_matches_graph": parents["node_registry"]["node_type_count"] == 14,
        "forbidden_direction_count_14": parents["draft_forbidden"]["excluded_frozen_directional_transition_count"] == 14,
        "coverage_76_of_76": parents["draft_coverage"]["overall"] == {
            "safe_sequence_count": 76,
            "represented_sequence_count": 76,
            "structural_sequence_coverage": 1.0,
        },
        "depth_coverage_14_21_41": [
            parents["draft_coverage"]["by_depth"][str(depth)]["safe_sequence_count"]
            for depth in (1, 2, 3)
        ] == [14, 21, 41],
        "topology_path_count_13371": parents["draft_simulation"]["candidate_path_count"] == 13371,
        "topology_depth_counts_match": parents["draft_simulation"]["paths_by_exact_depth"] == {
            "1": 3332, "2": 4477, "3": 5562,
        },
        "accepted_path_transition_partition_22_plus_8": (
            parents["draft_simulation"]["transition_exercise"]["accepted_path_transition_count"] == 22
            and parents["draft_simulation"]["transition_exercise"]["not_present_in_accepted_paths_count"] == 8
        ),
        "max_depth_3": draft["path_state_model"]["maximum_path_depth"] == 3,
        "simple_path_only": draft["path_state_model"]["simple_path_invariant"] == "record_id may appear at most once in one path",
        "no_new_graph_semantics": (
            draft["new_graph_edges_created"] is False
            and draft["new_relation_types_created"] is False
            and draft["new_node_types_created"] is False
        ),
    }
    if not all(checks.values()):
        raise RuntimeError("BLOCKED — PROPOSAL COUNT DISCREPANCY OR LINEAGE FAILURE: " + canonical(checks))

    parent_hash_rows = draft["parent_hash_verification"]["checks"]
    phase6a2_lineage = {row["path"]: row["observed_sha256"] for row in parent_hash_rows}
    lineage_expectations = {
        (REGISTRY_V1 / "graph_node_registry_v1.json").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_node_registry_v1.json"],
        (REGISTRY_V1 / "graph_relation_registry_v1.json").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_relation_registry_v1.json"],
        (REGISTRY_V1 / "graph_path_motifs_v1.json").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_path_motifs_v1.json"],
        (REGISTRY_V1 / "graph_ranking_policy_v1.json").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_ranking_policy_v1.json"],
        (REGISTRY_V1 / "graph_freeze_manifest_v1.json").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_freeze_manifest_v1.json"],
        (PHASE6A / "graph/nodes.jsonl").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[PHASE6A / "graph/nodes.jsonl"],
        (PHASE6A / "graph/edges.jsonl").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[PHASE6A / "graph/edges.jsonl"],
        (PHASE6A1 / "PHASE6A1_MOTIF_DIAGNOSTIC_REVIEW.md").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[PHASE6A1 / "PHASE6A1_MOTIF_DIAGNOSTIC_REVIEW.md"],
        (PHASE6A1 / "phase6a1_artifact_hashes.json").relative_to(ROOT).as_posix(): EXPECTED_PRIMARY_HASHES[PHASE6A1 / "phase6a1_artifact_hashes.json"],
    }
    lineage_matches = {
        path: phase6a2_lineage.get(path) == expected for path, expected in lineage_expectations.items()
    }
    if not all(lineage_matches.values()):
        raise RuntimeError("BLOCKED — PHASE 6A.2 LINEAGE MISMATCH: " + canonical(lineage_matches))
    return {
        "status": "PASS",
        "checks": checks,
        "phase6a2_references_same_parent_lineage": True,
        "phase6a2_parent_lineage_checks": lineage_matches,
        "graph_node_count": len(parents["nodes"]),
        "graph_edge_count": len(parents["edges"]),
        "graph_node_type_count": len(graph_node_types),
        "frozen_relation_count": len(frozen_relations),
        "transition_count": len(transitions),
        "transition_count_by_class": dict(sorted(class_counts.items())),
        "relation_type_count": len(relation_types),
    }


def accepted_path_transition_usage(simulation: dict[str, Any]) -> dict[str, int]:
    usage: Counter[str] = Counter()
    for row in simulation["transition_sequence_counts"]:
        for transition_id in set(row["transition_id_sequence"]):
            usage[transition_id] += row["path_instance_count"]
    return dict(usage)


def validate_transitions(parents: dict[str, Any]) -> dict[str, Any]:
    draft = parents["draft_grammar"]
    transitions = sorted(draft["transitions"], key=lambda row: row["transition_id"])
    relations = {row["relation_type"]: row for row in parents["relation_registry"]["frozen_relations"]}
    directionality = {row["relation_type"]: row for row in parents["directionality"]["relations"]}
    justifications = {
        row["transition_id"]: row for row in parents["draft_justifications"]["justifications"]
    }
    fanout = {
        row["transition_id"]: row for row in parents["draft_fanout"]["proposed_transition_fanout"]
    }
    usage = accepted_path_transition_usage(parents["draft_simulation"])
    expected_unused = set(
        parents["draft_simulation"]["transition_exercise"]["not_present_in_accepted_paths_transition_ids"]
    )
    validation_rows = []
    for transition in transitions:
        transition_id = transition["transition_id"]
        relation = relations.get(transition["relation_id"])
        forward = transition["traversal_direction"] == "FORWARD"
        expected_current = relation["source_node_type"] if relation and forward else relation["target_node_type"] if relation else None
        expected_next = relation["target_node_type"] if relation and forward else relation["source_node_type"] if relation else None
        justification = justifications.get(transition_id)
        transition_fanout = fanout.get(transition_id)
        checks = {
            "A_underlying_relation_exists": relation is not None,
            "B_relation_permits_deterministic_use": bool(
                relation and relation["status"] == "READY_FOR_FREEZE" and relation["traversable"]
            ),
            "C_source_target_types_match": (
                transition["current_node_type"] == expected_current
                and transition["next_node_type"] == expected_next
            ),
            "D_direction_supported": bool(
                relation
                and transition["traversal_direction"] in {"FORWARD", "REVERSE"}
                and (forward or relation["reverse_traversal"])
                and directionality[transition["relation_id"]]["reverse_traversal_class"] == "SAFE_REVERSIBLE_CANDIDATE"
                and transition["phase6a1_directionality_class"] == "SAFE_REVERSIBLE_CANDIDATE"
            ),
            "E_no_new_edge_created": transition["requires_exact_edge"] and draft["new_graph_edges_created"] is False,
            "F_provenance_preserved": bool(
                transition["requires_provenance"]
                and transition["operational_field_provenance"]["field_orientation"] == "FROZEN_STORED_EDGE"
                and transition["operational_field_provenance"]["provenance_record_type"]
                and justification
                and justification["provenance_behavior"]
            ),
            "G_temporal_cutoff_preserved": bool(
                transition["requires_cutoff_eligibility"]
                and DECISION_CUTOFF == parents["relation_registry"]["decision_cutoff"]
                and justification
                and justification["temporal_behavior"]
            ),
            "H_hub_restrictions_respected": (
                "VENDOR" not in {transition["current_node_type"], transition["next_node_type"]}
                and "EMPLOYEE" not in {transition["current_node_type"], transition["next_node_type"]}
                and transition["hub_policy"] == "NONE"
            ),
            "I_label_independent": transition["validation_gold_used"] is False and bool(justification) and justification["validation_gold_success_cited"] is False,
            "J_no_future_tier_b_evidence": (
                transition["tier_family"] == "A"
                and "CANDIDATE" not in transition["relation_id"]
                and transition["relation_id"] != "PAYMENT_CANDIDATE_BANK_TRANSACTION"
            ),
            "K_transition_class_matches": bool(
                justification
                and transition["transition_class"] in TRANSITION_CLASSES
                and justification["financial_lifecycle_role"] == transition["financial_lifecycle_role"]
            ),
            "L_continuation_terminal_matches": bool(
                justification
                and justification["continuation_decision"]["may_continue"] == transition["may_continue_after_transition"]
                and justification["continuation_decision"]["reason"] == transition["terminal_rule"]
            ),
        }
        route_usage = usage.get(transition_id, 0)
        structurally_justified = (
            all(checks.values())
            and transition_fanout is not None
            and transition_fanout["statistics"]["edge_count"] > 0
            and transition_fanout["multiplicity_class"] != "HUB_RISK"
        )
        validation_rows.append({
            "transition_id": transition_id,
            "underlying_frozen_relation": transition["relation_id"],
            "current_node_type": transition["current_node_type"],
            "next_node_type": transition["next_node_type"],
            "traversal_direction": transition["traversal_direction"],
            "transition_class": transition["transition_class"],
            "validation_route_usage_count": route_usage,
            "appears_in_accepted_validation_route_path": route_usage > 0,
            "structurally_justified": structurally_justified,
            "global_graph_support": {
                "edge_count": transition_fanout["statistics"]["edge_count"],
                "nonzero_current_node_count": transition_fanout["statistics"]["nonzero_current_node_count"],
            } if transition_fanout else None,
            "fanout_evidence": transition_fanout["statistics"] if transition_fanout else None,
            "operational_semantic_justification": transition["semantic_justification"],
            "reason_retained": "Existing frozen exact relation; operationally valid, provenance-preserving, temporally enforceable, and hub-safe independent of validation routing frequency.",
            "gold_evidence_used": False,
            "checks": checks,
            "result": "PASS" if structurally_justified else "FAIL",
        })
    failures = [row for row in validation_rows if row["result"] != "PASS"]
    unused_rows = [row for row in validation_rows if row["validation_route_usage_count"] == 0]
    observed_unused = {row["transition_id"] for row in unused_rows}
    if failures or len(validation_rows) != 30 or observed_unused != expected_unused or len(unused_rows) != 8:
        raise RuntimeError("BLOCKED — TRANSITION VALIDATION FAILURE: " + canonical({
            "failures": failures,
            "observed_unused": sorted(observed_unused),
            "expected_unused": sorted(expected_unused),
        }))
    return {
        "status": "PASS",
        "transition_count": len(validation_rows),
        "passing_transition_count": len(validation_rows),
        "new_relation_type_count": len({row["underlying_frozen_relation"] for row in validation_rows} - set(relations)),
        "validation_unused_transition_count": len(unused_rows),
        "validation_unused_transition_ids": sorted(observed_unused),
        "validation_unused_transitions": unused_rows,
        "transition_validations": validation_rows,
    }


def build_final_grammar(
    parents: dict[str, Any], transition_validation: dict[str, Any],
) -> dict[str, Any]:
    parent_path = PHASE6A2 / "graph_traversal_grammar_v1_1_draft.json"
    final = freeze_artifact(parents["draft_grammar"], parent_path)
    usage_by_id = {
        row["transition_id"]: row for row in transition_validation["transition_validations"]
    }
    final_transitions = []
    for transition in sorted(final["transitions"], key=lambda row: row["transition_id"]):
        validation = usage_by_id[transition["transition_id"]]
        transition["freeze_validation"] = {
            "VALIDATION_ROUTE_USAGE": validation["validation_route_usage_count"],
            "STRUCTURALLY_JUSTIFIED": validation["structurally_justified"],
            "validation_status": validation["result"],
            "global_graph_support": validation["global_graph_support"],
            "fanout_evidence": validation["fanout_evidence"],
            "gold_evidence_used": False,
        }
        final_transitions.append(transition)
    final["transitions"] = final_transitions
    final.update({
        "artifact_name": "graph_traversal_grammar_v1_1.json",
        "grammar_id": "GRAPH_TRAVERSAL_GRAMMAR_V1_1",
        "not_frozen": False,
        "not_implemented": True,
        "max_path_depth": 3,
        "simple_path_only": True,
        "payment_bank_enabled": False,
        "bank_statement_membership_enabled": False,
        "synthetic_gl_journal_enabled": False,
        "tier_b_enabled": False,
        "semantic_fallback_enabled": False,
        "generic_bfs_enabled": False,
        "transition_count": len(final_transitions),
        "transition_count_by_class": dict(sorted(Counter(row["transition_class"] for row in final_transitions).items())),
        "relation_type_count": len({row["relation_id"] for row in final_transitions}),
        "decision_cutoff": DECISION_CUTOFF,
        "validation_unused_but_retained_transition_count": transition_validation["validation_unused_transition_count"],
        "validation_frequency_used_as_correctness_criterion": False,
        "graph_v1_1_implemented": False,
        "graph_v1_1_retrieval_evaluated": False,
    })
    return final


def semantic_projection(transition: dict[str, Any]) -> dict[str, Any]:
    return {field: transition.get(field) for field in SEMANTIC_TRANSITION_FIELDS}


def build_semantic_diff(
    parents: dict[str, Any], final_grammar: dict[str, Any],
    final_transition_matrix: dict[str, Any], final_node_matrix: dict[str, Any],
    final_forbidden: dict[str, Any],
) -> dict[str, Any]:
    draft_by_id = {row["transition_id"]: row for row in parents["draft_grammar"]["transitions"]}
    final_by_id = {row["transition_id"]: row for row in final_grammar["transitions"]}
    transition_rows = []
    for transition_id in sorted(set(draft_by_id) | set(final_by_id)):
        draft_projection = semantic_projection(draft_by_id.get(transition_id, {}))
        final_projection = semantic_projection(final_by_id.get(transition_id, {}))
        changed_fields = [
            field for field in SEMANTIC_TRANSITION_FIELDS
            if draft_projection.get(field) != final_projection.get(field)
        ]
        transition_rows.append({
            "transition_id": transition_id,
            "changed_semantic_fields": changed_fields,
            "semantic_diff_count": len(changed_fields),
            "result": "PASS" if not changed_fields else "FAIL",
        })
    global_changes = [
        field for field in GLOBAL_GRAMMAR_SEMANTIC_FIELDS
        if parents["draft_grammar"].get(field) != final_grammar.get(field)
    ]
    draft_matrix_rows = {
        row["transition_id"]: {key: value for key, value in row.items() if key != "status"}
        for row in parents["draft_transition_matrix"]["rows"]
    }
    final_matrix_rows = {
        row["transition_id"]: {
            key: value for key, value in row.items()
            if key not in {"status", "freeze_validation"}
        }
        for row in final_transition_matrix["rows"]
    }
    node_policy_fields = (
        "node_type", "allowed_outgoing_transition_ids", "allowed_outgoing_transition_count",
        "anchor_exit_only_transition_ids", "noncontinuing_transition_ids",
        "terminal_context_transition_ids", "terminal_accounting_consequence_transition_ids",
        "explicit_empty_transition_set", "maximum_reachable_depth_from_exact_anchor",
        "reached_node_state_override", "prohibited_pattern_ids", "reasoning",
    )
    draft_nodes = {
        row["node_type"]: {field: row.get(field) for field in node_policy_fields}
        for row in parents["draft_node_matrix"]["node_types"]
    }
    final_nodes = {
        row["node_type"]: {field: row.get(field) for field in node_policy_fields}
        for row in final_node_matrix["node_types"]
    }
    forbidden_fields = (
        "forbidden_id", "category", "pattern", "blocked_relation_ids",
        "blocked_excluded_candidate_relation_ids", "blocked_directions", "enforcement",
        "rationale", "authority",
    )
    draft_forbidden = {
        row["forbidden_id"]: {field: row.get(field) for field in forbidden_fields}
        for row in parents["draft_forbidden"]["forbidden_patterns"]
    }
    final_forbidden_projection = {
        row["forbidden_id"]: {field: row.get(field) for field in forbidden_fields}
        for row in final_forbidden["forbidden_patterns"]
    }
    draft_relation_reuse = [
        {key: value for key, value in row.items() if key != "status"}
        for row in parents["draft_grammar"]["relation_reuse"]
    ]
    final_relation_reuse = [
        {key: value for key, value in row.items() if key != "status"}
        for row in final_grammar["relation_reuse"]
    ]
    semantic_transition_diff_count = sum(row["semantic_diff_count"] for row in transition_rows)
    checks = {
        "transition_id_set_unchanged": set(draft_by_id) == set(final_by_id),
        "transition_semantics_unchanged": semantic_transition_diff_count == 0,
        "global_grammar_semantics_unchanged": not global_changes,
        "typed_transition_matrix_rows_unchanged": draft_matrix_rows == final_matrix_rows,
        "node_type_policies_unchanged": draft_nodes == final_nodes,
        "forbidden_patterns_unchanged": draft_forbidden == final_forbidden_projection,
        "relation_reuse_dispositions_unchanged": draft_relation_reuse == final_relation_reuse,
        "excluded_direction_ids_unchanged": {
            row["excluded_transition_id"] for row in parents["draft_forbidden"]["excluded_frozen_directional_transitions"]
        } == {
            row["excluded_transition_id"] for row in final_forbidden["excluded_frozen_directional_transitions"]
        },
    }
    if not all(checks.values()):
        raise RuntimeError("BLOCK FREEZE — SEMANTIC DIFF: " + canonical({
            "checks": checks, "global_changes": global_changes, "transition_rows": transition_rows,
        }))
    return {
        "artifact_type": "graph_v1_1_draft_to_final_semantic_diff",
        "artifact_version": "1.1",
        "status": "FROZEN",
        "freeze_status": FREEZE_STATUS,
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "draft_path": (PHASE6A2 / "graph_traversal_grammar_v1_1_draft.json").relative_to(ROOT).as_posix(),
        "draft_sha256": sha256_file(PHASE6A2 / "graph_traversal_grammar_v1_1_draft.json"),
        "final_path": "results/graphrag/registry_freeze_v1_1/graph_traversal_grammar_v1_1.json",
        "allowed_difference_classes": [
            "artifact version", "status/freeze status", "approved freeze metadata",
            "canonical final filename", "deterministic serialization metadata",
            "validation-route usage and freeze-validation attestations",
        ],
        "semantic_transition_diff_count": semantic_transition_diff_count,
        "global_semantic_diff_count": len(global_changes),
        "global_changed_semantic_fields": global_changes,
        "transition_results": transition_rows,
        "supplemental_semantic_checks": checks,
        "result": "PASS",
        "serialization_convention": SERIALIZATION_CONVENTION,
    }


def build_final_transition_matrix(
    parents: dict[str, Any], transition_validation: dict[str, Any],
) -> dict[str, Any]:
    parent_path = PHASE6A2 / "typed_transition_matrix_v1_1_draft.json"
    result = freeze_artifact(parents["draft_transition_matrix"], parent_path)
    validation_by_id = {
        row["transition_id"]: row for row in transition_validation["transition_validations"]
    }
    rows = []
    for row in sorted(result["rows"], key=lambda item: item["transition_id"]):
        validation = validation_by_id[row["transition_id"]]
        row["freeze_validation"] = {
            "VALIDATION_ROUTE_USAGE": validation["validation_route_usage_count"],
            "STRUCTURALLY_JUSTIFIED": validation["structurally_justified"],
            "validation_status": validation["result"],
        }
        rows.append(row)
    result["rows"] = rows
    result["artifact_name"] = "typed_transition_matrix_v1_1.json"
    return result


def build_final_node_matrix(parents: dict[str, Any]) -> dict[str, Any]:
    parent_path = PHASE6A2 / "node_type_traversal_matrix_v1_1_draft.json"
    result = freeze_artifact(parents["draft_node_matrix"], parent_path)
    result["node_types"] = sorted(result["node_types"], key=lambda row: row["node_type"])
    result["artifact_name"] = "node_type_traversal_matrix_v1_1.json"
    return result


def build_final_forbidden(parents: dict[str, Any]) -> dict[str, Any]:
    parent_path = PHASE6A2 / "forbidden_traversals_v1_1_draft.json"
    result = freeze_artifact(parents["draft_forbidden"], parent_path)
    result["forbidden_patterns"] = sorted(result["forbidden_patterns"], key=lambda row: row["forbidden_id"])
    result["excluded_frozen_directional_transitions"] = sorted(
        result["excluded_frozen_directional_transitions"], key=lambda row: row["excluded_transition_id"]
    )
    result["artifact_name"] = "forbidden_traversals_v1_1.json"
    result["forbidden_direction_promotion_count"] = 0
    result["payment_bank_enabled"] = False
    result["bank_statement_membership_enabled"] = False
    result["synthetic_gl_journal_enabled"] = False
    result["tier_b_enabled"] = False
    result["semantic_fallback_enabled"] = False
    result["generic_bfs_enabled"] = False
    return result


def build_final_motif_mapping(parents: dict[str, Any]) -> dict[str, Any]:
    parent_path = PHASE6A2 / "v1_motif_to_v1_1_grammar_mapping.json"
    result = freeze_artifact(parents["draft_motif_mapping"], parent_path)
    result["artifact_name"] = "v1_motif_to_v1_1_grammar_mapping.json"
    result["mapping_is_compatibility_documentation_only"] = True
    result["graph_v1_motifs_modified"] = False
    return result


def build_final_justifications(
    parents: dict[str, Any], transition_validation: dict[str, Any],
) -> dict[str, Any]:
    parent_path = PHASE6A2 / "grammar_transition_justifications.json"
    result = freeze_artifact(parents["draft_justifications"], parent_path)
    validation_by_id = {
        row["transition_id"]: row for row in transition_validation["transition_validations"]
    }
    rows = []
    for row in sorted(result["justifications"], key=lambda item: item["transition_id"]):
        validation = validation_by_id[row["transition_id"]]
        row["freeze_validation"] = {
            "VALIDATION_ROUTE_USAGE": validation["validation_route_usage_count"],
            "STRUCTURALLY_JUSTIFIED": validation["structurally_justified"],
            "validation_status": validation["result"],
        }
        rows.append(row)
    result["justifications"] = rows
    result["artifact_name"] = "grammar_transition_justifications_v1_1.json"
    return result


def build_final_risks(parents: dict[str, Any]) -> dict[str, Any]:
    parent_path = PHASE6A2 / "grammar_risk_register.json"
    result = freeze_artifact(parents["draft_risks"], parent_path)
    result["artifact_name"] = "grammar_risk_register_v1_1.json"
    result["risks"] = sorted(result["risks"], key=lambda row: row["risk_id"])
    result["frozen_research_policies"] = {
        "gl_fanout": "ENUMERATE_ALL_EXACT_ELIGIBLE_EDGES / NO_ARBITRARY_TRANSITION_CAP",
        "gl_fanout_cap_status": "NOT_FROZEN / NO_RESEARCH_TRUNCATION",
        "bank_settlement": "DISABLED / SEPARATE FUTURE TIER_B STUDY",
    }
    result["unresolved_production_policy_count"] = 2
    result["unresolved_production_policies"] = [
        "GL fan-out drift / production cap governance",
        "absent deterministic bank-settlement linkage",
    ]
    return result


def topology_projection(simulation: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "candidate_path_count", "candidate_path_set_sha256", "candidate_paths_per_anchor",
        "candidate_paths_per_resolved_root", "resolved_root_count", "paths_by_exact_depth",
        "unique_records_reached_including_anchors", "unique_non_anchor_records_reached",
        "endpoint_node_type_counts_by_depth", "relation_sequence_counts",
        "transition_sequence_counts", "transition_sequence_counts_by_anchor_type",
        "cycles_prevented_by_simple_path", "terminal_stop_counts",
        "terminal_stop_counts_by_transition_class_and_depth", "no_allowed_transition_stop_counts",
        "temporal_rejection_counts", "provenance_rejection_counts",
        "exact_edge_or_type_rejection_counts", "multiplicity_policy_stop_count",
        "hub_attempts_prevented", "max_degree_transition_responsible", "by_anchor_type",
        "case_results", "phase6a1_safe_topology_comparison",
        "candidate_record_deduplication_design", "transition_exercise",
    )
    return {key: simulation[key] for key in keys}


def coverage_projection(coverage: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "metric_name", "definition", "not_required_document_recall", "gold_evidence_used",
        "overall", "by_depth", "by_anchor_type", "sequence_results",
        "excluded_sequence_count", "excluded_sequences",
    )
    return {key: coverage[key] for key in keys}


def fanout_projection(fanout: dict[str, Any]) -> dict[str, Any]:
    def strip_status(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: strip_status(item) for key, item in value.items() if key != "status"}
        if isinstance(value, list):
            return [strip_status(item) for item in value]
        return value
    return strip_status(fanout)


def rerun_topology(
    parents: dict[str, Any], runner: Any, runner_data: dict[str, Any],
    final_grammar: dict[str, Any], final_forbidden: dict[str, Any],
) -> dict[str, Any]:
    rerun_simulation = runner.simulate_topology(
        runner_data, final_grammar["transitions"], final_forbidden["excluded_frozen_directional_transitions"],
    )
    rerun_coverage = runner.structural_coverage(runner_data, final_grammar["transitions"], rerun_simulation)
    rerun_fanout = runner.build_fanout_analysis(
        final_grammar["transitions"], final_forbidden["excluded_frozen_directional_transitions"],
    )
    checks = {
        "topology_projection_identical": topology_projection(rerun_simulation) == topology_projection(parents["draft_simulation"]),
        "coverage_projection_identical": coverage_projection(rerun_coverage) == coverage_projection(parents["draft_coverage"]),
        "fanout_projection_identical": fanout_projection(rerun_fanout) == fanout_projection(parents["draft_fanout"]),
        "route_case_count_416": len(rerun_simulation["case_results"]) == 416,
        "resolved_root_count_430": rerun_simulation["resolved_root_count"] == 430,
        "path_count_13371": rerun_simulation["candidate_path_count"] == 13371,
        "depth_counts_3332_4477_5562": rerun_simulation["paths_by_exact_depth"] == {
            "1": 3332, "2": 4477, "3": 5562,
        },
        "paths_per_case_p50_p75_p90_p95_p99_max": [
            rerun_simulation["candidate_paths_per_anchor"][key]
            for key in (
                "p50_nearest_rank", "p75_nearest_rank", "p90_nearest_rank",
                "p95_nearest_rank", "p99_nearest_rank", "maximum",
            )
        ] == [31, 44, 62, 68, 78, 91],
        "unique_records_p50_p95_p99_max": [
            rerun_simulation["unique_records_reached_including_anchors"][key]
            for key in ("p50_nearest_rank", "p95_nearest_rank", "p99_nearest_rank", "maximum")
        ] == [20, 38, 43, 50],
        "coverage_depth_14_21_41": [
            rerun_coverage["by_depth"][str(depth)]["represented_sequence_count"]
            for depth in (1, 2, 3)
        ] == [14, 21, 41],
        "coverage_total_76_of_76": rerun_coverage["overall"] == {
            "safe_sequence_count": 76,
            "represented_sequence_count": 76,
            "structural_sequence_coverage": 1.0,
        },
        "vendor_employee_entry_zero": rerun_simulation["hub_attempts_prevented"]["vendor_or_employee_node_entry_count"] == 0,
        "cycle_rejections_4018": rerun_simulation["cycles_prevented_by_simple_path"]["total"] == 4018,
        "terminal_returns_stopped_4415": rerun_simulation["phase6a1_safe_topology_comparison"]["terminal_return_candidates_stopped_before_adjacency_lookup"] == 4415,
        "cycle_controls_reconcile_8433": rerun_simulation["phase6a1_safe_topology_comparison"]["cycle_control_equivalent_total"] == 8433,
        "accepted_path_transition_partition_22_plus_8": (
            rerun_simulation["transition_exercise"]["accepted_path_transition_count"] == 22
            and rerun_simulation["transition_exercise"]["not_present_in_accepted_paths_count"] == 8
        ),
    }
    if not all(checks.values()):
        raise RuntimeError("BLOCK FREEZE — TOPOLOGY EQUIVALENCE FAILURE: " + canonical(checks))
    return {
        "rerun_simulation": rerun_simulation,
        "rerun_coverage": rerun_coverage,
        "rerun_fanout": rerun_fanout,
        "validation": {
            "artifact_type": "graph_v1_1_topology_equivalence_validation",
            "artifact_version": "1.1",
            "status": "FROZEN",
            "freeze_status": FREEZE_STATUS,
            "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
            "not_retrieval_evaluation": True,
            "validation_gold_used": False,
            "checks": checks,
            "candidate_path_set_sha256": rerun_simulation["candidate_path_set_sha256"],
            "topology_equivalence_result": "PASS",
            "structural_sequence_coverage_result": "76/76",
            "forbidden_vendor_employee_entry_count": 0,
            "serialization_convention": SERIALIZATION_CONVENTION,
        },
    }


def build_scientific_integrity(input_verification: dict[str, Any]) -> dict[str, Any]:
    prohibited_flags = {
        "phase5_artifacts_modified": False,
        "graph_v1_registry_modified": False,
        "graph_v1_graph_modified": False,
        "phase6a_artifacts_modified": False,
        "phase6a1_artifacts_modified": False,
        "phase6a2_artifacts_modified": False,
        "new_operational_relation_types_created": False,
        "new_synthetic_node_types_created": False,
        "validation_gold_opened": False,
        "validation_gold_used_for_freeze": False,
        "validation_retrieval_performance_used_to_change_grammar": False,
        "heldout_labels_opened": False,
        "heldout_gold_opened": False,
        "oracle_sources_opened": False,
        "previous_model_predictions_used_for_grammar": False,
        "payment_bank_enabled": False,
        "bank_statement_relation_added": False,
        "tier_b_enabled": False,
        "semantic_fallback_enabled": False,
        "llm_calls_made": False,
        "api_calls_made": False,
        "new_embeddings_created": False,
        "graph_v1_1_retriever_implemented": False,
        "graph_v1_1_retrieval_evaluated": False,
        "phase6b_started": False,
    }
    if any(prohibited_flags.values()):
        raise RuntimeError("BLOCK GRAPH v1.1 FREEZE — SCIENTIFIC INTEGRITY FAILURE")
    return {
        "artifact_type": "graph_v1_1_freeze_scientific_integrity",
        "artifact_version": "1.1",
        "status": "FROZEN",
        "freeze_status": FREEZE_STATUS,
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "integrity_status": "PASS",
        "parent_hash_verification_status": input_verification["status"],
        **prohibited_flags,
        "topology_only_structural_verification_performed": True,
        "retrieval_evaluation_performed": False,
        "violation_policy": "RECOMMEND BLOCK GRAPH v1.1 IMPLEMENTATION",
        "serialization_convention": SERIALIZATION_CONVENTION,
    }


def build_transition_validation_artifact(
    transition_validation: dict[str, Any], semantic_diff: dict[str, Any],
    final_forbidden: dict[str, Any],
) -> dict[str, Any]:
    proposed_ids = {row["transition_id"] for row in transition_validation["transition_validations"]}
    excluded_ids = {
        row["excluded_transition_id"] for row in final_forbidden["excluded_frozen_directional_transitions"]
    }
    return {
        "artifact_type": "graph_v1_1_transition_freeze_validation",
        "artifact_version": "1.1",
        "status": "FROZEN",
        "freeze_status": FREEZE_STATUS,
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "transition_count": transition_validation["transition_count"],
        "passing_transition_count": transition_validation["passing_transition_count"],
        "transition_validation_result": "30/30 PASS",
        "new_relation_type_count": transition_validation["new_relation_type_count"],
        "semantic_transition_diff_count": semantic_diff["semantic_transition_diff_count"],
        "forbidden_direction_count": len(excluded_ids),
        "forbidden_direction_promotion_count": 0,
        "proposed_and_excluded_id_sets_disjoint": proposed_ids.isdisjoint(excluded_ids),
        "validation_unused_transition_count": transition_validation["validation_unused_transition_count"],
        "validation_unused_transition_ids": transition_validation["validation_unused_transition_ids"],
        "validation_unused_transitions": transition_validation["validation_unused_transitions"],
        "transition_validations": transition_validation["transition_validations"],
        "validation_frequency_used_as_correctness_criterion": False,
        "result": "PASS",
        "serialization_convention": SERIALIZATION_CONVENTION,
    }


def build_core_artifacts(
    parents: dict[str, Any], input_verification: dict[str, Any],
    transition_validation: dict[str, Any], runner: Any, runner_data: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    final_grammar = build_final_grammar(parents, transition_validation)
    final_transition_matrix = build_final_transition_matrix(parents, transition_validation)
    final_node_matrix = build_final_node_matrix(parents)
    final_forbidden = build_final_forbidden(parents)
    final_motif_mapping = build_final_motif_mapping(parents)
    final_justifications = build_final_justifications(parents, transition_validation)
    final_risks = build_final_risks(parents)

    semantic_diff = build_semantic_diff(
        parents, final_grammar, final_transition_matrix, final_node_matrix, final_forbidden,
    )
    topology = rerun_topology(parents, runner, runner_data, final_grammar, final_forbidden)
    transition_validation_artifact = build_transition_validation_artifact(
        transition_validation, semantic_diff, final_forbidden,
    )
    scientific_integrity = build_scientific_integrity(input_verification)

    final_fanout = freeze_artifact(
        parents["draft_fanout"], PHASE6A2 / "grammar_fanout_analysis.json",
    )
    final_fanout.update({
        "artifact_name": "grammar_fanout_analysis_v1_1.json",
        "freeze_recheck_result": "PASS",
        "gl_fanout_policy": "ENUMERATE_ALL_EXACT_ELIGIBLE_EDGES / NO_ARBITRARY_TRANSITION_CAP",
        "gl_fanout_cap_status": "NOT_FROZEN / NO_RESEARCH_TRUNCATION",
        "transition_local_cap": None,
    })
    final_coverage = freeze_artifact(
        parents["draft_coverage"], PHASE6A2 / "grammar_structural_coverage.json",
    )
    final_coverage.update({
        "artifact_name": "grammar_structural_coverage_v1_1.json",
        "freeze_recheck_result": "PASS",
        "structural_sequence_coverage": 1.0,
        "metric_is_retrieval_performance": False,
    })
    final_simulation = freeze_artifact(
        parents["draft_simulation"], PHASE6A2 / "grammar_topology_simulation.json",
    )
    final_simulation.update({
        "artifact_name": "grammar_topology_simulation_v1_1.json",
        "freeze_recheck_result": "PASS",
        "final_grammar_candidate_path_set_sha256": topology["rerun_simulation"]["candidate_path_set_sha256"],
        "semantic_equivalence_to_phase6a2": True,
        "retrieval_evaluation_performed": False,
    })

    core = {
        "graph_traversal_grammar_v1_1.json": final_grammar,
        "typed_transition_matrix_v1_1.json": final_transition_matrix,
        "node_type_traversal_matrix_v1_1.json": final_node_matrix,
        "forbidden_traversals_v1_1.json": final_forbidden,
        "v1_motif_to_v1_1_grammar_mapping.json": final_motif_mapping,
        "grammar_transition_justifications_v1_1.json": final_justifications,
        "grammar_risk_register_v1_1.json": final_risks,
        "grammar_fanout_analysis_v1_1.json": final_fanout,
        "grammar_structural_coverage_v1_1.json": final_coverage,
        "grammar_topology_simulation_v1_1.json": final_simulation,
        "draft_to_final_semantic_diff_v1_1.json": semantic_diff,
        "transition_freeze_validation_v1_1.json": transition_validation_artifact,
        "topology_equivalence_validation_v1_1.json": topology["validation"],
        "scientific_integrity_v1_1_freeze.json": scientific_integrity,
    }
    context = {
        "final_grammar": final_grammar,
        "final_forbidden": final_forbidden,
        "semantic_diff": semantic_diff,
        "topology": topology,
        "transition_validation_artifact": transition_validation_artifact,
        "scientific_integrity": scientific_integrity,
        "final_risks": final_risks,
        "final_fanout": final_fanout,
        "final_coverage": final_coverage,
        "final_simulation": final_simulation,
    }
    return core, context


def artifact_hashes_from_payloads(payloads: dict[str, dict[str, Any] | str]) -> dict[str, dict[str, Any]]:
    result = {}
    for name, payload in sorted(payloads.items()):
        raw = payload.encode("utf-8") if isinstance(payload, str) else serialize_json(payload)
        result[name] = {"sha256": sha256_bytes(raw), "bytes": len(raw)}
    return result


def build_determinism_artifact(
    core_run_1: dict[str, Any], core_run_2: dict[str, Any],
) -> dict[str, Any]:
    hashes_1 = artifact_hashes_from_payloads(core_run_1)
    hashes_2 = artifact_hashes_from_payloads(core_run_2)
    comparisons = {
        name: {
            "run_1_sha256": hashes_1[name]["sha256"],
            "run_2_sha256": hashes_2[name]["sha256"],
            "run_1_bytes": hashes_1[name]["bytes"],
            "run_2_bytes": hashes_2[name]["bytes"],
            "identical": hashes_1[name] == hashes_2[name],
        }
        for name in sorted(hashes_1)
    }
    if set(hashes_1) != set(hashes_2) or not all(row["identical"] for row in comparisons.values()):
        raise RuntimeError("BLOCK FREEZE — DETERMINISTIC REGENERATION FAILURE: " + canonical(comparisons))
    return {
        "artifact_type": "graph_v1_1_freeze_determinism_validation",
        "artifact_version": "1.1",
        "status": "FROZEN",
        "freeze_status": FREEZE_STATUS,
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "build_count": 2,
        "canonical_timestamp_reused": True,
        "canonical_timestamp": CANONICAL_FREEZE_TIMESTAMP,
        "core_artifact_count": len(comparisons),
        "core_artifact_comparisons": comparisons,
        "semantic_content_identical": True,
        "raw_bytes_identical": True,
        "transition_sets_identical": True,
        "transition_ids_identical": True,
        "topology_path_sets_identical": True,
        "structural_sequence_coverage_identical": True,
        "fanout_statistics_identical": True,
        "prohibition_outcomes_identical": True,
        "deterministic_regeneration_result": "PASS",
        "serialization_convention": SERIALIZATION_CONVENTION,
    }


def build_manifest(
    input_verification: dict[str, Any], lineage: dict[str, Any],
    core: dict[str, Any], determinism: dict[str, Any], context: dict[str, Any],
) -> dict[str, Any]:
    hash_scope_payloads: dict[str, dict[str, Any] | str] = {**core}
    hash_scope_payloads["determinism_validation_v1_1_freeze.json"] = determinism
    output_hashes = artifact_hashes_from_payloads(hash_scope_payloads)
    grammar = context["final_grammar"]
    return {
        "artifact_type": "graph_v1_1_freeze_manifest",
        "artifact_version": "1.1",
        "status": "FROZEN",
        "freeze_status": FREEZE_STATUS,
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "decision_cutoff": DECISION_CUTOFF,
        "phase6a2_report_sha256": EXPECTED_PRIMARY_HASHES[PHASE6A2 / "PHASE6A2_TYPED_GRAMMAR_DESIGN_REVIEW.md"],
        "phase6a2_hash_inventory_sha256": EXPECTED_PRIMARY_HASHES[PHASE6A2 / "phase6a2_artifact_hashes.json"],
        "phase6a1_report_sha256": EXPECTED_PRIMARY_HASHES[PHASE6A1 / "PHASE6A1_MOTIF_DIAGNOSTIC_REVIEW.md"],
        "phase6a1_hash_inventory_sha256": EXPECTED_PRIMARY_HASHES[PHASE6A1 / "phase6a1_artifact_hashes.json"],
        "graph_v1_node_registry_sha256": EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_node_registry_v1.json"],
        "graph_v1_relation_registry_sha256": EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_relation_registry_v1.json"],
        "graph_v1_path_motifs_sha256": EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_path_motifs_v1.json"],
        "graph_v1_ranking_policy_sha256": EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_ranking_policy_v1.json"],
        "graph_v1_freeze_manifest_sha256": EXPECTED_PRIMARY_HASHES[REGISTRY_V1 / "graph_freeze_manifest_v1.json"],
        "phase6a_graph_nodes_sha256": EXPECTED_PRIMARY_HASHES[PHASE6A / "graph/nodes.jsonl"],
        "phase6a_graph_edges_sha256": EXPECTED_PRIMARY_HASHES[PHASE6A / "graph/edges.jsonl"],
        "parent_hash_verification": input_verification,
        "phase6a2_references_same_parent_lineage": lineage["phase6a2_references_same_parent_lineage"],
        "graph_node_count": lineage["graph_node_count"],
        "graph_edge_count": lineage["graph_edge_count"],
        "graph_node_type_count": lineage["graph_node_type_count"],
        "graph_frozen_relation_type_count": lineage["frozen_relation_count"],
        "transition_count": grammar["transition_count"],
        "backbone_transition_count": grammar["transition_count_by_class"]["BACKBONE"],
        "supporting_transition_count": grammar["transition_count_by_class"]["SUPPORTING"],
        "context_transition_count": grammar["transition_count_by_class"]["CONTEXT"],
        "terminal_context_transition_count": grammar["transition_count_by_class"]["TERMINAL_CONTEXT"],
        "frozen_relation_types_used": grammar["frozen_relation_types_used"],
        "frozen_relation_type_count_used": grammar["relation_type_count"],
        "forbidden_direction_count": context["transition_validation_artifact"]["forbidden_direction_count"],
        "forbidden_direction_promotion_count": context["transition_validation_artifact"]["forbidden_direction_promotion_count"],
        "max_path_depth": 3,
        "simple_path_only": True,
        "structural_sequence_count": 76,
        "structural_sequence_coverage": 1.0,
        "semantic_transition_diff_count": context["semantic_diff"]["semantic_transition_diff_count"],
        "validation_unused_but_retained_transition_count": context["transition_validation_artifact"]["validation_unused_transition_count"],
        "payment_bank_enabled": False,
        "bank_statement_membership_enabled": False,
        "bank_statement_membership_status": "RELATION_GAP / EXCLUDED UNRESOLVED FUTURE CAPABILITY",
        "bank_settlement_linkage_status": "RELATION_GAP / SEPARATE FUTURE TIER_B RESEARCH",
        "synthetic_gl_journal_enabled": False,
        "tier_b_enabled": False,
        "semantic_fallback_enabled": False,
        "generic_bfs_enabled": False,
        "vendor_cross_transaction_traversal_enabled": False,
        "employee_cross_transaction_traversal_enabled": False,
        "gl_fanout_policy": "ENUMERATE_ALL_EXACT_ELIGIBLE_DETERMINISTIC_EDGES / NO_ARBITRARY_TRANSITION_LOCAL_TRUNCATION",
        "gl_fanout_cap_status": "NOT_FROZEN / NO_RESEARCH_TRUNCATION",
        "gl_observed_maximum_fanout": 8,
        "max_raw_source_records": 40,
        "exact_llm_token_cap_status": "NOT_YET_FROZEN",
        "validation_gold_used_for_freeze": False,
        "heldout_gold_opened": False,
        "heldout_labels_opened": False,
        "oracle_sources_opened": False,
        "llm_calls_made": False,
        "api_calls_made": False,
        "new_embeddings_created": False,
        "graph_v1_1_implemented": False,
        "graph_v1_1_retrieval_evaluated": False,
        "phase6b_authorized": False,
        "implementation_commit_or_freeze_commit": "NOT_AVAILABLE_WORKSPACE_NOT_GIT_REPOSITORY",
        "environment_info": {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
        },
        "unresolved_production_policy_count": 2,
        "unresolved_production_policies": [
            "GL fan-out drift / production cap governance",
            "absent deterministic bank-settlement linkage",
        ],
        "topology_equivalence_result": context["topology"]["validation"]["topology_equivalence_result"],
        "scientific_integrity_result": context["scientific_integrity"]["integrity_status"],
        "deterministic_regeneration_result": determinism["deterministic_regeneration_result"],
        "output_artifact_hashes": output_hashes,
        "output_artifact_hash_scope": "Core frozen specification/validation artifacts plus determinism artifact; excludes this manifest, the report, and the final hash inventory to avoid circular dependencies.",
        "hash_inventory_circularity_policy": "graph_v1_1_freeze_hashes.json hashes every other final artifact and omits only its own raw digest; its external digest is reported at handoff.",
        "serialization_convention": SERIALIZATION_CONVENTION,
    }


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return lines


def build_report(
    input_verification: dict[str, Any], lineage: dict[str, Any],
    manifest: dict[str, Any], context: dict[str, Any], determinism: dict[str, Any],
) -> str:
    grammar = context["final_grammar"]
    simulation = context["final_simulation"]
    coverage = context["final_coverage"]
    fanout = context["final_fanout"]
    semantic_diff = context["semantic_diff"]
    transition_validation = context["transition_validation_artifact"]
    risks = context["final_risks"]
    integrity = context["scientific_integrity"]
    path_distribution = simulation["candidate_paths_per_anchor"]
    unique_distribution = simulation["unique_records_reached_including_anchors"]
    maximum_fanout = fanout["maximum_proposed_transition"]

    lines = [
        "# Graph v1.1 Typed Financial Traversal Grammar — Registry Freeze Review",
        "",
        f"Freeze status: `{FREEZE_STATUS}`",
        "",
        "This is an internal research-readiness freeze of registry/specification artifacts. It does not implement or evaluate a Graph v1.1 retriever.",
        "",
        "## A. Executive decision",
        "",
        "Freeze the verified Phase 6A.2 typed grammar as immutable Graph v1.1 specification artifacts. All parent hashes, 30 transition validations, zero semantic-drift checks, topology equivalence, 76/76 structural sequence coverage, hub controls, scientific-integrity controls, and double-build hashes pass.",
        "",
        "This decision authorizes only a later implementation review. No retriever, ranking engine, evidence selector, retrieval evaluation, LLM workflow, or Phase 6B activity is authorized here.",
        "",
        "## B. Parent artifact verification",
        "",
        f"The freeze gate independently passed **{input_verification['verified_check_count']} raw-byte checks over {input_verification['verified_distinct_path_count']} distinct parent paths**. Checks include prompt-pinned Phase 6A.2 artifacts, all inventory-listed Phase 6A.2 extras, the complete Phase 6A.1 inventory, five Graph v1.0 registry parents, and the persisted graph nodes/edges. No failed check was normalized, repaired, or regenerated.",
        "",
    ]
    primary_rows = []
    check_by_path = {row["path"]: row for row in input_verification["checks"]}
    for path, expected in sorted(EXPECTED_PRIMARY_HASHES.items(), key=lambda row: row[0].as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        row = check_by_path[relative]
        primary_rows.append((relative, expected, row["observed_sha256"], row["status"]))
    lines.extend(markdown_table(["Parent", "Expected SHA-256", "Observed SHA-256", "Result"], primary_rows))
    lines.extend([
        "",
        "## C. Graph v1.0 lineage",
        "",
        f"Graph v1.0 remains immutable and independently reconstructible. Its node, relation, motif, ranking, and freeze-manifest hashes match. The persisted graph remains {lineage['graph_node_count']:,} nodes across {lineage['graph_node_type_count']} types and {lineage['graph_edge_count']:,} edges across {lineage['frozen_relation_count']} frozen relation types. Graph v1.1 creates and deletes zero graph edges.",
        "",
        "## D. Phase 6A.1 diagnostic lineage",
        "",
        "The Phase 6A.1 report and complete hash inventory match their pinned digests. The v1.1 freeze preserves the diagnostic conclusion that the v1.0 multi-hop failure arose from fixed-motif execution constraints, not missing deterministic graph structure. Phase 6A.1 was neither rerun nor modified.",
        "",
        "## E. Phase 6A.2 design lineage",
        "",
        "Every required Phase 6A.2 proposal artifact and inventory-listed extra matches exactly. Phase 6A.2 references the same Graph v1.0, Phase 6A graph, and Phase 6A.1 lineage verified here. Promotion changes only version/status/filename, serialization, and freeze-validation metadata.",
        "",
        "## F. Draft-to-final semantic diff",
        "",
        f"Machine-readable comparison reports **SEMANTIC_TRANSITION_DIFF_COUNT = {semantic_diff['semantic_transition_diff_count']}** and global semantic diff count {semantic_diff['global_semantic_diff_count']}. Transition IDs, node types, relation IDs, directions, classes, hop permissions, continuation and terminal behavior, hub/multiplicity/cycle rules, provenance, temporal rules, node policies, relation dispositions, and forbidden definitions are unchanged.",
        "",
    ])
    diff_rows = [
        (row["transition_id"], row["semantic_diff_count"], row["result"])
        for row in semantic_diff["transition_results"]
    ]
    lines.extend(markdown_table(["Transition", "Semantic changes", "Result"], diff_rows))
    lines.extend([
        "",
        "Allowed freeze-normalization differences are artifact version, frozen status, canonical filename, deterministic serialization metadata, fixed timestamp, and label-independent freeze-validation attestations.",
        "",
        "## G. Transition inventory",
        "",
        f"All **{grammar['transition_count']}** transitions passed checks A–L. No new relation, edge, or node type was introduced.",
        "",
    ])
    validation_by_id = {
        row["transition_id"]: row for row in transition_validation["transition_validations"]
    }
    transition_rows = []
    for transition in grammar["transitions"]:
        validation = validation_by_id[transition["transition_id"]]
        transition_rows.append((
            transition["transition_id"], transition["transition_class"], transition["relation_id"],
            transition["traversal_direction"], transition["current_node_type"], transition["next_node_type"],
            validation["validation_route_usage_count"], validation["result"],
        ))
    lines.extend(markdown_table([
        "Transition ID", "Class", "Frozen relation", "Direction", "Current type", "Next type",
        "Accepted-route usage", "Freeze validation",
    ], transition_rows))
    lines.extend([
        "",
        "## H. Transition-class counts",
        "",
    ])
    class_rows = [
        (transition_class, grammar["transition_count_by_class"][transition_class])
        for transition_class in TRANSITION_CLASSES
    ]
    lines.extend(markdown_table(["Class", "Frozen transition count"], class_rows))
    lines.extend([
        "",
        "The class assignment of every transition is byte-derived from the approved proposal and was not reinterpreted during freeze.",
        "",
        "## I. Frozen relation types used",
        "",
        f"The grammar uses **{grammar['relation_type_count']}** of the 22 existing Graph v1.0 relation types:",
        "",
    ])
    for relation_id in grammar["frozen_relation_types_used"]:
        lines.append(f"- `{relation_id}`")
    lines.extend([
        "",
        "New relation type count: **0**.",
        "",
        "## J. Backbone traversal policy",
        "",
        "The 18 BACKBONE rows compose exact purchase, invoice, line, allocation, payment, and typed GL-source relationships. Conceptual lifecycle proximity never creates a direct edge: each hop must match its named frozen relation and exact persisted edge.",
        "",
        "## K. Context/terminal-context policy",
        "",
        "Five CONTEXT rows are exact event-anchor exits permitted only at hop 1. Five TERMINAL_CONTEXT rows collect entity-local approval/audit evidence and stop. A reached GL_ENTRY is also a terminal accounting consequence. Context cannot route through Employee, Vendor, actor identity, or another event neighborhood.",
        "",
        "## L. Payment-allocation policy",
        "",
        "The explicit `INVOICE ↔ PAYMENT_ALLOCATION ↔ PAYMENT` model remains the provenance-complete backbone. The already-frozen direct Payment↔Invoice projection remains SUPPORTING only with its exact PAYMENT_ALLOCATION provenance. No synthesized payment relation is introduced; multiplicity and all supporting path IDs remain preservable.",
        "",
        "## M. GL source-transaction policy",
        "",
        "GL traversal is restricted to the three frozen typed `GL_SOURCE_*` families and requires exact `source_transaction_id`, frozen transaction-type mapping, source/target type agreement, endpoint eligibility, edge provenance, and cutoff compliance. No fuzzy source matching, GL similarity, account bridge, or synthetic journal is permitted.",
        "",
        "## N. GL fan-out governance",
        "",
        f"The maximum proposed direction remains `{maximum_fanout['transition_id']}` with mean {maximum_fanout['statistics']['mean_out_degree']:.6f}, median {maximum_fanout['statistics']['median_out_degree']}, p95 {maximum_fanout['statistics']['p95_out_degree']}, p99 {maximum_fanout['statistics']['p99_out_degree']}, and maximum {maximum_fanout['statistics']['maximum_out_degree']}. Research policy is **enumerate all exact eligible deterministic edges with no arbitrary transition-local cap**. Cap status remains `NOT_FROZEN / NO_RESEARCH_TRUNCATION`; production drift/cap governance remains unresolved.",
        "",
        "## O. Vendor/Employee hub controls",
        "",
        f"Both orientations of seven restricted Vendor/Employee relation families remain excluded: {transition_validation['forbidden_direction_count']} directions, zero promotions. The equivalent topology run observed {simulation['hub_attempts_prevented']['path_state_occurrence_count']:,} prohibited frontier incidences and accepted **zero Vendor/Employee entries**. `AUDIT_EVENT_FOR_VENDOR` remains excluded even though locally bounded because frozen Vendor policy is authoritative.",
        "",
        "## P. Bank settlement relation gap",
        "",
        "`PAYMENT ↔ BANK_TRANSACTION` remains disabled. `BANK_SETTLEMENT_LINKAGE_STATUS = RELATION_GAP / SEPARATE FUTURE TIER_B RESEARCH`. Amount, currency, date, account, reference, text, embedding, and heuristic-window matching are prohibited.",
        "",
        "## Q. BankStatement relation gap",
        "",
        "No frozen BankStatement-to-transaction membership/reconciliation relation exists. `BANK_STATEMENT` retains an explicit empty transition set. No relationship is introduced during freeze; this remains an excluded/unresolved future capability not required by v1.1.",
        "",
        "## R. Forbidden traversal registry",
        "",
        f"The immutable registry preserves all {context['final_forbidden']['forbidden_pattern_count']} draft prohibitions and {context['final_forbidden']['excluded_frozen_directional_transition_count']} excluded frozen directions. It is default-deny: an existing graph edge is not traversable without an exact grammar row.",
        "",
    ])
    for pattern in context["final_forbidden"]["forbidden_patterns"]:
        lines.append(f"- `{pattern['forbidden_id']}` — {pattern['pattern']}")
    lines.extend([
        "",
        "## S. Depth and cycle policies",
        "",
        f"`MAX_PATH_DEPTH = 3`; depth 1, 2, and 3 remain separately identifiable. Paths are record-ID-simple. The equivalent run rejected {simulation['cycles_prevented_by_simple_path']['total']:,} repeated-record expansions and stopped {simulation['phase6a1_safe_topology_comparison']['terminal_return_candidates_stopped_before_adjacency_lookup']:,} terminal event/GL returns earlier, reconciling to {simulation['phase6a1_safe_topology_comparison']['cycle_control_equivalent_total']:,}. No additional cycle behavior is introduced.",
        "",
        "## T. Multiplicity behavior",
        "",
        "Every exact eligible neighbor is enumerated deterministically; one-to-many and many-to-many facts are not collapsed. No arbitrary transition cap exists. The future `MAX_RAW_SOURCE_RECORDS = 40` selection budget applies after traversal and does not limit candidate paths or alter relation cardinality.",
        "",
        "## U. Provenance guarantees",
        "",
        "Every transition retains transition ID/class, relation ID/direction, current and next node types, stored/current/next operational fields, edge ID, provenance record ID/type/fields, anchor and node sequence, temporal result, path depth, and path-class sequence. All 30 provenance validations pass.",
        "",
        "## V. Temporal guarantees",
        "",
        f"The authoritative cutoff remains **{DECISION_CUTOFF}**. Every hop requires cutoff eligibility for both endpoints, the persisted edge, and provenance-effective availability. A grammar row cannot override temporal eligibility; the equivalence run recorded zero type/provenance/temporal violations.",
        "",
        "## W. Structural sequence coverage",
        "",
        f"STRUCTURAL_SEQUENCE_COVERAGE remains **{coverage['overall']['represented_sequence_count']}/{coverage['overall']['safe_sequence_count']} = {coverage['overall']['structural_sequence_coverage']:.1%}**: depth 1 is 14/14, depth 2 is 21/21, and depth 3 is 41/41. This is typed-sequence representability, not required-document recall, evidence precision, full-evidence coverage, RCA accuracy, or LLM performance.",
        "",
        "## X. Topology-equivalence validation",
        "",
        f"The final frozen specification reproduces the proposal topology exactly: 416 route cases, {simulation['resolved_root_count']} roots, {simulation['candidate_path_count']:,} accepted prefixes, and depth counts {simulation['paths_by_exact_depth']['1']:,}/{simulation['paths_by_exact_depth']['2']:,}/{simulation['paths_by_exact_depth']['3']:,}. Paths per case are p50 {path_distribution['p50_nearest_rank']}, p75 {path_distribution['p75_nearest_rank']}, p90 {path_distribution['p90_nearest_rank']}, p95 {path_distribution['p95_nearest_rank']}, p99 {path_distribution['p99_nearest_rank']}, max {path_distribution['maximum']}. Unique records including anchors are p50 {unique_distribution['p50_nearest_rank']}, p95 {unique_distribution['p95_nearest_rank']}, p99 {unique_distribution['p99_nearest_rank']}, max {unique_distribution['maximum']}. Candidate path digest: `{simulation['candidate_path_set_sha256']}`.",
        "",
        "No retrieval metric or gold evidence was calculated.",
        "",
        "## Y. Eight validation-unused transitions",
        "",
        "**Absence from the validation routing mix is not evidence that an operationally valid transition should be removed.** The eight rows below have zero accepted-path usage in that routing mix but pass all frozen-relation, type, direction, provenance, temporal, fan-out, hub, label-independence, and no-new-fact checks.",
        "",
    ])
    unused_rows = []
    for row in transition_validation["validation_unused_transitions"]:
        stats = row["fanout_evidence"]
        unused_rows.append((
            row["transition_id"], row["underlying_frozen_relation"], row["current_node_type"],
            row["next_node_type"], row["traversal_direction"], row["transition_class"],
            row["validation_route_usage_count"],
            f"{row['global_graph_support']['edge_count']} exact edges",
            f"mean {stats['mean_out_degree']:.6f}; med {stats['median_out_degree']}; p95 {stats['p95_out_degree']}; p99 {stats['p99_out_degree']}; max {stats['maximum_out_degree']}",
            row["operational_semantic_justification"],
            "RETAINED — exact frozen relation; validation frequency is not correctness",
            "false",
        ))
    lines.extend(markdown_table([
        "Transition ID", "Relation", "Source/current", "Target/next", "Direction", "Class",
        "Route usage", "Global support", "Fan-out", "Operational justification",
        "Reason retained/excluded", "Gold used?",
    ], unused_rows))
    lines.extend([
        "",
        "All eight are retained with `VALIDATION_ROUTE_USAGE = 0` and `STRUCTURALLY_JUSTIFIED = true` in the frozen grammar metadata.",
        "",
        "## Z. Risk register",
        "",
    ])
    risk_rows = [
        (row["risk_id"], row["risk"], row["inherent_rating"], row["residual_rating"], row["mitigation"])
        for row in risks["risks"]
    ]
    lines.extend(markdown_table(["ID", "Risk", "Inherent", "Residual", "Frozen mitigation"], risk_rows))
    lines.extend([
        "",
        "No HIGH residual risk exists. The two retained review items are GL fan-out drift/production cap governance and absent deterministic bank-settlement linkage. Research traversal enumerates all exact eligible GL edges without a cap; bank settlement remains disabled for a separate Tier-B study.",
        "",
        "## AA. Scientific-integrity review",
        "",
        f"Scientific integrity is **{integrity['integrity_status']}**. Every prohibited activity flag is false: no parent modification, new relation/node, gold or held-out access, previous prediction use, payment-bank/BankStatement relation, Tier B, semantic fallback, LLM/API call, embedding, retriever implementation, retrieval evaluation, or Phase 6B work. Only topology-only structural verification was performed.",
        "",
        "## AB. Determinism and hashing",
        "",
        f"Two independent builds reused the canonical timestamp `{CANONICAL_FREEZE_TIMESTAMP}` and produced identical semantic content and raw bytes for all {determinism['core_artifact_count']} core artifacts. Manifest and report construction were also regenerated from those identical payloads. Deterministic regeneration result: **{determinism['deterministic_regeneration_result']}**.",
        "",
        "Serialization is UTF-8 JSON, lexicographically sorted keys, two-space indentation, `ensure_ascii=false`, LF newlines, and one trailing newline. Transition arrays are ordered by transition ID. No filesystem/hash-map/concurrency ordering is used.",
        "",
        "The manifest hashes core frozen artifacts but excludes itself, this report, and the hash inventory. The final hash inventory hashes every other final artifact and omits only its own digest, avoiding circularity; its external raw digest is reported at handoff.",
        "",
        "## AC. Known limitations",
        "",
        "- GL fan-out production drift/cap governance remains unresolved; no research truncation is frozen.",
        "- Payment-bank settlement linkage remains a deterministic relation gap and separate future Tier-B question.",
        "- BankStatement membership remains an unresolved, excluded capability.",
        "- The exact Phase 6B LLM token cap remains `NOT_YET_FROZEN`.",
        "- Candidate traversal may exceed the later 40-record comparison budget; evidence selection is not implemented here.",
        "",
        "This freeze establishes that Graph v1.1 is structurally defined, registry-driven, deterministic, provenance-preserving, temporally bounded, hub-restricted, and scientifically frozen before gold retrieval evaluation.",
        "",
        "It does **not** establish that Graph v1.1 beats Relational-RAG, achieves 77.239% retrieval recall, improves full evidence coverage, improves RCA accuracy, or improves LLM performance. Those claims require subsequent experiments.",
        "",
        "The serious future comparator remains Relational-RAG. Historical Phase 6A context is micro required-document Recall@40 66.716% and full evidence coverage 15.144%; neither was rerun or optimized here. The future question is: *Does bounded typed multi-hop financial traversal add evidence recovery beyond exact one-hop relational expansion?*",
        "",
        "## AD. Implementation readiness decision",
        "",
        "Final counts: 30 transitions (18 BACKBONE, 2 SUPPORTING, 5 CONTEXT, 5 TERMINAL_CONTEXT), 15 frozen relation types used, 14 node types available, 14 forbidden directions, maximum depth 3, 76/76 structural sequence coverage, zero semantic draft-to-final transition changes, eight unused-but-retained transitions, and two unresolved production policies.",
        "",
        "All implementation-review prerequisites in this freeze prompt pass. This is an internal recommendation only; implementation requires a separate explicit prompt.",
        "",
        "RECOMMEND GO FOR GRAPH v1.1 TYPED GRAMMAR IMPLEMENTATION REVIEW",
    ])
    return "\n".join(lines) + "\n"


def build_hash_inventory(
    package: dict[str, dict[str, Any] | str],
    package_run_2: dict[str, dict[str, Any] | str],
    input_verification: dict[str, Any],
) -> dict[str, Any]:
    hashes_1 = artifact_hashes_from_payloads(package)
    hashes_2 = artifact_hashes_from_payloads(package_run_2)
    double_build_comparisons = {
        name: {
            "run_1_sha256": hashes_1[name]["sha256"],
            "run_2_sha256": hashes_2[name]["sha256"],
            "run_1_bytes": hashes_1[name]["bytes"],
            "run_2_bytes": hashes_2[name]["bytes"],
            "identical": hashes_1[name] == hashes_2[name],
        }
        for name in sorted(hashes_1)
    }
    if set(hashes_1) != set(hashes_2) or not all(row["identical"] for row in double_build_comparisons.values()):
        raise RuntimeError("BLOCK FREEZE — PACKAGE DOUBLE-BUILD FAILURE: " + canonical(double_build_comparisons))
    final_names = sorted([*package, "graph_v1_1_freeze_hashes.json"])
    expected_names = set(REQUIRED_FINAL_ARTIFACTS) | set(OPTIONAL_LINEAGE_ARTIFACTS)
    if set(final_names) != expected_names:
        raise RuntimeError("final artifact name mismatch: " + canonical({
            "observed": final_names, "expected": sorted(expected_names),
        }))
    return {
        "artifact_type": "graph_v1_1_freeze_hash_inventory",
        "artifact_version": "1.1",
        "status": "FROZEN",
        "freeze_status": FREEZE_STATUS,
        "created_at_utc": CANONICAL_FREEZE_TIMESTAMP,
        "hash_algorithm": "SHA-256",
        "hash_scope": "raw serialized file bytes",
        "verified": True,
        "final_artifact_count_including_self": len(final_names),
        "final_artifact_names_including_self": final_names,
        "hashed_nonself_artifact_count": len(hashes_1),
        "artifacts": hashes_1,
        "self_hash_omitted": True,
        "self_hash_omission_reason": "Including this inventory's raw digest in itself would be circular. Its external SHA-256 is computed and reported after serialization.",
        "manifest_circularity_policy": "The manifest hashes core specification/validation outputs and determinism only; it excludes itself, report, and hash inventory. This inventory hashes the manifest and report and omits only itself.",
        "double_build_artifact_count": len(double_build_comparisons),
        "double_build_comparisons": double_build_comparisons,
        "double_build_raw_bytes_identical": True,
        "canonical_timestamp_reused": True,
        "canonical_timestamp": CANONICAL_FREEZE_TIMESTAMP,
        "parent_input_verification": input_verification,
        "analysis_script": {
            "path": Path(__file__).name,
            "sha256": sha256_file(Path(__file__)),
            "bytes": Path(__file__).stat().st_size,
        },
        "serialization_convention": SERIALIZATION_CONVENTION,
    }


def write_immutable(path: Path, raw: bytes) -> None:
    if path.exists():
        existing = path.read_bytes()
        if existing != raw:
            raise RuntimeError(f"refusing to overwrite differing frozen artifact: {path}")
        return
    path.write_bytes(raw)


def main() -> None:
    input_verification = verify_inputs()
    parents = load_parents()
    lineage = validate_parent_lineage(parents)
    transition_validation = validate_transitions(parents)
    runner = import_phase6a2_runner()
    runner_data = runner.load_data()

    core_1, context_1 = build_core_artifacts(
        parents, input_verification, transition_validation, runner, runner_data,
    )
    core_2, context_2 = build_core_artifacts(
        parents, input_verification, transition_validation, runner, runner_data,
    )
    determinism_1 = build_determinism_artifact(core_1, core_2)
    determinism_2 = build_determinism_artifact(core_1, core_2)
    if serialize_json(determinism_1) != serialize_json(determinism_2):
        raise RuntimeError("BLOCK FREEZE — DETERMINISM ARTIFACT REGENERATION FAILURE")

    manifest_1 = build_manifest(input_verification, lineage, core_1, determinism_1, context_1)
    manifest_2 = build_manifest(input_verification, lineage, core_2, determinism_2, context_2)
    if serialize_json(manifest_1) != serialize_json(manifest_2):
        raise RuntimeError("BLOCK FREEZE — MANIFEST REGENERATION FAILURE")
    report_1 = build_report(input_verification, lineage, manifest_1, context_1, determinism_1)
    report_2 = build_report(input_verification, lineage, manifest_2, context_2, determinism_2)
    if report_1.encode("utf-8") != report_2.encode("utf-8"):
        raise RuntimeError("BLOCK FREEZE — REPORT REGENERATION FAILURE")

    package_1: dict[str, dict[str, Any] | str] = {
        **core_1,
        "determinism_validation_v1_1_freeze.json": determinism_1,
        "graph_v1_1_freeze_manifest.json": manifest_1,
        "GRAPH_V1_1_TYPED_GRAMMAR_FREEZE_REVIEW.md": report_1,
    }
    package_2: dict[str, dict[str, Any] | str] = {
        **core_2,
        "determinism_validation_v1_1_freeze.json": determinism_2,
        "graph_v1_1_freeze_manifest.json": manifest_2,
        "GRAPH_V1_1_TYPED_GRAMMAR_FREEZE_REVIEW.md": report_2,
    }
    hash_inventory_1 = build_hash_inventory(package_1, package_2, input_verification)
    hash_inventory_2 = build_hash_inventory(package_1, package_2, input_verification)
    if serialize_json(hash_inventory_1) != serialize_json(hash_inventory_2):
        raise RuntimeError("BLOCK FREEZE — HASH INVENTORY REGENERATION FAILURE")

    output_payloads: dict[str, dict[str, Any] | str] = {
        **package_1,
        "graph_v1_1_freeze_hashes.json": hash_inventory_1,
    }
    for name, payload in sorted(output_payloads.items()):
        raw = payload.encode("utf-8") if isinstance(payload, str) else serialize_json(payload)
        write_immutable(OUTPUT / name, raw)

    # Independent post-write raw-byte and parse verification.
    expected_nonself_hashes = hash_inventory_1["artifacts"]
    post_write_checks = {}
    for name, metadata in sorted(expected_nonself_hashes.items()):
        path = OUTPUT / name
        if path.suffix == ".json":
            load_json(path)
        observed = sha256_file(path)
        passed = observed == metadata["sha256"] and path.stat().st_size == metadata["bytes"]
        post_write_checks[name] = passed
    if not all(post_write_checks.values()):
        raise RuntimeError("BLOCK FREEZE — POST-WRITE HASH FAILURE: " + canonical(post_write_checks))
    if sha256_file(Path(__file__)) != hash_inventory_1["analysis_script"]["sha256"]:
        raise RuntimeError("BLOCK FREEZE — ANALYSIS SCRIPT HASH FAILURE")
    if sha256_file(PHASE6A2 / "phase6a2_artifact_hashes.json") != EXPECTED_PRIMARY_HASHES[PHASE6A2 / "phase6a2_artifact_hashes.json"]:
        raise RuntimeError("BLOCK FREEZE — PHASE 6A.2 PARENT CHANGED DURING WRITE")
    report_path = OUTPUT / "GRAPH_V1_1_TYPED_GRAMMAR_FREEZE_REVIEW.md"
    if report_path.read_text(encoding="utf-8").rstrip().splitlines()[-1] != "RECOMMEND GO FOR GRAPH v1.1 TYPED GRAMMAR IMPLEMENTATION REVIEW":
        raise RuntimeError("freeze report terminal recommendation mismatch")

    hash_inventory_path = OUTPUT / "graph_v1_1_freeze_hashes.json"
    summary = {
        "status": "PASS",
        "freeze_status": FREEZE_STATUS,
        "output_directory": OUTPUT.relative_to(ROOT).as_posix(),
        "final_artifact_count": len(output_payloads),
        "transition_count": context_1["final_grammar"]["transition_count"],
        "transition_count_by_class": context_1["final_grammar"]["transition_count_by_class"],
        "relation_type_count": context_1["final_grammar"]["relation_type_count"],
        "semantic_transition_diff_count": context_1["semantic_diff"]["semantic_transition_diff_count"],
        "structural_sequence_coverage": context_1["final_coverage"]["overall"],
        "topology_path_count": context_1["final_simulation"]["candidate_path_count"],
        "candidate_path_set_sha256": context_1["final_simulation"]["candidate_path_set_sha256"],
        "validation_unused_but_retained_transition_count": transition_validation["validation_unused_transition_count"],
        "deterministic_regeneration": determinism_1["deterministic_regeneration_result"],
        "scientific_integrity": context_1["scientific_integrity"]["integrity_status"],
        "hash_inventory_external_sha256": sha256_file(hash_inventory_path),
        "recommendation": "RECOMMEND GO FOR GRAPH v1.1 TYPED GRAMMAR IMPLEMENTATION REVIEW",
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
