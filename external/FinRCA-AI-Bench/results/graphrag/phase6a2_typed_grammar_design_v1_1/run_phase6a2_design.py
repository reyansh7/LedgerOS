#!/usr/bin/env python3
"""Generate the Phase 6A.2 proposal-only typed grammar design artifacts.

This is a static design and topology-safety simulator.  It does not implement a
retriever, select evidence, open validation gold, evaluate recall, or modify any
parent graph/registry artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT = Path(__file__).resolve().parent
FREEZE = ROOT / "results/graphrag/registry_freeze_v1"
PHASE6A = ROOT / "results/graphrag/phase6a_graph_retrieval_v1_0"
PHASE6A1 = ROOT / "results/graphrag/phase6a1_motif_diagnostic_v1"
ROUTES = ROOT / "results/rag/phase5_rag_validation_routes_v1_0_20260812T040938Z/validation_routes.jsonl"

EXPECTED_PRIMARY_HASHES = {
    PHASE6A1 / "PHASE6A1_MOTIF_DIAGNOSTIC_REVIEW.md": "4b32dee5614982ffab50d458e9ee876b98f8a4fa70de25b8d8e76aab4233fec6",
    PHASE6A1 / "phase6a1_artifact_hashes.json": "d2c70d76e72fbe16a9210f191facbf8eeaecdd97bbd39c009b036cc4d332d7b5",
    FREEZE / "graph_node_registry_v1.json": "4c17ff5c863ed446418fbc2b3b407704519862feddc5f0c81546c210f8e91d10",
    FREEZE / "graph_relation_registry_v1.json": "f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3",
    FREEZE / "graph_path_motifs_v1.json": "36dd0b0d491dd6ef5f46c1dcd38cfe5e9e2ab61c632038b89cdc6ed9e0ec58ef",
    FREEZE / "graph_ranking_policy_v1.json": "85a167767f6147c2a51db9cdab47d7157731bb2126ca2cf2c452f4e9bde602f0",
    FREEZE / "graph_freeze_manifest_v1.json": "8097eb64accec2c076d07ed9ae4604d2202d1ca83578cf8557b40f034b7cad76",
    PHASE6A / "graph/nodes.jsonl": "87f80fa5e91675b192dd051598a9197c0703650f4daf09c2a7619c031295a167",
    PHASE6A / "graph/edges.jsonl": "ee364fa677abeda3b25119d5c3c2f1aea5bc8902a28e7f7ecefcddd38a77d9ed",
    PHASE6A / "retrieval/anchor_resolutions.jsonl": "b7cfffccc5660b8c50a365b8a72dc656857e4feab8dccb8049634494c6c9f9e2",
    ROUTES: "08ceeaf3a7c569ca94a87b0c0830d0fb90784daac66dd959de3fee1561b94b44",
}

NODE_TYPES = (
    "APPROVAL_EVENT", "AUDIT_EVENT", "BANK_STATEMENT", "BANK_TRANSACTION",
    "EMPLOYEE", "GL_ENTRY", "INVOICE", "INVOICE_LINE", "PAYMENT",
    "PAYMENT_ALLOCATION", "PO_LINE", "PURCHASE_ORDER", "VENDOR", "VENDOR_CHANGE",
)

MANDATORY_ARTIFACT_NAMES = (
    "graph_traversal_grammar_v1_1_draft.json",
    "typed_transition_matrix_v1_1_draft.json",
    "node_type_traversal_matrix_v1_1_draft.json",
    "forbidden_traversals_v1_1_draft.json",
    "v1_motif_to_v1_1_grammar_mapping.json",
    "grammar_transition_justifications.json",
    "grammar_fanout_analysis.json",
    "grammar_structural_coverage.json",
    "grammar_topology_simulation.json",
    "grammar_risk_register.json",
    "scientific_integrity.json",
    "phase6a2_artifact_hashes.json",
    "PHASE6A2_TYPED_GRAMMAR_DESIGN_REVIEW.md",
)

BACKBONE_RELATIONS = {
    "LINE_OF_PO", "INVOICE_REFERENCES_PO", "INVOICE_LINE_REFERENCES_PO_LINE",
    "LINE_OF_INVOICE", "ALLOCATION_OF_PAYMENT", "ALLOCATION_TO_INVOICE",
    "GL_SOURCE_BANK_TRANSACTION", "GL_SOURCE_INVOICE", "GL_SOURCE_PAYMENT",
}
SUPPORTING_RELATIONS = {"PAYMENT_ALLOCATED_TO_INVOICE"}
CONTEXT_RELATIONS = {
    "APPROVAL_FOR_INVOICE", "AUDIT_EVENT_FOR_BANK_TRANSACTION",
    "AUDIT_EVENT_FOR_INVOICE", "AUDIT_EVENT_FOR_PAYMENT",
    "AUDIT_EVENT_FOR_PURCHASE_ORDER",
}
HUB_EXCLUDED_RELATIONS = {
    "VENDOR_CHANGE_FOR_VENDOR", "PO_FOR_VENDOR", "INVOICE_FOR_VENDOR",
    "PAYMENT_FOR_VENDOR", "PURCHASE_ORDER_CREATED_BY_EMPLOYEE",
    "VENDOR_CHANGE_CHANGED_BY_EMPLOYEE", "AUDIT_EVENT_FOR_VENDOR",
}

RELATION_JUSTIFICATIONS = {
    "LINE_OF_PO": "A purchase-order line is an exact component of its purchase-order header through po_id.",
    "INVOICE_REFERENCES_PO": "An invoice's populated po_id is an exact reference to its purchase order and supports purchase-lifecycle navigation.",
    "INVOICE_LINE_REFERENCES_PO_LINE": "An invoice line's po_line_id exactly identifies the corresponding purchase-order line.",
    "LINE_OF_INVOICE": "An invoice line is an exact component of its invoice through invoice_id.",
    "APPROVAL_FOR_INVOICE": "An approval event records local approval context for exactly one invoice through invoice_id.",
    "ALLOCATION_OF_PAYMENT": "A payment allocation identifies its exact payment through payment_id.",
    "ALLOCATION_TO_INVOICE": "A payment allocation identifies its exact invoice through invoice_id.",
    "PAYMENT_ALLOCATED_TO_INVOICE": "The frozen direct payment-invoice association is backed by the PAYMENT_ALLOCATION provenance record; it is not inferred.",
    "GL_SOURCE_BANK_TRANSACTION": "A GL entry's typed source_transaction_id exactly identifies a bank transaction for approved transaction types.",
    "GL_SOURCE_INVOICE": "A GL entry's typed source_transaction_id exactly identifies an invoice for approved transaction types.",
    "GL_SOURCE_PAYMENT": "A GL entry's typed source_transaction_id exactly identifies a payment for approved transaction types.",
    "AUDIT_EVENT_FOR_BANK_TRANSACTION": "A typed audit event's entity_id exactly identifies one bank transaction.",
    "AUDIT_EVENT_FOR_INVOICE": "A typed audit event's entity_id exactly identifies one invoice.",
    "AUDIT_EVENT_FOR_PAYMENT": "A typed audit event's entity_id exactly identifies one payment.",
    "AUDIT_EVENT_FOR_PURCHASE_ORDER": "A typed audit event's entity_id exactly identifies one purchase order.",
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


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


def nearest_rank(values: Sequence[int | float], quantile: float) -> int | float:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def numeric_distribution(values: Sequence[int]) -> dict[str, Any]:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else 0.0,
        "median": statistics.median(values) if values else 0.0,
        "p50_nearest_rank": nearest_rank(values, 0.50),
        "p75_nearest_rank": nearest_rank(values, 0.75),
        "p90_nearest_rank": nearest_rank(values, 0.90),
        "p95_nearest_rank": nearest_rank(values, 0.95),
        "p99_nearest_rank": nearest_rank(values, 0.99),
        "maximum": max(values, default=0),
        "total": sum(values),
    }


def verify_inputs() -> dict[str, Any]:
    checks = []
    for path, expected in sorted(EXPECTED_PRIMARY_HASHES.items(), key=lambda item: item[0].as_posix()):
        observed = sha256_file(path)
        checks.append({
            "path": path.relative_to(ROOT).as_posix(), "expected_sha256": expected,
            "observed_sha256": observed, "status": "PASS" if observed == expected else "FAIL",
        })
    phase6a1_inventory = load_json(PHASE6A1 / "phase6a1_artifact_hashes.json")
    script_metadata = phase6a1_inventory["analysis_script"]
    script_path = PHASE6A1 / script_metadata["path"]
    observed_script = sha256_file(script_path)
    checks.append({
        "path": script_path.relative_to(ROOT).as_posix(), "expected_sha256": script_metadata["sha256"],
        "observed_sha256": observed_script,
        "status": (
            "PASS" if observed_script == script_metadata["sha256"] and script_path.stat().st_size == script_metadata["bytes"]
            else "FAIL"
        ),
    })
    for name, metadata in sorted(phase6a1_inventory["artifacts"].items()):
        path = PHASE6A1 / name
        observed = sha256_file(path)
        checks.append({
            "path": path.relative_to(ROOT).as_posix(), "expected_sha256": metadata["sha256"],
            "observed_sha256": observed,
            "status": "PASS" if observed == metadata["sha256"] and path.stat().st_size == metadata["bytes"] else "FAIL",
        })
    failed = [row for row in checks if row["status"] != "PASS"]
    if failed:
        raise RuntimeError("STOP — PHASE 6A.2 BLOCKED: " + canonical(failed))
    return {
        "status": "PASS", "proposal_status": "PROPOSAL_ONLY",
        "verified_check_count": len(checks),
        "verified_distinct_path_count": len({row["path"] for row in checks}),
        "duplicate_check_reason": "The authoritative Phase 6A.1 main report is checked both against the prompt-pinned digest and through the Phase 6A.1 inventory.",
        "checks": checks,
    }


def transition_id(current: str, relation: str, direction: str, next_type: str) -> str:
    return f"TR_{current}__{relation}__{direction}__{next_type}"


def edge_degree_stats(
    *, relation: dict[str, Any], direction: str, nodes_by_type: dict[str, list[str]],
    edges_by_relation: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    current_type = relation["source_node_type"] if direction == "FORWARD" else relation["target_node_type"]
    field = "source_record_id" if direction == "FORWARD" else "target_record_id"
    counts = Counter(edge[field] for edge in edges_by_relation[relation["relation_type"]])
    values = [counts.get(record_id, 0) for record_id in nodes_by_type[current_type]]
    return {
        "degree_domain": "all current-node-type records including zero-degree records",
        "current_node_count": len(values),
        "nonzero_current_node_count": sum(value > 0 for value in values),
        "mean_out_degree": statistics.fmean(values) if values else 0.0,
        "median_out_degree": statistics.median(values) if values else 0.0,
        "p95_out_degree": nearest_rank(values, 0.95),
        "p99_out_degree": nearest_rank(values, 0.99),
        "maximum_out_degree": max(values, default=0),
        "edge_count": sum(values),
    }


def transition_role(relation_type: str, direction: str) -> tuple[str, bool, bool, bool, bool, str]:
    if relation_type.startswith("GL_SOURCE_") and direction == "FORWARD":
        return "BACKBONE", True, False, True, True, "GL_ANCHOR_EXIT_ALLOWED_ONLY_AS_HOP_1"
    if relation_type.startswith("GL_SOURCE_") and direction == "REVERSE":
        return "BACKBONE", True, True, True, False, "STOP_AFTER_ACCOUNTING_CONSEQUENCE"
    if relation_type in BACKBONE_RELATIONS:
        return "BACKBONE", True, True, True, True, "CONTINUE_UNTIL_DEPTH_OR_OTHER_STOP"
    if relation_type in SUPPORTING_RELATIONS:
        return "SUPPORTING", True, True, True, True, "CONTINUE_WITH_EXPLICIT_PROVENANCE"
    if relation_type in CONTEXT_RELATIONS and direction == "FORWARD":
        return "CONTEXT", True, False, True, True, "CONTEXT_ANCHOR_EXIT_ALLOWED_ONLY_AS_HOP_1"
    if relation_type in CONTEXT_RELATIONS and direction == "REVERSE":
        return "TERMINAL_CONTEXT", True, True, True, False, "STOP_AFTER_LOCAL_CONTEXT_NODE"
    raise ValueError((relation_type, direction))


def multiplicity_class(transition_class: str, maximum: int) -> str:
    if transition_class == "TERMINAL_CONTEXT":
        return "TERMINAL_CONTEXT_ONLY"
    if maximum <= 4:
        return "LOW_FANOUT"
    return "BOUNDED_FANOUT"


def lifecycle_role(relation_type: str) -> str:
    if relation_type in {"LINE_OF_PO", "INVOICE_REFERENCES_PO", "INVOICE_LINE_REFERENCES_PO_LINE", "LINE_OF_INVOICE"}:
        return "PURCHASE_TO_INVOICE_LIFECYCLE"
    if relation_type in {"ALLOCATION_OF_PAYMENT", "ALLOCATION_TO_INVOICE", "PAYMENT_ALLOCATED_TO_INVOICE"}:
        return "INVOICE_PAYMENT_SETTLEMENT_LIFECYCLE"
    if relation_type.startswith("GL_SOURCE_"):
        return "ACCOUNTING_CONSEQUENCE"
    if relation_type == "APPROVAL_FOR_INVOICE":
        return "LOCAL_APPROVAL_CONTEXT"
    if relation_type.startswith("AUDIT_EVENT_FOR_"):
        return "LOCAL_AUDIT_CONTEXT"
    raise ValueError(relation_type)


def make_transition(
    relation: dict[str, Any], direction: str, fanout: dict[str, Any],
    phase6a1_audit: dict[str, Any],
) -> dict[str, Any]:
    current = relation["source_node_type"] if direction == "FORWARD" else relation["target_node_type"]
    next_type = relation["target_node_type"] if direction == "FORWARD" else relation["source_node_type"]
    transition_class, first, intermediate, terminal, may_continue, terminal_rule = transition_role(relation["relation_type"], direction)
    fanout_class = multiplicity_class(transition_class, fanout["maximum_out_degree"])
    return {
        "transition_id": transition_id(current, relation["relation_type"], direction, next_type),
        "current_node_type": current,
        "relation_id": relation["relation_type"],
        "traversal_direction": direction,
        "next_node_type": next_type,
        "transition_class": transition_class,
        "financial_lifecycle_role": lifecycle_role(relation["relation_type"]),
        "relation_tier": relation["confidence_tier"],
        "tier_family": "A",
        "max_transition_depth": (
            1 if transition_class == "CONTEXT" or terminal_rule == "GL_ANCHOR_EXIT_ALLOWED_ONLY_AS_HOP_1" else 3
        ),
        "requires_exact_edge": True,
        "requires_cutoff_eligibility": True,
        "requires_provenance": True,
        "allow_as_first_hop": first,
        "allow_as_intermediate_hop": intermediate,
        "allow_as_terminal_hop": terminal,
        "may_continue_after_transition": may_continue,
        "hub_policy": "NONE",
        "multiplicity_class": fanout_class,
        "multiplicity_policy": {
            "policy": "ENUMERATE_ALL_EXACT_EDGES_DETERMINISTICALLY",
            "ordering": "target record_id, provenance record_id, edge_id",
            "transition_local_cap": None,
            "cap_status": "CAP_NOT_YET_FROZEN" if fanout_class == "BOUNDED_FANOUT" else "NO_TRANSITION_LOCAL_CAP_PROPOSED",
            "reason": (
                "The observed maximum is bounded at eight, but any transition-local cap requires independent freeze review; this draft does not truncate."
                if fanout_class == "BOUNDED_FANOUT" else
                "Observed proposed-transition fan-out is low; no gold-derived or arbitrary truncation is introduced."
            ),
        },
        "observed_fanout": fanout,
        "cycle_policy": "SIMPLE_PATH_ONLY",
        "terminal_rule": terminal_rule,
        "semantic_justification": RELATION_JUSTIFICATIONS[relation["relation_type"]],
        "operational_field_provenance": {
            "field_orientation": "FROZEN_STORED_EDGE",
            "stored_relation_source_fields": relation["source_fields"],
            "stored_relation_target_fields": relation["target_fields"],
            "current_node_operational_fields": (
                relation["source_fields"] if direction == "FORWARD" else relation["target_fields"]
            ),
            "next_node_operational_fields": (
                relation["target_fields"] if direction == "FORWARD" else relation["source_fields"]
            ),
            "provenance_record_type": relation["provenance_record_type"],
            "constraints": relation.get("constraints", {}),
        },
        "provenance_behavior": "Retain edge_id, provenance_record_id, provenance_record_type, and provenance_fields on every path step.",
        "temporal_behavior": "Require both endpoint nodes, edge, and provenance-derived effective availability to be cutoff eligible.",
        "parent_relation_status": relation["status"],
        "parent_relation_traversable": relation["traversable"],
        "parent_relation_reverse_traversal": relation["reverse_traversal"],
        "phase6a1_directionality_class": phase6a1_audit[relation["relation_type"]]["reverse_traversal_class"],
        "reverse_safety_basis": (
            "NOT_APPLICABLE_STORED_DIRECTION" if direction == "FORWARD" else
            "Exact edge identity, provenance, and cutoff validity are unchanged when traversed from target to source."
        ),
        "path_state_requirements": {
            "terminal_context_already_reached": False,
            "hop_1_only": transition_class == "CONTEXT" or terminal_rule == "GL_ANCHOR_EXIT_ALLOWED_ONLY_AS_HOP_1",
        },
        "path_state_effects": {
            "sets_terminal_context_reached": transition_class == "TERMINAL_CONTEXT",
            "path_class_component": transition_class,
        },
        "justification_evidence_sources": [
            "graph_relation_registry_v1.json",
            "relation_directionality_audit.json",
            "persisted Phase 6A graph degree statistics",
        ],
        "validation_gold_used": False,
        "status": "PROPOSAL_ONLY",
    }


def build_transition_set(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    proposed_relation_types = BACKBONE_RELATIONS | SUPPORTING_RELATIONS | CONTEXT_RELATIONS
    transitions = []
    excluded = []
    for relation in data["relations"]:
        relation_type = relation["relation_type"]
        for direction in ("FORWARD", "REVERSE"):
            current = relation["source_node_type"] if direction == "FORWARD" else relation["target_node_type"]
            next_type = relation["target_node_type"] if direction == "FORWARD" else relation["source_node_type"]
            fanout = edge_degree_stats(
                relation=relation, direction=direction, nodes_by_type=data["nodes_by_type"],
                edges_by_relation=data["edges_by_relation"],
            )
            if relation_type in proposed_relation_types:
                transitions.append(make_transition(relation, direction, fanout, data["phase6a1_directionality_by_relation"]))
                continue
            if relation_type not in HUB_EXCLUDED_RELATIONS:
                raise RuntimeError(f"unclassified frozen relation: {relation_type}")
            if "EMPLOYEE" in {current, next_type}:
                reason_code = "EMPLOYEE_HUB_PROHIBITION"
            elif relation_type == "AUDIT_EVENT_FOR_VENDOR":
                reason_code = "VENDOR_POLICY_OVERRIDES_BOUNDED_AUDIT_RELATION"
            else:
                reason_code = "VENDOR_HUB_PROHIBITION"
            excluded.append({
                "excluded_transition_id": f"XTR_{current}__{relation_type}__{direction}__{next_type}",
                "current_node_type": current, "relation_id": relation_type,
                "traversal_direction": direction, "next_node_type": next_type,
                "reason_code": reason_code,
                "reason": "The exact relation remains in the frozen graph for provenance/context, but the Vendor/Employee hub policy prohibits ordinary grammar traversal.",
                "observed_fanout": fanout,
                "phase6a1_directionality_class": data["phase6a1_directionality_by_relation"][relation_type]["reverse_traversal_class"],
                "status": "PROPOSAL_ONLY",
            })
    transitions.sort(key=lambda row: row["transition_id"])
    excluded.sort(key=lambda row: row["excluded_transition_id"])
    if len(transitions) != 30 or len(excluded) != 14:
        raise RuntimeError(f"unexpected transition inventory: proposed={len(transitions)} excluded={len(excluded)}")
    return transitions, excluded


def diagnostic_path_id(
    case_id: str, anchor_id: str, transition_ids: Sequence[str], record_ids: Sequence[str],
    edge_ids: Sequence[str],
) -> str:
    raw = "\t".join((case_id, anchor_id, *transition_ids, *record_ids, *edge_ids)).encode("utf-8")
    return "GRAMMAR_DIAG_PATH_" + hashlib.sha256(raw).hexdigest()[:24]


def simulate_topology(
    data: dict[str, Any], transitions: list[dict[str, Any]], excluded: list[dict[str, Any]],
) -> dict[str, Any]:
    transitions_by_current: dict[str, list[dict[str, Any]]] = defaultdict(list)
    transition_by_id = {row["transition_id"]: row for row in transitions}
    for transition in transitions:
        transitions_by_current[transition["current_node_type"]].append(transition)
    for values in transitions_by_current.values():
        values.sort(key=lambda row: row["transition_id"])
    excluded_by_current: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in excluded:
        excluded_by_current[row["current_node_type"]].append(row)

    forward: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    reverse: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for edge in data["edges"]:
        forward[(edge["source_record_id"], edge["relation_type"])].append(edge)
        reverse[(edge["target_record_id"], edge["relation_type"])].append(edge)
    for mapping in (forward, reverse):
        for key in mapping:
            mapping[key].sort(key=lambda edge: (
                edge["target_record_id"], edge["source_record_id"],
                edge["provenance_record_id"], edge["edge_id"],
            ))

    route_by_case = {row["case_id"]: row for row in data["routes"]}
    path_ids: set[str] = set()
    path_rows_for_inventory: list[dict[str, Any]] = []
    case_rows = []
    paths_by_depth = Counter()
    endpoint_types_by_depth: dict[str, Counter[str]] = defaultdict(Counter)
    relation_sequences = Counter()
    transition_sequences = Counter()
    transition_sequences_by_anchor_type: dict[str, Counter[tuple[str, ...]]] = defaultdict(Counter)
    cycles_prevented = Counter()
    terminal_stops = Counter()
    terminal_stops_by_class_depth = Counter()
    no_transition_stops = Counter()
    temporal_rejections = Counter()
    provenance_rejections = Counter()
    exact_type_rejections = Counter()
    blocked_hub_occurrences = Counter()
    blocked_hub_distinct: set[tuple[str, str, str, str]] = set()
    blocked_hub_physical_edges: set[tuple[str, str]] = set()

    for resolution in data["resolutions"]:
        case_id = resolution["case_id"]
        partial: list[tuple[list[str], list[str], list[str], bool]] = [
            ([anchor], [], [], False) for anchor in resolution["resolved_record_ids"]
        ]
        case_path_ids: set[str] = set()
        case_paths_by_depth = Counter()
        case_records = set(resolution["resolved_record_ids"])
        case_new_records_by_min_depth: dict[str, int] = {}
        case_blocked_hubs: set[tuple[str, str, str]] = set()
        for depth in (1, 2, 3):
            expanded: list[tuple[list[str], list[str], list[str], bool]] = []
            for records, transition_ids, edge_ids, terminal_reached in partial:
                current = records[-1]
                current_type = data["nodes"][current]["node_type"]
                if terminal_reached:
                    terminal_stops[f"before_depth_{depth}"] += 1
                    continue

                # Measure exact frozen hub edges that an unrestricted traversal
                # could have considered but the grammar never exposes.
                for blocked in excluded_by_current.get(current_type, []):
                    mapping = forward if blocked["traversal_direction"] == "FORWARD" else reverse
                    for edge in mapping.get((current, blocked["relation_id"]), []):
                        blocked_hub_occurrences[blocked["excluded_transition_id"]] += 1
                        blocked_hub_distinct.add((case_id, current, edge["edge_id"], blocked["excluded_transition_id"]))
                        blocked_hub_physical_edges.add((edge["edge_id"], blocked["excluded_transition_id"]))
                        case_blocked_hubs.add((current, edge["edge_id"], blocked["excluded_transition_id"]))

                allowed = []
                for transition in transitions_by_current.get(current_type, []):
                    if depth == 1 and not transition["allow_as_first_hop"]:
                        continue
                    if depth > 1 and not transition["allow_as_intermediate_hop"]:
                        continue
                    if depth == 3 and not transition["allow_as_terminal_hop"]:
                        continue
                    allowed.append(transition)
                if not allowed:
                    no_transition_stops[f"before_depth_{depth}"] += 1
                for transition in allowed:
                    mapping = forward if transition["traversal_direction"] == "FORWARD" else reverse
                    for edge in mapping.get((current, transition["relation_id"]), []):
                        next_id = edge["target_record_id"] if transition["traversal_direction"] == "FORWARD" else edge["source_record_id"]
                        expected_current_edge_type = (
                            edge["source_node_type"] if transition["traversal_direction"] == "FORWARD"
                            else edge["target_node_type"]
                        )
                        expected_next_edge_type = (
                            edge["target_node_type"] if transition["traversal_direction"] == "FORWARD"
                            else edge["source_node_type"]
                        )
                        if (
                            expected_current_edge_type != transition["current_node_type"]
                            or expected_next_edge_type != transition["next_node_type"]
                            or data["nodes"][next_id]["node_type"] != transition["next_node_type"]
                        ):
                            exact_type_rejections[f"depth_{depth}"] += 1
                            continue
                        if (
                            not edge.get("edge_id")
                            or not edge.get("provenance_record_id")
                            or not edge.get("provenance_record_type")
                            or not edge.get("provenance_fields")
                        ):
                            provenance_rejections[f"depth_{depth}"] += 1
                            continue
                        if (
                            not data["nodes"][current]["temporal_eligible"]
                            or not edge["temporal_eligible"]
                            or not data["nodes"][next_id]["temporal_eligible"]
                        ):
                            temporal_rejections[f"depth_{depth}"] += 1
                            continue
                        if next_id in records:
                            cycles_prevented[f"depth_{depth}"] += 1
                            continue
                        next_records = [*records, next_id]
                        next_transition_ids = [*transition_ids, transition["transition_id"]]
                        next_edge_ids = [*edge_ids, edge["edge_id"]]
                        new_terminal = not transition["may_continue_after_transition"]
                        pid = diagnostic_path_id(case_id, next_records[0], next_transition_ids, next_records, next_edge_ids)
                        if pid in path_ids:
                            raise RuntimeError(f"duplicate diagnostic path ID: {pid}")
                        path_ids.add(pid)
                        case_path_ids.add(pid)
                        case_paths_by_depth[str(depth)] += 1
                        paths_by_depth[str(depth)] += 1
                        endpoint_types_by_depth[str(depth)][data["nodes"][next_id]["node_type"]] += 1
                        relation_sequence = tuple(transition_by_id[value]["relation_id"] for value in next_transition_ids)
                        relation_sequences[relation_sequence] += 1
                        transition_sequences[tuple(next_transition_ids)] += 1
                        transition_sequences_by_anchor_type[
                            route_by_case[case_id]["primary_entity_type"]
                        ][tuple(next_transition_ids)] += 1
                        case_records.update(next_records)
                        for record_id in next_records[1:]:
                            case_new_records_by_min_depth.setdefault(record_id, depth)
                        path_rows_for_inventory.append({
                            "path_id": pid, "case_id": case_id, "anchor_record_id": next_records[0],
                            "path_depth": depth, "record_id_sequence": next_records,
                            "node_type_sequence": [data["nodes"][value]["node_type"] for value in next_records],
                            "edge_id_sequence": next_edge_ids,
                            "transition_id_sequence": next_transition_ids,
                            "relation_sequence": list(relation_sequence),
                            "traversal_sequence": [
                                f"{transition_by_id[value]['relation_id']}:{transition_by_id[value]['traversal_direction'].lower()}"
                                for value in next_transition_ids
                            ],
                            "path_class_sequence": [transition_by_id[value]["transition_class"] for value in next_transition_ids],
                            "terminal_context_reached": new_terminal,
                        })
                        if new_terminal:
                            terminal_stops[f"after_depth_{depth}"] += 1
                            terminal_stops_by_class_depth[
                                f"{transition['transition_class']}:after_depth_{depth}"
                            ] += 1
                        else:
                            expanded.append((next_records, next_transition_ids, next_edge_ids, new_terminal))
            partial = expanded
        ordered_case_ids = sorted(case_path_ids)
        case_rows.append({
            "case_id": case_id,
            "route_anchor_type": route_by_case[case_id]["primary_entity_type"],
            "resolved_anchor_count": len(resolution["resolved_record_ids"]),
            "path_count_by_exact_depth": {str(depth): case_paths_by_depth.get(str(depth), 0) for depth in (1, 2, 3)},
            "total_path_count": len(case_path_ids),
            "unique_records_reached_including_anchors": len(case_records),
            "unique_non_anchor_records_reached": len(case_records - set(resolution["resolved_record_ids"])),
            "new_unique_records_by_minimum_depth": dict(sorted(Counter(str(value) for value in case_new_records_by_min_depth.values()).items())),
            "distinct_hub_edge_attempts_prevented": len(case_blocked_hubs),
            "path_set_sha256": sha256_bytes(("\n".join(ordered_case_ids) + "\n").encode("utf-8")),
        })

    path_rows_for_inventory.sort(key=lambda row: row["path_id"])
    case_rows.sort(key=lambda row: row["case_id"])
    path_counts = [row["total_path_count"] for row in case_rows]
    unique_records = [row["unique_records_reached_including_anchors"] for row in case_rows]
    unique_non_anchor = [row["unique_non_anchor_records_reached"] for row in case_rows]
    root_path_counts = Counter((row["case_id"], row["anchor_record_id"]) for row in path_rows_for_inventory)
    resolved_roots = [
        (row["case_id"], record_id)
        for row in data["resolutions"] for record_id in row["resolved_record_ids"]
    ]
    root_path_values = [root_path_counts.get(root, 0) for root in resolved_roots]
    case_endpoint_sets: dict[str, set[str]] = defaultdict(set)
    case_endpoint_path_counts: Counter[tuple[str, str]] = Counter()
    for row in path_rows_for_inventory:
        endpoint = row["record_id_sequence"][-1]
        case_endpoint_sets[row["case_id"]].add(endpoint)
        case_endpoint_path_counts[(row["case_id"], endpoint)] += 1
    distinct_case_endpoints = sum(len(values) for values in case_endpoint_sets.values())
    duplicate_endpoint_occurrences = len(path_rows_for_inventory) - distinct_case_endpoints
    prohibited_hub_node_entries = sum(
        data["nodes"][row["record_id_sequence"][-1]]["node_type"] in {"VENDOR", "EMPLOYEE"}
        for row in path_rows_for_inventory
    )
    all_path_ids = sorted(path_ids)
    by_anchor_type = {}
    for anchor_type in sorted({row["route_anchor_type"] for row in case_rows}):
        selected = [row for row in case_rows if row["route_anchor_type"] == anchor_type]
        by_anchor_type[anchor_type] = {
            "case_count": len(selected),
            "candidate_paths_per_anchor": numeric_distribution([row["total_path_count"] for row in selected]),
            "unique_records_including_anchor": numeric_distribution([row["unique_records_reached_including_anchors"] for row in selected]),
            "paths_by_exact_depth": {
                str(depth): sum(row["path_count_by_exact_depth"][str(depth)] for row in selected)
                for depth in (1, 2, 3)
            },
        }
    max_fanout = max(row["observed_fanout"]["maximum_out_degree"] for row in transitions)
    max_fanout_transitions = [
        row["transition_id"] for row in transitions if row["observed_fanout"]["maximum_out_degree"] == max_fanout
    ]
    exercised_transition_ids = sorted({value for sequence in transition_sequences for value in sequence})
    unexercised_transition_ids = sorted(set(transition_by_id) - set(exercised_transition_ids))
    return {
        "artifact_type": "graphrag_typed_grammar_topology_simulation",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "simulation_scope": "Label-independent 416-case validation anchor routing set over persisted deterministic graph",
        "not_retrieval_evaluation": True,
        "gold_evidence_opened": False,
        "maximum_path_depth": 3,
        "simple_path_policy": "record_id may appear at most once per path",
        "candidate_path_count": len(path_ids),
        "candidate_path_set_sha256": sha256_bytes(("\n".join(all_path_ids) + "\n").encode("utf-8")),
        "candidate_paths_per_anchor": numeric_distribution(path_counts),
        "candidate_paths_per_resolved_root": numeric_distribution(root_path_values),
        "resolved_root_count": len(resolved_roots),
        "unique_records_reached_including_anchors": numeric_distribution(unique_records),
        "unique_non_anchor_records_reached": numeric_distribution(unique_non_anchor),
        "paths_by_exact_depth": {str(depth): paths_by_depth.get(str(depth), 0) for depth in (1, 2, 3)},
        "endpoint_node_type_counts_by_depth": {
            depth: dict(sorted(counts.items())) for depth, counts in sorted(endpoint_types_by_depth.items())
        },
        "relation_sequence_counts": [
            {"relation_sequence": list(sequence), "path_instance_count": count}
            for sequence, count in sorted(relation_sequences.items(), key=lambda item: (-item[1], item[0]))
        ],
        "transition_sequence_counts": [
            {"transition_id_sequence": list(sequence), "path_instance_count": count}
            for sequence, count in sorted(transition_sequences.items(), key=lambda item: (-item[1], item[0]))
        ],
        "transition_sequence_counts_by_anchor_type": {
            anchor_type: [
                {"transition_id_sequence": list(sequence), "path_instance_count": count}
                for sequence, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            ]
            for anchor_type, counts in sorted(transition_sequences_by_anchor_type.items())
        },
        "cycles_prevented_by_simple_path": {
            "by_attempted_depth": dict(sorted(cycles_prevented.items())),
            "total": sum(cycles_prevented.values()),
        },
        "terminal_stop_counts": dict(sorted(terminal_stops.items())),
        "terminal_stop_counts_by_transition_class_and_depth": dict(sorted(terminal_stops_by_class_depth.items())),
        "no_allowed_transition_stop_counts": dict(sorted(no_transition_stops.items())),
        "temporal_rejection_counts": dict(sorted(temporal_rejections.items())),
        "provenance_rejection_counts": dict(sorted(provenance_rejections.items())),
        "exact_edge_or_type_rejection_counts": dict(sorted(exact_type_rejections.items())),
        "multiplicity_policy_stop_count": 0,
        "hub_attempts_prevented": {
            "distinct_case_current_edge_transition_count": len(blocked_hub_distinct),
            "distinct_physical_edge_direction_count": len(blocked_hub_physical_edges),
            "path_state_occurrence_count": sum(blocked_hub_occurrences.values()),
            "by_excluded_transition_occurrence": dict(sorted(blocked_hub_occurrences.items())),
            "vendor_or_employee_node_entry_count": prohibited_hub_node_entries,
        },
        "max_degree_transition_responsible": {
            "maximum_observed_out_degree": max_fanout,
            "transition_ids": max_fanout_transitions,
        },
        "transition_exercise": {
            "proposed_transition_count": len(transition_by_id),
            "accepted_path_transition_count": len(exercised_transition_ids),
            "accepted_path_transition_ids": exercised_transition_ids,
            "not_present_in_accepted_paths_count": len(unexercised_transition_ids),
            "not_present_in_accepted_paths_transition_ids": unexercised_transition_ids,
            "interpretation": "This counts transition IDs in accepted emitted paths. A missing ID may still have been considered and rejected by a later simple-path, temporal, provenance, or state rule; it is not necessarily absent from every reachable frontier.",
            "static_review_basis_for_missing_ids": "Frozen relation semantics, Phase 6A.1 directionality classification, and graph-global directional fanout; absence from accepted route paths is not an exclusion criterion.",
        },
        "by_anchor_type": by_anchor_type,
        "case_results": case_rows,
        "phase6a1_safe_topology_comparison": {
            "phase6a1_candidate_paths_per_anchor": {"p50": 31, "p95": 68, "p99": 78, "maximum": 91},
            "phase6a1_total_paths_by_exact_depth": {"1": 3332, "2": 4477, "3": 5562},
            "path_count_delta": len(path_ids) - 13371,
            "major_unexplained_increase": len(path_ids) > math.ceil(13371 * 1.10),
            "phase6a1_cycle_candidates_removed": 8433,
            "terminal_return_candidates_stopped_before_adjacency_lookup": (
                terminal_stops.get("after_depth_1", 0) + terminal_stops.get("after_depth_2", 0)
            ),
            "context_event_return_candidates_stopped": sum(
                terminal_stops_by_class_depth.get(f"TERMINAL_CONTEXT:after_depth_{depth}", 0)
                for depth in (1, 2)
            ),
            "reached_gl_return_candidates_stopped": sum(
                terminal_stops_by_class_depth.get(f"BACKBONE:after_depth_{depth}", 0)
                for depth in (1, 2)
            ),
            "cycle_control_equivalent_total": (
                sum(cycles_prevented.values())
                + terminal_stops.get("after_depth_1", 0) + terminal_stops.get("after_depth_2", 0)
            ),
        },
        "candidate_record_deduplication_design": {
            "policy": "one evidence record plus all supporting path IDs",
            "selection_budget_applied": False,
            "maximum_raw_source_records_reference_only": 40,
            "distinct_case_endpoint_records": distinct_case_endpoints,
            "duplicate_path_endpoint_occurrences": duplicate_endpoint_occurrences,
            "duplicate_path_endpoint_fraction": duplicate_endpoint_occurrences / len(path_rows_for_inventory),
            "case_unique_endpoint_records": numeric_distribution([
                len(case_endpoint_sets.get(row["case_id"], set())) for row in case_rows
            ]),
            "cases_with_more_than_40_unique_records_including_anchors": sum(
                row["unique_records_reached_including_anchors"] > 40 for row in case_rows
            ),
        },
        "runtime_metadata_persisted": False,
    }


def sequence_representability(
    sequence: dict[str, Any], transition_lookup: dict[tuple[str, str, str, str], dict[str, Any]],
) -> tuple[bool, list[str], str | None]:
    transition_ids = []
    node_types = sequence["node_type_sequence"]
    traversals = sequence["traversal_sequence"]
    prior_may_continue = True
    for index, traversal in enumerate(traversals, start=1):
        relation, raw_direction = traversal.rsplit(":", 1)
        key = (node_types[index - 1], relation, raw_direction.upper(), node_types[index])
        transition = transition_lookup.get(key)
        if transition is None:
            return False, transition_ids, f"NO_PROPOSED_TYPED_TRANSITION:{key}"
        if not prior_may_continue:
            return False, transition_ids, f"PRIOR_TRANSITION_TERMINAL:{transition_ids[-1]}"
        if index == 1 and not transition["allow_as_first_hop"]:
            return False, transition_ids, f"HOP_1_NOT_ALLOWED:{transition['transition_id']}"
        if index > 1 and not transition["allow_as_intermediate_hop"]:
            return False, transition_ids, f"INTERMEDIATE_HOP_NOT_ALLOWED:{transition['transition_id']}"
        transition_ids.append(transition["transition_id"])
        prior_may_continue = transition["may_continue_after_transition"]
    return True, transition_ids, None


def structural_coverage(
    data: dict[str, Any], transitions: list[dict[str, Any]], simulation: dict[str, Any],
) -> dict[str, Any]:
    transition_lookup = {
        (row["current_node_type"], row["relation_id"], row["traversal_direction"], row["next_node_type"]): row
        for row in transitions
    }
    safe_sequences = data["phase6a1_sequence_inventory"]["views"]["SAFE_BIDIRECTIONAL_DIAGNOSTIC"]
    simulated_sequence_counts = {
        tuple(row["transition_id_sequence"]): row["path_instance_count"]
        for row in simulation["transition_sequence_counts"]
    }
    simulated_sequence_counts_by_anchor_type = {
        anchor_type: {
            tuple(row["transition_id_sequence"]): row["path_instance_count"]
            for row in values
        }
        for anchor_type, values in simulation["transition_sequence_counts_by_anchor_type"].items()
    }
    rows = []
    for sequence in safe_sequences:
        represented, transition_ids, reason = sequence_representability(sequence, transition_lookup)
        simulated_count = simulated_sequence_counts.get(tuple(transition_ids), 0) if represented else 0
        actually_represented = represented and simulated_count > 0
        counts_by_anchor_type = {
            anchor_type: (
                simulated_sequence_counts_by_anchor_type.get(anchor_type, {}).get(tuple(transition_ids), 0)
                if represented else 0
            )
            for anchor_type in sequence["anchor_types"]
        }
        rows.append({
            "sequence_id": sequence["sequence_id"],
            "path_depth": sequence["path_depth"],
            "node_type_sequence": sequence["node_type_sequence"],
            "traversal_sequence": sequence["traversal_sequence"],
            "anchor_types": sequence["anchor_types"],
            "distinct_anchor_count": sequence["distinct_anchor_count"],
            "path_instance_count": sequence["path_instance_count"],
            "syntactically_accepted_by_draft_grammar": represented,
            "simulated_path_instance_count": simulated_count,
            "simulated_path_instance_count_by_anchor_type": counts_by_anchor_type,
            "represented_by_anchor_type": {
                anchor_type: count > 0 for anchor_type, count in counts_by_anchor_type.items()
            },
            "represented_by_draft_grammar": actually_represented,
            "transition_id_sequence": transition_ids,
            "exclusion_reason": reason if reason else (None if actually_represented else "NO_EMITTED_PATH_IN_416_ROUTE_SIMULATION"),
        })
    def summarize(selected: list[dict[str, Any]], anchor_type: str | None = None) -> dict[str, Any]:
        represented = sum(
            row["represented_by_draft_grammar"] if anchor_type is None
            else row["represented_by_anchor_type"].get(anchor_type, False)
            for row in selected
        )
        return {
            "safe_sequence_count": len(selected),
            "represented_sequence_count": represented,
            "structural_sequence_coverage": represented / len(selected) if selected else None,
        }
    by_depth = {
        str(depth): summarize([row for row in rows if row["path_depth"] == depth])
        for depth in (1, 2, 3)
    }
    anchor_types = sorted({value for row in rows for value in row["anchor_types"]})
    by_anchor_type = {
        anchor_type: {
            "overall": summarize([row for row in rows if anchor_type in row["anchor_types"]], anchor_type),
            "by_depth": {
                str(depth): summarize([
                    row for row in rows if anchor_type in row["anchor_types"] and row["path_depth"] == depth
                ], anchor_type) for depth in (1, 2, 3)
            },
        }
        for anchor_type in anchor_types
    }
    return {
        "artifact_type": "graphrag_typed_grammar_structural_coverage",
        "artifact_version": "1.1-draft", "status": "PROPOSAL_ONLY",
        "metric_name": "STRUCTURAL_SEQUENCE_COVERAGE",
        "definition": "Distinct Phase 6A.1 safe direction-aware typed sequences both accepted by explicit draft transition/state rules and emitted at least once by the 416-route topology simulator / all distinct Phase 6A.1 safe sequences.",
        "not_required_document_recall": True,
        "gold_evidence_used": False,
        "overall": summarize(rows),
        "by_depth": by_depth,
        "by_anchor_type": by_anchor_type,
        "sequence_results": rows,
        "excluded_sequence_count": sum(not row["represented_by_draft_grammar"] for row in rows),
        "excluded_sequences": [row for row in rows if not row["represented_by_draft_grammar"]],
        "frozen_v1_motif_sequence_coverage_context": {
            "represented": 5, "safe_sequences": 76, "ratio": 5 / 76,
        },
    }


def build_transition_matrix(transitions: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for transition in transitions:
        rows.append({
            "transition_id": transition["transition_id"],
            "current_node_type": transition["current_node_type"],
            "relation_id": transition["relation_id"],
            "direction": transition["traversal_direction"],
            "next_node_type": transition["next_node_type"],
            "allowed_as_hop_1": transition["allow_as_first_hop"],
            "allowed_as_hop_2": transition["allow_as_intermediate_hop"] and transition["max_transition_depth"] >= 2,
            "allowed_as_hop_3": (
                transition["allow_as_intermediate_hop"]
                and transition["allow_as_terminal_hop"]
                and transition["max_transition_depth"] >= 3
            ),
            "transition_class": transition["transition_class"],
            "may_continue_after_transition": transition["may_continue_after_transition"],
            "hub_restriction": transition["hub_policy"],
            "terminal_rule": transition["terminal_rule"],
            "multiplicity_class": transition["multiplicity_class"],
            "observed_maximum_out_degree": transition["observed_fanout"]["maximum_out_degree"],
            "status": "PROPOSAL_ONLY",
        })
    return {
        "artifact_type": "graphrag_typed_transition_matrix",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "default_policy": "DENY_UNLESS_EXACT_ROW_MATCHES_CURRENT_TYPE_RELATION_DIRECTION_NEXT_TYPE_AND_PATH_STATE",
        "maximum_path_depth": 3,
        "row_count": len(rows),
        "rows": rows,
    }


NODE_REASONING = {
    "APPROVAL_EVENT": "An exact approval anchor may exit to its owning Invoice; approval events reached from an Invoice are local evidence and cannot route onward.",
    "AUDIT_EVENT": "An exact audit anchor may exit to its typed owning entity; audit events reached from an entity are local evidence and actor/Vendor routing stays prohibited.",
    "BANK_STATEMENT": "No frozen statement-membership relation exists, so the grammar declares an empty transition set instead of synthesizing account/date links.",
    "BANK_TRANSACTION": "Only exact typed GL consequences and local audit context are available; payment settlement linkage remains a relation gap.",
    "EMPLOYEE": "Employee is identity context and a prohibited shared hub, with no outgoing grammar transition.",
    "GL_ENTRY": "An exact GL anchor may exit through one typed source relation; a GL entry reached from its source transaction is a terminal accounting consequence.",
    "INVOICE": "Invoice is a lifecycle hub only through exact PO, line, allocation, payment-projection, GL, approval, and audit relations.",
    "INVOICE_LINE": "Invoice lines compose only through their exact owning Invoice and referenced PO line.",
    "PAYMENT": "Payment composes through exact allocation/projection relations and may expose typed GL consequences or local audit context; bank matching is disabled.",
    "PAYMENT_ALLOCATION": "The allocation record is the provenance-complete bridge between an exact Invoice and Payment and remains composable.",
    "PO_LINE": "PO lines compose through their exact PO header and exact referencing invoice lines.",
    "PURCHASE_ORDER": "Purchase orders compose to exact lines and referencing invoices and may expose local audit context; Vendor/Employee bridges are disabled.",
    "VENDOR": "Vendor is restricted identity/filter context and cannot be a cross-transaction bridge, including through audit events.",
    "VENDOR_CHANGE": "Vendor changes remain standalone context because their Vendor and Employee relations are frozen traversal-disabled.",
}


NODE_PROHIBITIONS = {
    "APPROVAL_EVENT": ["FT_CONTEXT_BRIDGE", "FT_EMPLOYEE_BRIDGE"],
    "AUDIT_EVENT": ["FT_CONTEXT_BRIDGE", "FT_EMPLOYEE_BRIDGE", "FT_VENDOR_BRIDGE", "FT_SYNTHETIC_GL_JOURNAL"],
    "BANK_STATEMENT": ["FT_DEFAULT_DENY_BFS", "FT_PAYMENT_BANK", "FT_SAME_ACCOUNT", "FT_SAME_DATE"],
    "BANK_TRANSACTION": ["FT_PAYMENT_BANK", "FT_SAME_AMOUNT", "FT_SAME_ACCOUNT"],
    "EMPLOYEE": ["FT_EMPLOYEE_BRIDGE", "FT_DEFAULT_DENY_BFS"],
    "GL_ENTRY": ["FT_SYNTHETIC_GL_JOURNAL", "FT_GL_TYPE_MISMATCH", "FT_REACHED_GL_CONTINUATION"],
    "INVOICE": ["FT_VENDOR_BRIDGE", "FT_PAYMENT_BANK", "FT_ALLOCATION_BYPASS"],
    "INVOICE_LINE": ["FT_DEFAULT_DENY_BFS"],
    "PAYMENT": ["FT_PAYMENT_BANK", "FT_VENDOR_BRIDGE", "FT_ALLOCATION_BYPASS"],
    "PAYMENT_ALLOCATION": ["FT_MULTIPLICITY_COLLAPSE"],
    "PO_LINE": ["FT_DEFAULT_DENY_BFS"],
    "PURCHASE_ORDER": ["FT_VENDOR_BRIDGE", "FT_EMPLOYEE_BRIDGE"],
    "VENDOR": ["FT_VENDOR_BRIDGE", "FT_DEFAULT_DENY_BFS"],
    "VENDOR_CHANGE": ["FT_VENDOR_BRIDGE", "FT_EMPLOYEE_BRIDGE", "FT_DEFAULT_DENY_BFS"],
}


def build_node_matrix(transitions: list[dict[str, Any]]) -> dict[str, Any]:
    by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for transition in transitions:
        by_node[transition["current_node_type"]].append(transition)
    rows = []
    for node_type in NODE_TYPES:
        outgoing = sorted(by_node[node_type], key=lambda row: row["transition_id"])
        noncontinuing_ids = [
            row["transition_id"] for row in outgoing if not row["may_continue_after_transition"]
        ]
        terminal_context_ids = [
            row["transition_id"] for row in outgoing if row["transition_class"] == "TERMINAL_CONTEXT"
        ]
        terminal_accounting_ids = [
            row["transition_id"] for row in outgoing
            if row["terminal_rule"] == "STOP_AFTER_ACCOUNTING_CONSEQUENCE"
        ]
        anchor_exit_ids = [
            row["transition_id"] for row in outgoing if row["path_state_requirements"]["hop_1_only"]
        ]
        if node_type in {"BANK_STATEMENT", "EMPLOYEE", "VENDOR", "VENDOR_CHANGE"}:
            maximum_reachable_depth = 0
        elif node_type == "BANK_TRANSACTION":
            maximum_reachable_depth = 1
        else:
            maximum_reachable_depth = 3
        rows.append({
            "node_type": node_type,
            "allowed_outgoing_transition_ids": [row["transition_id"] for row in outgoing],
            "allowed_outgoing_transition_count": len(outgoing),
            "noncontinuing_transition_ids": noncontinuing_ids,
            "terminal_context_transition_ids": terminal_context_ids,
            "terminal_accounting_consequence_transition_ids": terminal_accounting_ids,
            "anchor_exit_only_transition_ids": anchor_exit_ids,
            "explicit_empty_transition_set": not outgoing,
            "maximum_reachable_depth_from_exact_anchor": maximum_reachable_depth,
            "reached_node_state_override": (
                "TERMINAL_IF_REACHED_AFTER_HOP_0" if node_type in {"APPROVAL_EVENT", "AUDIT_EVENT", "GL_ENTRY"}
                else "NONE"
            ),
            "prohibited_pattern_ids": NODE_PROHIBITIONS[node_type],
            "reasoning": NODE_REASONING[node_type],
            "status": "PROPOSAL_ONLY",
        })
    return {
        "artifact_type": "graphrag_node_type_traversal_matrix",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "node_type_count": len(rows),
        "node_types": rows,
    }


def forbidden_entry(
    forbidden_id: str, category: str, pattern: str, rationale: str,
    *, blocked_relation_ids: Sequence[str] = (), blocked_directions: Sequence[str] = (),
    blocked_excluded_candidate_relation_ids: Sequence[str] = (),
    enforcement: str = "PRE_ENQUEUE_REJECT_AND_RECORD_REASON",
) -> dict[str, Any]:
    return {
        "forbidden_id": forbidden_id,
        "category": category,
        "pattern": pattern,
        "blocked_relation_ids": list(blocked_relation_ids),
        "blocked_excluded_candidate_relation_ids": list(blocked_excluded_candidate_relation_ids),
        "blocked_directions": list(blocked_directions),
        "enforcement": enforcement,
        "rationale": rationale,
        "authority": ["frozen registry v1", "Phase 6A.1 structural audit", "Phase 6A.2 design constraint"],
        "status": "PROPOSAL_ONLY",
    }


def build_forbidden_registry(excluded: list[dict[str, Any]]) -> dict[str, Any]:
    vendor = [
        "VENDOR_CHANGE_FOR_VENDOR", "PO_FOR_VENDOR", "INVOICE_FOR_VENDOR",
        "PAYMENT_FOR_VENDOR", "AUDIT_EVENT_FOR_VENDOR",
    ]
    employee = ["PURCHASE_ORDER_CREATED_BY_EMPLOYEE", "VENDOR_CHANGE_CHANGED_BY_EMPLOYEE"]
    entries = [
        forbidden_entry("FT_DEFAULT_DENY_BFS", "GENERIC_EXPLORATION", "Any graph edge without an exact current-type/relation/direction/next-type grammar row", "The typed grammar is a whitelist, never generic BFS."),
        forbidden_entry("FT_VENDOR_BRIDGE", "HUB", "Any * -> VENDOR -> * cross-transaction path", "Vendor is restricted identity/filter context and cannot route between transactions.", blocked_relation_ids=vendor, blocked_directions=["FORWARD", "REVERSE"]),
        forbidden_entry("FT_EMPLOYEE_BRIDGE", "HUB", "Any * -> EMPLOYEE -> * path, including actor/approver coercion", "Employee identity may be shared/system context and cannot route between transactions.", blocked_relation_ids=employee, blocked_excluded_candidate_relation_ids=["APPROVAL_EVENT_APPROVER_EMPLOYEE", "AUDIT_EVENT_ACTOR_EMPLOYEE"], blocked_directions=["FORWARD", "REVERSE"]),
        forbidden_entry("FT_PAYMENT_BANK", "RELATION_GAP", "PAYMENT <-> BANK_TRANSACTION", "The deterministic payment-bank relation is not frozen; amount/date/currency/account heuristics remain Tier B and disabled.", blocked_excluded_candidate_relation_ids=["PAYMENT_CANDIDATE_BANK_TRANSACTION"], blocked_directions=["FORWARD", "REVERSE"]),
        forbidden_entry("FT_SYNTHETIC_GL_JOURNAL", "SYNTHETIC_GRAPH", "GL_JOURNAL node, journal_id bridge/group traversal, or AUDIT_EVENT -> GL_JOURNAL", "No canonical journal-header source record exists; gl_journal route labels resolve only to GL_ENTRY anchors."),
        forbidden_entry("FT_SEMANTIC_SIMILARITY", "SEMANTIC_FALLBACK", "Embedding, text similarity, semantic neighbor, failure-class, or RCA-concept expansion", "Traversal correctness must arise from frozen operational relations, never label or semantic similarity."),
        forbidden_entry("FT_SAME_CURRENCY", "ATTRIBUTE_BRIDGE", "Traversal based only on equal currency", "Equality of a non-node attribute does not establish an operational fact."),
        forbidden_entry("FT_SAME_AMOUNT", "ATTRIBUTE_BRIDGE", "Traversal based only on equal amount", "Equality of a non-node attribute does not establish an operational fact."),
        forbidden_entry("FT_SAME_DATE", "ATTRIBUTE_BRIDGE", "Traversal based only on equal date or a date window", "Date proximity does not establish an operational fact."),
        forbidden_entry("FT_SAME_ACCOUNT", "ATTRIBUTE_BRIDGE", "Traversal based only on bank_account_id or gl_account", "Account values remain context/filter attributes and are not graph nodes or joins."),
        forbidden_entry("FT_ATTRIBUTE_BRIDGE", "ATTRIBUTE_BRIDGE", "Traversal through department, cost_center, source_system, status, or any other non-node dimension", "Attributes cannot be promoted to bridge nodes or inferred edges in this phase."),
        forbidden_entry("FT_REPEATED_RECORD", "CYCLE", "Any candidate path in which a record_id repeats", "A record-ID-simple path prohibits A -> B -> A and longer cycles."),
        forbidden_entry("FT_DEPTH_GT_3", "BOUNDEDNESS", "Any fourth or later graph edge", "MAX_PATH_DEPTH is fixed at three for this proposal."),
        forbidden_entry("FT_CONTEXT_BRIDGE", "STATE", "Continue from APPROVAL_EVENT or AUDIT_EVENT reached after hop 0", "Events enrich local evidence but cannot route to unrelated neighborhoods; an exact event anchor may take one typed owner exit at hop 1."),
        forbidden_entry("FT_GL_TYPE_MISMATCH", "TYPE_SAFETY", "GL traversal without exact source_transaction_id and frozen transaction_type target mapping", "Typed GL provenance must select exactly BANK_TRANSACTION, INVOICE, or PAYMENT."),
        forbidden_entry("FT_PROVENANCE_MISSING", "PROVENANCE", "Traverse an edge without retainable source fields, target fields, edge ID, and provenance record", "Every path step must remain operationally reconstructible."),
        forbidden_entry("FT_POST_CUTOFF", "TEMPORAL", "Traverse when source, target, edge, or provenance-effective availability exceeds cutoff", "Every path participant must be cutoff eligible; edge effective availability is the latest participant availability."),
        forbidden_entry("FT_AMBIGUOUS_OR_INFERRED_JOIN", "EXACTNESS", "Fuzzy ID, cross-type fallback, nearest neighbor, collision winner, or inferred relation", "Only persisted exact frozen edges may be followed."),
        forbidden_entry("FT_ALLOCATION_BYPASS", "PROVENANCE", "Invented Invoice <-> Payment edge without a PAYMENT_ALLOCATION provenance record", "The frozen projection is allowed only with its exact PAYMENT_ALLOCATION provenance; the allocation-node route is the fuller lifecycle representation."),
        forbidden_entry("FT_MULTIPLICITY_COLLAPSE", "CARDINALITY", "Silently select one neighbor or treat M:N/N:1 as 1:1", "Enumerate exact neighbors deterministically; a future cap may stop expansion but cannot rewrite cardinality."),
        forbidden_entry("FT_REACHED_GL_CONTINUATION", "STATE", "Continue from GL_ENTRY reached from BANK_TRANSACTION, INVOICE, or PAYMENT", "A reached GL entry is a terminal accounting consequence; only an exact GL_ENTRY anchor may exit to one typed source at hop 1."),
    ]
    return {
        "artifact_type": "graphrag_forbidden_traversal_registry",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "default_deny": True,
        "forbidden_pattern_count": len(entries),
        "forbidden_patterns": entries,
        "excluded_frozen_directional_transition_count": len(excluded),
        "excluded_frozen_directional_transitions": excluded,
        "known_relation_gaps": [
            {
                "gap_id": "RELATION_GAP_PAYMENT_BANK",
                "description": "No frozen deterministic PAYMENT <-> BANK_TRANSACTION relation exists.",
                "impact": "KNOWN STRUCTURAL LIMITATION — BANK SETTLEMENT LINKAGE EXCLUDED",
                "compensating_heuristic_allowed": False,
                "status": "PROPOSAL_ONLY",
            },
            {
                "gap_id": "RELATION_GAP_BANK_STATEMENT_TRANSACTION_MEMBERSHIP",
                "description": "No frozen BANK_STATEMENT membership/reconciliation relation to BANK_TRANSACTION exists.",
                "impact": "BANK_STATEMENT has an explicit empty transition set in v1.1; no synthetic account/date linkage is permitted.",
                "required_for_v1_1": False,
                "compensating_heuristic_allowed": False,
                "status": "PROPOSAL_ONLY",
            },
        ],
    }


def build_motif_mapping(data: dict[str, Any], transitions: list[dict[str, Any]]) -> dict[str, Any]:
    transition_by_relation_direction: dict[tuple[str, str], list[str]] = defaultdict(list)
    for transition in transitions:
        transition_by_relation_direction[(transition["relation_id"], transition["traversal_direction"])].append(transition["transition_id"])
    mapping_specs = {
        "PO_WITH_INVOICES": ("FULLY_REPRESENTABLE", "EXACT_TYPED_REVERSE", "The grammar applies PURCHASE_ORDER -> INVOICE only from a compatible current node type; Invoice -> PO is an independent forward row."),
        "PO_WITH_LINES": ("FULLY_REPRESENTABLE", "EXACT_TYPED_REVERSE", "The grammar applies PURCHASE_ORDER -> PO_LINE only from a compatible current node type."),
        "PO_INVOICE_LINES": ("FULLY_REPRESENTABLE", "DIRECTION_CORRECTED_NATURALLY_BY_GRAMMAR", "The two typed reverse rows compose from PURCHASE_ORDER; the invalid Invoice-origin first step is never looked up. The complete motif is obsolete because grammar composition generalizes it."),
        "INVOICE_PAYMENTS": ("FULLY_REPRESENTABLE", "EXACT_TYPED_REVERSE_WITH_MANDATORY_ALLOCATION_PROVENANCE", "The direct frozen projection remains SUPPORTING; the explicit PAYMENT_ALLOCATION bridge is the fuller lifecycle route."),
        "INVOICE_APPROVALS": ("FULLY_REPRESENTABLE", "TERMINAL_CONTEXT", "Invoice -> ApprovalEvent is exact local context and stops."),
        "INVOICE_AUDIT_EVENTS": ("FULLY_REPRESENTABLE", "TERMINAL_CONTEXT", "Invoice -> AuditEvent is exact local context and stops."),
        "PAYMENT_GL_ENTRIES": ("FULLY_REPRESENTABLE", "TERMINAL_ACCOUNTING_CONSEQUENCE", "Payment -> GL_ENTRY uses typed exact reverse provenance and stops at the reached GL entry."),
        "GL_ENTRY_SOURCE_TRANSACTION": ("FULLY_REPRESENTABLE_BY_TYPED_DECOMPOSITION", "WILDCARD_REMOVED", "Three explicit GL_ENTRY source rows replace the motif wildcard; no GL_JOURNAL is introduced."),
        "INVOICE_PAYMENT_BANK": ("INTENTIONALLY_NOT_REPRESENTABLE", "RELATION_GAP", "PAYMENT_CANDIDATE_BANK_TRANSACTION remains excluded and Tier B disabled."),
        "GL_PAYMENT_BANK": ("INTENTIONALLY_NOT_REPRESENTABLE", "RELATION_GAP", "PAYMENT_CANDIDATE_BANK_TRANSACTION remains excluded and Tier B disabled."),
    }
    rows = []
    for registry_group, motifs in (("FROZEN", data["motifs"]["frozen_motifs"]), ("EXCLUDED", data["motifs"]["excluded_motifs"])):
        for motif in motifs:
            representability, direction_status, explanation = mapping_specs[motif["motif_id"]]
            transition_sequence = []
            transition_alternatives = []
            if motif["motif_id"] == "GL_ENTRY_SOURCE_TRANSACTION":
                for relation in ("GL_SOURCE_BANK_TRANSACTION", "GL_SOURCE_INVOICE", "GL_SOURCE_PAYMENT"):
                    transition_alternatives.extend(transition_by_relation_direction[(relation, "FORWARD")])
            elif representability != "INTENTIONALLY_NOT_REPRESENTABLE":
                for traversal in motif["edge_sequence"]:
                    relation, direction = traversal.rsplit(":", 1)
                    transition_sequence.extend(transition_by_relation_direction[(relation, direction.upper())])
            rows.append({
                "motif_id": motif["motif_id"],
                "v1_registry_group": registry_group,
                "v1_edge_sequence": motif["edge_sequence"],
                "v1_permitted_anchor_types": motif["permitted_anchor_types"],
                "v1_1_transition_sequence": transition_sequence,
                "v1_1_transition_alternatives": sorted(transition_alternatives),
                "v1_1_transition_id_set": sorted(set(transition_sequence + transition_alternatives)),
                "representability": representability,
                "direction_status": direction_status,
                "grammar_role": (
                    "OBSOLETE_BECAUSE_GRAMMAR_COMPOSITION_GENERALIZES_IT"
                    if motif["motif_id"] == "PO_INVOICE_LINES" else "COMPATIBILITY_DOCUMENTATION_ONLY"
                ),
                "explanation": explanation,
                "v1_artifact_modified": False,
                "status": "PROPOSAL_ONLY",
            })
    return {
        "artifact_type": "graphrag_v1_motif_to_v1_1_grammar_mapping",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "v1_motifs_immutable": True,
        "mapping_is_not_migration_or_deletion": True,
        "mapped_frozen_motif_count": sum(row["v1_registry_group"] == "FROZEN" for row in rows),
        "mapped_excluded_motif_count": sum(row["v1_registry_group"] == "EXCLUDED" for row in rows),
        "mappings": rows,
    }


def build_justifications(transitions: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for transition in transitions:
        rows.append({
            "transition_id": transition["transition_id"],
            "underlying_frozen_relation": transition["relation_id"],
            "source_type": transition["current_node_type"],
            "target_type": transition["next_node_type"],
            "traversal_direction": transition["traversal_direction"],
            "operational_fields": transition["operational_field_provenance"],
            "factual_semantics_preservation": transition["semantic_justification"] + (
                " Forward traversal follows the persisted stored edge and creates no new operational fact."
                if transition["traversal_direction"] == "FORWARD" else
                " Reverse traversal changes navigation orientation only and creates no new operational fact."
            ),
            "provenance_behavior": transition["provenance_behavior"],
            "temporal_behavior": transition["temporal_behavior"],
            "fanout": transition["observed_fanout"],
            "multiplicity_class": transition["multiplicity_class"],
            "hub_risk": transition["hub_policy"],
            "reverse_safety_classification": transition["phase6a1_directionality_class"],
            "financial_lifecycle_role": transition["financial_lifecycle_role"],
            "continuation_decision": {
                "may_continue": transition["may_continue_after_transition"],
                "reason": transition["terminal_rule"],
            },
            "evidence_sources_used_for_justification": transition["justification_evidence_sources"],
            "validation_gold_success_cited": False,
            "status": "PROPOSAL_ONLY",
        })
    return {
        "artifact_type": "graphrag_grammar_transition_justifications",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "transition_count": len(rows),
        "justifications": rows,
    }


def build_fanout_analysis(transitions: list[dict[str, Any]], excluded: list[dict[str, Any]]) -> dict[str, Any]:
    class_rows = []
    for transition_class in ("BACKBONE", "SUPPORTING", "CONTEXT", "TERMINAL_CONTEXT"):
        selected = [row for row in transitions if row["transition_class"] == transition_class]
        class_rows.append({
            "transition_class": transition_class,
            "directional_transition_count": len(selected),
            "frozen_relation_type_count": len({row["relation_id"] for row in selected}),
            "maximum_observed_out_degree": max((row["observed_fanout"]["maximum_out_degree"] for row in selected), default=0),
            "continuation_policy": (
                "NO" if transition_class == "TERMINAL_CONTEXT" else
                "ANCHOR_EXIT_ONLY_THEN_CONTINUE" if transition_class == "CONTEXT" else
                "TRANSITION_SPECIFIC" if transition_class == "BACKBONE" else "YES"
            ),
        })
    class_rows.append({
        "transition_class": "RESTRICTED_EXCLUDED",
        "directional_transition_count": len(excluded),
        "frozen_relation_type_count": len({row["relation_id"] for row in excluded}),
        "maximum_observed_out_degree": max(row["observed_fanout"]["maximum_out_degree"] for row in excluded),
        "continuation_policy": "NO",
    })
    invoice_gl = next(row for row in transitions if row["transition_id"] == "TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY")
    return {
        "artifact_type": "graphrag_grammar_fanout_analysis",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "degree_domain": "All persisted records of the current node type, including zero-degree records",
        "classification_definitions": {
            "LOW_FANOUT": "Observed directional maximum <=4; enumerate all exact edges deterministically.",
            "BOUNDED_FANOUT": "Observed direction remains structurally bounded but requires drift monitoring and independent review before any cap.",
            "HUB_RISK": "Observed or policy-defined hub behavior; exclude from ordinary traversal.",
            "POLICY_EXCLUDED": "Observed degree is bounded, but an explicit frozen node-hub prohibition still excludes traversal.",
            "TERMINAL_CONTEXT_ONLY": "May be gathered as local context but cannot expand further.",
        },
        "class_summary": class_rows,
        "proposed_transition_fanout": [{
            "transition_id": row["transition_id"],
            "relation_id": row["relation_id"],
            "direction": row["traversal_direction"],
            "current_node_type": row["current_node_type"],
            "next_node_type": row["next_node_type"],
            "multiplicity_class": row["multiplicity_class"],
            "statistics": row["observed_fanout"],
            "cap_status": row["multiplicity_policy"]["cap_status"],
            "transition_local_cap": row["multiplicity_policy"]["transition_local_cap"],
            "status": "PROPOSAL_ONLY",
        } for row in transitions],
        "excluded_transition_fanout": [{
            **row,
            "multiplicity_class": (
                "POLICY_EXCLUDED" if row["reason_code"] == "VENDOR_POLICY_OVERRIDES_BOUNDED_AUDIT_RELATION"
                else "HUB_RISK"
            ),
        } for row in excluded],
        "maximum_proposed_transition": {
            "transition_id": invoice_gl["transition_id"],
            "statistics": invoice_gl["observed_fanout"],
            "classification": "BOUNDED_FANOUT",
            "cap_status": "CAP_NOT_YET_FROZEN",
            "arbitrary_truncation_applied": False,
        },
        "result": "All proposed transitions have observed maximum directional fan-out <=8; Vendor/Employee directions remain excluded.",
    }


def risk(
    risk_id: str, name: str, inherent: str, residual: str, failure_mode: str,
    mitigation: str, freeze_question: str,
) -> dict[str, Any]:
    return {
        "risk_id": risk_id, "risk": name, "inherent_rating": inherent,
        "failure_mode": failure_mode, "mitigation": mitigation,
        "residual_rating": residual, "freeze_review_question": freeze_question,
        "status": "PROPOSAL_ONLY",
    }


def build_risk_register(simulation: dict[str, Any]) -> dict[str, Any]:
    risks = [
        risk("R01", "Graph explosion", "MEDIUM", "LOW", "Transition composition could multiply candidate paths.", "Explicit whitelist, depth 3, record-ID-simple paths, hub bans, full fanout enumeration, and a topology regression gate; an unexplained material increase is NEEDS_REVIEW, not a reason for metric-tuned pruning.", "Is the observed path distribution acceptably bounded under independent drift tests?"),
        risk("R02", "Hub leakage", "HIGH", "LOW", "Vendor, Employee, or context nodes could join unrelated transactions.", "No Vendor/Employee transition is executable; context nodes are terminal when reached and default-deny is enforced.", "Do tests prove all 14 excluded hub directions and actor/approver routes remain blocked?"),
        risk("R03", "Cycles", "HIGH", "LOW", "Bidirectional exact relations can oscillate or form longer loops.", "Reject a neighbor before enqueue when its record_id already appears in the path; depth remains three.", "Does the implementation reproduce the simple-path prohibition before expansion?"),
        risk("R04", "Temporal leakage", "MEDIUM", "LOW", "A path could disclose an endpoint or provenance record after the decision cutoff.", "Require source, target, persisted edge, and provenance-effective availability eligibility on every hop.", "Are all participant availability fields checked at each hop?"),
        risk("R05", "Semantic leakage", "LOW", "LOW", "Rules could encode RCA/failure concepts or semantic-neighbor expansion.", "Every transition is justified only by frozen operational fields and topology; semantic fallback is explicitly prohibited.", "Can every rule be justified without outcome language?"),
        risk("R06", "Validation overfitting", "HIGH", "LOW", "Transitions could be selected because of gold retrieval gains.", "Transition selection used registry semantics and label-independent topology only; structural coverage is reported after selection and never used as gold optimization.", "Can lineage demonstrate no validation gold or recall was accessed for design?"),
        risk("R07", "Ambiguity collapse", "MEDIUM", "LOW", "M:N or N:1 relations could be silently treated as 1:1.", "Enumerate all exact neighbors in deterministic order and retain every provenance record; do not use a cap as semantic cardinality.", "Are multiplicity cases preserved without first-match selection?"),
        risk("R08", "Provenance loss", "MEDIUM", "LOW", "A reached record could lose the operational explanation for its path.", "Persist transition, edge, relation/direction, provenance record/fields, cutoff outcome, node sequence, and path class for every hop.", "Does every candidate record retain all supporting path IDs after deduplication?"),
        risk("R09", "Production interpretability", "MEDIUM", "LOW", "Investigators could be unable to explain why a record was reached.", "Human-readable transition justifications plus one deduped evidence record and all supporting path ledgers.", "Can an investigator reconstruct each path from immutable operational fields?"),
        risk("R10", "Context bridge leakage", "HIGH", "LOW", "Approval or audit events could route into unrelated subjects or actors.", "Terminal-on-entry state; exact event anchors get one owner exit only; actor/Employee and Vendor exits are absent.", "Are reached-event continuation attempts rejected regardless of remaining depth?"),
        risk("R11", "GL source-type confusion", "MEDIUM", "LOW", "A GL source ID could resolve against the wrong operational node type.", "Require exact source_transaction_id plus the frozen transaction_type mapping and matching typed transition.", "Are mismatched or unknown transaction types rejected?"),
        risk("R12", "Fanout/data drift", "MEDIUM", "MEDIUM", "Future Invoice-to-GL degree could exceed the observed p99 7/max 8.", "Classify as BOUNDED_FANOUT, mark CAP_NOT_YET_FROZEN, apply no arbitrary truncation, and require freeze-time distribution regression.", "Should an independently justified deterministic cap be frozen after out-of-sample drift review?"),
        risk("R13", "Parallel payment representation", "MEDIUM", "LOW", "Direct projection and allocation-node paths could look like duplicate facts.", "Retain allocation provenance and multiple path IDs, globally deduplicate records, and label the explicit allocation bridge as the fuller lifecycle route.", "Should the already-frozen direct projection remain SUPPORTING executable or be removed in a later freeze decision?"),
        risk("R14", "Bank settlement limitation", "MEDIUM", "MEDIUM", "Bank anchors remain shallow because deterministic payment linkage is absent.", "Record RELATION_GAP and do not compensate with amount/date/account/currency heuristics; study Tier B separately.", "Is a separate, independently audited Tier-B experiment warranted?"),
        risk("R15", "Registry drift", "LOW", "LOW", "A changed parent artifact could silently alter semantics or topology.", "Pin and verify raw-byte SHA-256 for all authoritative parents before any design run.", "Does every freeze-review run pass the parent hash gate?"),
    ]
    return {
        "artifact_type": "graphrag_grammar_risk_register",
        "artifact_version": "1.1-draft", "status": "PROPOSAL_ONLY",
        "risk_scale": ["LOW", "MEDIUM", "HIGH"],
        "risk_count": len(risks),
        "residual_high_risk_count": sum(row["residual_rating"] == "HIGH" for row in risks),
        "topology_reference": {
            "candidate_path_count": simulation["candidate_path_count"],
            "candidate_paths_per_anchor": simulation["candidate_paths_per_anchor"],
            "cycles_prevented": simulation["cycles_prevented_by_simple_path"]["total"],
        },
        "risks": risks,
    }


def build_grammar(
    data: dict[str, Any], transitions: list[dict[str, Any]], excluded: list[dict[str, Any]],
    input_verification: dict[str, Any],
) -> dict[str, Any]:
    relation_rows = []
    used = {row["relation_id"] for row in transitions}
    for relation in sorted(data["relations"], key=lambda row: row["relation_type"]):
        relation_rows.append({
            "relation_id": relation["relation_type"],
            "source_node_type": relation["source_node_type"],
            "target_node_type": relation["target_node_type"],
            "parent_traversable": relation["traversable"],
            "parent_reverse_traversal": relation["reverse_traversal"],
            "grammar_disposition": "USED_BY_EXPLICIT_TYPED_TRANSITIONS" if relation["relation_type"] in used else "EXCLUDED_BY_HUB_POLICY",
            "proposed_directional_transition_count": sum(row["relation_id"] == relation["relation_type"] for row in transitions),
            "status": "PROPOSAL_ONLY",
        })
    return {
        "artifact_type": "graphrag_typed_financial_traversal_grammar",
        "artifact_version": "1.1-draft",
        "grammar_id": "GRAPH_TRAVERSAL_GRAMMAR_V1_1_DRAFT",
        "status": "PROPOSAL_ONLY",
        "not_frozen": True,
        "not_implemented": True,
        "design_scope": "Typed deterministic bounded navigation over persisted frozen operational graph edges",
        "default_deny": True,
        "parent_hash_verification": input_verification,
        "node_universe": list(NODE_TYPES),
        "node_type_count": len(NODE_TYPES),
        "frozen_relation_universe_count": len(data["relations"]),
        "frozen_relation_types_used_count": len(used),
        "frozen_relation_types_used": sorted(used),
        "directional_transition_count": len(transitions),
        "transition_class_counts": dict(sorted(Counter(row["transition_class"] for row in transitions).items())),
        "excluded_frozen_directional_transition_count": len(excluded),
        "excluded_frozen_relation_type_count": len({row["relation_id"] for row in excluded}),
        "relation_reuse": relation_rows,
        "transition_inclusion_rule": [
            "Underlying relation is one of the 22 frozen executable graph relations.",
            "Source and target types exactly agree with the frozen relation registry.",
            "Direction is frozen allowed and Phase 6A.1 classifies the exact relation as safely reversible where reverse is used.",
            "Traversal creates no new fact and retains operational provenance.",
            "Source, target, edge, and provenance-effective temporal eligibility remain enforceable.",
            "Vendor and Employee hub controls are not violated.",
            "No benchmark label, gold evidence, retrieval metric, failure class, or RCA concept justifies the transition.",
            "The transition has ordinary operational financial semantics.",
        ],
        "transition_class_definitions": {
            "BACKBONE": "Exact transaction, component, allocation, purchase-lifecycle, or accounting-source connectivity. Continuation is allowed except when a reached GL consequence is terminal.",
            "SUPPORTING": "Exact operational projection with explicit provenance that complements a more provenance-complete backbone route.",
            "CONTEXT": "Exact local event-to-owner anchor exit allowed only as hop 1; after reaching the owner, normal lifecycle transitions may compose.",
            "TERMINAL_CONTEXT": "Exact owner-to-event local evidence that terminates immediately.",
            "RESTRICTED": "A frozen edge direction recorded for audit but absent from the executable proposal because of hub or safety policy.",
        },
        "path_state_model": {
            "maximum_path_depth": 3,
            "path_identity": "case_id + exact resolved root + ordered transition IDs + edge IDs + record IDs",
            "simple_path_invariant": "record_id may appear at most once in one path",
            "initial_state": "EXACT_ANCHOR_AT_DEPTH_0",
            "normal_state": "LIFECYCLE_COMPOSITION_ALLOWED",
            "terminal_context_state": "STOP_IMMEDIATELY",
            "context_anchor_exception": "APPROVAL_EVENT or AUDIT_EVENT at depth 0 may take exactly one stored-direction owner transition at hop 1, then enter normal lifecycle state.",
            "gl_anchor_exception": "GL_ENTRY at depth 0 may take exactly one typed stored-direction source transition at hop 1, then enter normal lifecycle state.",
            "reached_gl_rule": "GL_ENTRY reached from a transaction is a terminal accounting consequence.",
            "empty_outgoing_node_types": ["BANK_STATEMENT", "EMPLOYEE", "VENDOR", "VENDOR_CHANGE"],
        },
        "stop_conditions": [
            "MAX_DEPTH_REACHED", "NO_ALLOWED_OUTGOING_TYPED_TRANSITION", "TERMINAL_CONTEXT_REACHED",
            "REACHED_GL_ACCOUNTING_CONSEQUENCE", "HUB_PROHIBITED_TRANSITION", "SIMPLE_PATH_VIOLATION",
            "TEMPORAL_INELIGIBILITY", "PROVENANCE_MISSING", "MULTIPLICITY_POLICY_REVIEW_STOP",
        ],
        "evidence_sufficiency_llm_stop_allowed": False,
        "candidate_path_priority_framework_for_future_review": {
            "implemented": False,
            "learned_weights": False,
            "gold_derived": False,
            "ordered_structural_groups": [
                "EXACT_ANCHOR",
                "SEMANTICALLY_COMPLETE_MULTI_HOP_BACKBONE_LIFECYCLE",
                "DIRECT_DETERMINISTIC_BACKBONE",
                "BACKBONE_WITH_EXACT_SUPPORTING_PROJECTION",
                "LOCAL_APPROVAL_OR_AUDIT_CONTEXT",
                "OTHER_EXPLICIT_BOUNDED_CONTEXT",
            ],
            "shorter_path_automatically_preferred": False,
            "note": "This is proposal metadata only; independent freeze review must decide ranking semantics without gold tuning.",
        },
        "multiplicity_and_budget_policy": {
            "enumeration": "Enumerate every exact edge in deterministic target/provenance/edge order unless a separately frozen cap applies.",
            "transition_local_caps": [],
            "bounded_transition_pending_cap_review": "TR_INVOICE__GL_SOURCE_INVOICE__REVERSE__GL_ENTRY",
            "bounded_transition_observed_maximum": 8,
            "cap_status": "CAP_NOT_YET_FROZEN",
            "max_raw_source_records_future_retrieval_budget_reference": 40,
            "source_record_selection_implemented_here": False,
        },
        "candidate_record_deduplication": {
            "record_key": "case_id + record_id",
            "output_semantics": "one candidate evidence record plus sorted unique supporting path IDs",
            "path_multiplicity_preserved": True,
            "direct_payment_projection_and_allocation_bridge_both_preserved": True,
        },
        "required_path_provenance": [
            "anchor_id", "node_sequence", "relation_sequence", "relation_direction_sequence",
            "edge_id_sequence", "provenance_record_id_and_fields_per_hop", "transition_id_sequence",
            "temporal_eligibility_per_hop", "path_depth", "path_class_sequence",
        ],
        "transitions": transitions,
        "unsupported_executable_transition_count": 0,
        "new_graph_edges_created": False,
        "new_relation_types_created": False,
        "new_node_types_created": False,
    }


def build_scientific_integrity(input_verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_type": "graphrag_phase6a2_scientific_integrity",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "integrity_status": "PASS",
        "parent_hash_gate": input_verification["status"],
        "phase5_artifacts_modified": False,
        "registry_v1_modified": False,
        "graph_v1_modified": False,
        "phase6a_artifacts_modified": False,
        "phase6a1_artifacts_modified": False,
        "new_operational_edge_types_created": False,
        "new_synthetic_node_types_created": False,
        "payment_bank_enabled": False,
        "synthetic_gl_journal_enabled": False,
        "tier_b_enabled": False,
        "semantic_fallback_enabled": False,
        "heldout_labels_opened": False,
        "heldout_gold_opened": False,
        "oracle_sources_opened": False,
        "validation_gold_used_for_transition_design": False,
        "validation_recall_used_to_select_transitions": False,
        "llm_calls_made": False,
        "api_calls_made": False,
        "new_embeddings_created": False,
        "graph_v1_1_implemented": False,
        "graph_v1_1_retrieval_evaluated": False,
        "graph_v1_1_recall_at_40_calculated": False,
        "graph_v1_1_full_evidence_coverage_calculated": False,
        "phase6b_started": False,
        "design_inputs": "Frozen registries, persisted deterministic graph topology, frozen route anchors, and Phase 6A.1 structural artifacts only.",
        "structural_coverage_is_not_retrieval_recall": True,
        "violation_policy": "BLOCK GRAPH v1.1 DESIGN REVIEW",
    }


def component_fingerprints(
    transitions: list[dict[str, Any]], excluded: list[dict[str, Any]],
    simulation: dict[str, Any], coverage: dict[str, Any], fanout: dict[str, Any],
) -> dict[str, str]:
    components = {
        "transition_set": transitions,
        "excluded_transition_set": excluded,
        "transition_ids": [row["transition_id"] for row in transitions],
        "structural_sequence_coverage": coverage,
        "candidate_path_set": {
            "count": simulation["candidate_path_count"],
            "sha256": simulation["candidate_path_set_sha256"],
        },
        "fanout_statistics": fanout,
        "prohibition_outcomes": {
            "hub_attempts_prevented": simulation["hub_attempts_prevented"],
            "terminal_stop_counts": simulation["terminal_stop_counts"],
            "terminal_stop_counts_by_transition_class_and_depth": simulation["terminal_stop_counts_by_transition_class_and_depth"],
            "no_allowed_transition_stop_counts": simulation["no_allowed_transition_stop_counts"],
            "temporal_rejection_counts": simulation["temporal_rejection_counts"],
            "provenance_rejection_counts": simulation["provenance_rejection_counts"],
            "exact_edge_or_type_rejection_counts": simulation["exact_edge_or_type_rejection_counts"],
            "multiplicity_policy_stop_count": simulation["multiplicity_policy_stop_count"],
        },
        "cycle_outcomes": simulation["cycles_prevented_by_simple_path"],
    }
    return {name: sha256_bytes((canonical(value) + "\n").encode("utf-8")) for name, value in components.items()}


def build_determinism_validation(
    first: dict[str, str], second: dict[str, str],
) -> dict[str, Any]:
    comparisons = {
        name: {"run_1_sha256": first[name], "run_2_sha256": second[name], "identical": first[name] == second[name]}
        for name in sorted(first)
    }
    return {
        "artifact_type": "graphrag_phase6a2_determinism_validation",
        "artifact_version": "1.1-draft", "status": "PROPOSAL_ONLY",
        "analysis_run_count": 2,
        "simulation_run_count": 2,
        "comparison_scope": "Canonical serialization excluding runtime metadata; no runtime metadata is persisted.",
        "components": comparisons,
        "transition_sets_identical": comparisons["transition_set"]["identical"],
        "transition_ids_identical": comparisons["transition_ids"]["identical"],
        "structural_sequence_coverage_identical": comparisons["structural_sequence_coverage"]["identical"],
        "path_sets_identical": comparisons["candidate_path_set"]["identical"],
        "fanout_statistics_identical": comparisons["fanout_statistics"]["identical"],
        "prohibition_outcomes_identical": comparisons["prohibition_outcomes"]["identical"],
        "determinism_status": "PASS" if all(row["identical"] for row in comparisons.values()) else "FAIL",
    }


def readiness_gates(
    input_verification: dict[str, Any], grammar: dict[str, Any], coverage: dict[str, Any],
    simulation: dict[str, Any], determinism: dict[str, Any], risks: dict[str, Any],
    integrity: dict[str, Any], transition_matrix: dict[str, Any], node_matrix: dict[str, Any],
    forbidden: dict[str, Any], motif_mapping: dict[str, Any], justifications: dict[str, Any],
) -> list[dict[str, Any]]:
    required_forbidden_ids = {
        "FT_DEFAULT_DENY_BFS", "FT_VENDOR_BRIDGE", "FT_EMPLOYEE_BRIDGE", "FT_PAYMENT_BANK",
        "FT_SYNTHETIC_GL_JOURNAL", "FT_SEMANTIC_SIMILARITY", "FT_SAME_CURRENCY",
        "FT_SAME_AMOUNT", "FT_SAME_DATE", "FT_SAME_ACCOUNT", "FT_REPEATED_RECORD",
        "FT_DEPTH_GT_3", "FT_CONTEXT_BRIDGE", "FT_REACHED_GL_CONTINUATION",
    }
    actual_forbidden_ids = {row["forbidden_id"] for row in forbidden["forbidden_patterns"]}
    integrity_false_fields = (
        "phase5_artifacts_modified", "registry_v1_modified", "graph_v1_modified",
        "phase6a_artifacts_modified", "phase6a1_artifacts_modified",
        "new_operational_edge_types_created", "new_synthetic_node_types_created",
        "payment_bank_enabled", "synthetic_gl_journal_enabled", "tier_b_enabled",
        "semantic_fallback_enabled", "heldout_labels_opened", "heldout_gold_opened",
        "oracle_sources_opened", "validation_gold_used_for_transition_design",
        "validation_recall_used_to_select_transitions", "llm_calls_made", "api_calls_made",
        "new_embeddings_created", "graph_v1_1_implemented", "graph_v1_1_retrieval_evaluated",
    )
    phase6a1_comparison = simulation["phase6a1_safe_topology_comparison"]
    exact_topology_match = (
        simulation["candidate_path_count"] == 13371
        and simulation["paths_by_exact_depth"] == {"1": 3332, "2": 4477, "3": 5562}
        and simulation["candidate_paths_per_anchor"]["p50_nearest_rank"] == 31
        and simulation["candidate_paths_per_anchor"]["p95_nearest_rank"] == 68
        and simulation["candidate_paths_per_anchor"]["p99_nearest_rank"] == 78
        and simulation["candidate_paths_per_anchor"]["maximum"] == 91
        and phase6a1_comparison["path_count_delta"] == 0
        and phase6a1_comparison["cycle_control_equivalent_total"] == 8433
    )
    full_coverage = (
        coverage["overall"]["represented_sequence_count"] == 76
        and coverage["overall"]["safe_sequence_count"] == 76
        and coverage["excluded_sequence_count"] == 0
        and all(
            row["represented_sequence_count"] == row["safe_sequence_count"]
            for row in coverage["by_depth"].values()
        )
        and all(
            values["overall"]["represented_sequence_count"] == values["overall"]["safe_sequence_count"]
            for values in coverage["by_anchor_type"].values()
        )
    )
    gate_specs = [
        ("GATE_1_LINEAGE_AND_INTEGRITY", input_verification["status"] == "PASS" and integrity["integrity_status"] == "PASS" and all(integrity[field] is False for field in integrity_false_fields), f"{input_verification['verified_check_count']} parent raw-byte checks over {input_verification['verified_distinct_path_count']} distinct paths passed; every mandated scientific-integrity flag is false."),
        ("GATE_2_UNIVERSE_AND_RELATION_REUSE", grammar["node_type_count"] == 14 and set(grammar["node_universe"]) == set(NODE_TYPES) and grammar["frozen_relation_universe_count"] == 22 and grammar["frozen_relation_types_used_count"] == 15 and grammar["unsupported_executable_transition_count"] == 0 and not grammar["new_graph_edges_created"] and not grammar["new_relation_types_created"] and not grammar["new_node_types_created"], "Exactly the 14 frozen node types and 15 of 22 frozen relations are used; no unsupported transition, graph edge, relation type, or node type is introduced."),
        ("GATE_3_TYPED_DIRECTION_SAFETY", grammar["directional_transition_count"] == 30 and len({row["transition_id"] for row in grammar["transitions"]}) == 30 and all(row["parent_relation_traversable"] and row["parent_relation_reverse_traversal"] and row["phase6a1_directionality_class"] == "SAFE_REVERSIBLE_CANDIDATE" for row in grammar["transitions"]) and grammar["excluded_frozen_directional_transition_count"] == 14 and any(row["relation_id"] == "AUDIT_EVENT_FOR_VENDOR" for row in forbidden["excluded_frozen_directional_transitions"]), "Thirty unique typed rows are frozen-permitted and Phase 6A.1-safe; all 14 Vendor/Employee directions remain excluded, including AUDIT_EVENT_FOR_VENDOR."),
        ("GATE_4_STATE_AND_HUB_SAFETY", grammar["default_deny"] and grammar["path_state_model"]["maximum_path_depth"] == 3 and grammar["path_state_model"]["simple_path_invariant"] == "record_id may appear at most once in one path" and required_forbidden_ids <= actual_forbidden_ids and set(grammar["path_state_model"]["empty_outgoing_node_types"]) == {"BANK_STATEMENT", "EMPLOYEE", "VENDOR", "VENDOR_CHANGE"} and simulation["cycles_prevented_by_simple_path"]["total"] > 0 and simulation["terminal_stop_counts_by_transition_class_and_depth"] and simulation["hub_attempts_prevented"]["path_state_occurrence_count"] > 0 and simulation["hub_attempts_prevented"]["vendor_or_employee_node_entry_count"] == 0, "Default deny, depth 3, simple paths, terminal event/GL states, explicit hub/payment-bank/GL_JOURNAL prohibitions, and four empty hub/gap node sets are machine-checked; no Vendor/Employee node is entered."),
        ("GATE_5_PROVENANCE_TEMPORAL_CARDINALITY", all(row["requires_provenance"] and row["requires_cutoff_eligibility"] and row["requires_exact_edge"] and row["operational_field_provenance"]["field_orientation"] == "FROZEN_STORED_EDGE" and row["multiplicity_policy"]["policy"] == "ENUMERATE_ALL_EXACT_EDGES_DETERMINISTICALLY" for row in grammar["transitions"]) and simulation["temporal_rejection_counts"] == {} and simulation["provenance_rejection_counts"] == {} and simulation["exact_edge_or_type_rejection_counts"] == {}, "Every row requires an exact typed edge, explicit stored/current/next field provenance, cutoff eligibility, and deterministic full-neighbor enumeration; the persisted simulation has zero provenance/type/temporal violations."),
        ("GATE_6_BOUNDEDNESS_AND_DETERMINISM", determinism["determinism_status"] == "PASS" and all(row["identical"] for row in determinism["components"].values()) and exact_topology_match and not phase6a1_comparison["major_unexplained_increase"], "Two canonical simulations agree on every fingerprint; totals and depth counts exactly match Phase 6A.1, p50/p95/p99/max remain 31/68/78/91, and cycle controls reconcile to 8,433."),
        ("GATE_7_EXPRESSIVENESS_AND_INDEPENDENCE", full_coverage and coverage["gold_evidence_used"] is False and coverage["not_required_document_recall"] is True, "Structural sequence coverage is exactly 76/76 overall, complete at every depth and anchor type, with zero exclusions and no gold evidence or retrieval metric."),
        ("GATE_8_PACKAGE_AND_RESIDUAL_RISK", transition_matrix["row_count"] == 30 and node_matrix["node_type_count"] == 14 and len({row["node_type"] for row in node_matrix["node_types"]}) == 14 and motif_mapping["mapped_frozen_motif_count"] == 8 and motif_mapping["mapped_excluded_motif_count"] == 2 and len(motif_mapping["mappings"]) == 10 and justifications["transition_count"] == 30 and required_forbidden_ids <= actual_forbidden_ids and risks["residual_high_risk_count"] == 0, "Transition, 14-node, forbidden, 8+2 motif, 30-justification, and risk design objects are complete, and no HIGH residual risk remains."),
    ]
    return [{
        "gate_id": gate_id, "result": "GO" if passed else "NOT_GO",
        "passed": passed, "evidence": evidence, "status": "PROPOSAL_ONLY",
    } for gate_id, passed, evidence in gate_specs]


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    output = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        output.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return output


def pct(value: float) -> str:
    return f"{value * 100:.3f}%"


def build_report(
    input_verification: dict[str, Any], grammar: dict[str, Any], transition_matrix: dict[str, Any],
    node_matrix: dict[str, Any], forbidden: dict[str, Any], motif_mapping: dict[str, Any],
    fanout: dict[str, Any], coverage: dict[str, Any], simulation: dict[str, Any],
    risks: dict[str, Any], integrity: dict[str, Any], determinism: dict[str, Any],
    gates: list[dict[str, Any]],
) -> str:
    transitions = grammar["transitions"]
    class_summary = fanout["class_summary"]
    distribution = simulation["candidate_paths_per_anchor"]
    unique_distribution = simulation["unique_records_reached_including_anchors"]
    cycles = simulation["cycles_prevented_by_simple_path"]
    comparison = simulation["phase6a1_safe_topology_comparison"]
    final_go = all(row["passed"] for row in gates) and integrity["integrity_status"] == "PASS"
    decision = (
        "RECOMMEND 8/8 GO FOR GRAPH v1.1 TYPED GRAMMAR REGISTRY FREEZE REVIEW"
        if final_go else "RECOMMEND REVISE GRAPH v1.1 TYPED GRAMMAR DESIGN BEFORE FREEZE"
    )
    lines = [
        "# Phase 6A.2 — GraphRAG v1.1 Typed Financial Traversal Grammar Design Review",
        "",
        "`status = PROPOSAL_ONLY`",
        "",
        "This package is a design and label-independent structural review. It is not a frozen registry, retriever implementation, retrieval evaluation, or Phase 6B authorization.",
        "",
        "## A. Executive recommendation",
        "",
        f"Recommend independent registry-freeze review of a default-deny grammar with **{grammar['directional_transition_count']} typed directional transitions** over **{grammar['frozen_relation_types_used_count']} already-frozen relation types**. It represents **{coverage['overall']['represented_sequence_count']}/{coverage['overall']['safe_sequence_count']} ({pct(coverage['overall']['structural_sequence_coverage'])})** Phase 6A.1 safe typed sequences while reproducing the bounded 416-route topology profile: {simulation['candidate_path_count']:,} paths and maximum {distribution['maximum']} paths per route case.",
        "",
        "The recommendation is only readiness for independent freeze review. It does not freeze or implement Graph v1.1 and makes no claim about retrieval accuracy.",
        "",
        "## B. Parent hash verification",
        "",
        f"The pre-design gate passed **{input_verification['verified_check_count']}/{input_verification['verified_check_count']}** raw-byte checks over **{input_verification['verified_distinct_path_count']} distinct paths**. The Phase 6A.1 report is intentionally checked twice: once against the prompt-pinned digest and again through its inventory. The gate includes the Phase 6A.1 hash inventory, every artifact and analysis script named by it, all five frozen v1 registries, persisted nodes and edges, anchor resolutions, and validation routes.",
        "",
    ]
    primary_rows = []
    checks_by_path = {row["path"]: row for row in input_verification["checks"]}
    for path, expected in sorted(EXPECTED_PRIMARY_HASHES.items(), key=lambda item: item[0].as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        row = checks_by_path[relative]
        primary_rows.append((relative, expected, row["observed_sha256"], row["status"]))
    lines.extend(markdown_table(["Authoritative input", "Expected SHA-256", "Observed SHA-256", "Result"], primary_rows))
    lines.extend([
        "",
        "No parent artifact was reconstructed or altered.",
        "",
        "## C. Why fixed motifs were insufficient",
        "",
        "Graph v1.0 froze eight complete motifs: seven one-hop, one two-hop, and no three-hop motif. Phase 6A.1 found 76 safe direction-aware typed sequences, but only five were represented (6.579%). Its sole two-hop motif failed every eligible Invoice-origin attempt because the first reverse edge expected a Purchase Order current node. The graph contained the needed exact relations; the complete-path motif contract could not compose them from the actual current type.",
        "",
        "The earlier recall figures are motivation only. They were not rerun, inspected at record level, or used to select a transition.",
        "",
        "## D. Typed grammar design principles",
        "",
        "The proposed lookup key is `(current node type, frozen relation, direction, next node type, depth, path state)`. Missing rows are denied. Every accepted hop must correspond to one persisted exact edge, preserve its operational provenance, pass temporal eligibility, respect the depth-three/simple-path rules, and obey terminal/hub state controls. Independently valid rows can compose; no complete motif and no unrestricted BFS is required.",
        "",
        "The transition inventory was frozen in-memory from registry semantics and Phase 6A.1 safety classes before structural coverage was calculated. Gold outcomes, failure labels, evidence contracts, and retrieval metrics were not design inputs.",
        "",
        "## E. Frozen relation reuse",
        "",
        f"The operational graph remains unchanged at 22 frozen executable relations. The grammar uses {grammar['frozen_relation_types_used_count']} relations with traversal and reverse traversal already frozen true. Seven relations remain present for provenance but supply no grammar row: six Vendor/Employee hub relations plus `AUDIT_EVENT_FOR_VENDOR`, where the explicit Vendor policy overrides its bounded degree.",
        "",
    ])
    relation_rows = [
        (row["relation_id"], f"{row['source_node_type']} → {row['target_node_type']}", row["grammar_disposition"], row["proposed_directional_transition_count"])
        for row in grammar["relation_reuse"]
    ]
    lines.extend(markdown_table(["Frozen relation", "Stored types", "Grammar disposition", "Directional rows"], relation_rows))
    lines.extend([
        "",
        "## F. Proposed transition inventory",
        "",
    ])
    summary_rows = []
    display_names = {
        "BACKBONE": "Backbone", "SUPPORTING": "Supporting", "CONTEXT": "Context",
        "TERMINAL_CONTEXT": "Terminal context", "RESTRICTED_EXCLUDED": "Restricted/excluded",
    }
    for row in class_summary:
        summary_rows.append((
            display_names[row["transition_class"]], row["directional_transition_count"],
            row["frozen_relation_type_count"], row["maximum_observed_out_degree"], row["continuation_policy"],
        ))
    lines.extend(markdown_table(["Transition class", "Proposed/excluded count", "Frozen relations used", "Max observed fan-out", "Continue allowed?"], summary_rows))
    lines.extend(["", "The 30 executable proposal rows are:", ""])
    transition_rows = [
        (row["transition_id"], row["transition_class"], row["multiplicity_class"], row["observed_fanout"]["maximum_out_degree"], "Yes" if row["may_continue_after_transition"] else "No")
        for row in transitions
    ]
    lines.extend(markdown_table(["Transition ID", "Class", "Multiplicity", "Max", "Continue"], transition_rows))
    lines.extend([
        "",
        "## G. Transition classes",
        "",
        "`BACKBONE` connects the purchase, invoice, allocation, payment, and typed accounting lifecycle. `SUPPORTING` is the exact Payment↔Invoice projection whose edge retains a specific allocation record. `CONTEXT` is a stored-direction event-anchor exit allowed only at hop 1. `TERMINAL_CONTEXT` gathers a local event from its owning entity and stops. `RESTRICTED` records a frozen relation direction that the executable grammar does not expose.",
        "",
        "### Node-level grammar summary",
        "",
    ])
    transition_by_id = {row["transition_id"]: row for row in transitions}
    for node in node_matrix["node_types"]:
        lines.extend([f"#### {node['node_type']}", "", "Allowed:"])
        if node["allowed_outgoing_transition_ids"]:
            for transition_id_value in node["allowed_outgoing_transition_ids"]:
                row = transition_by_id[transition_id_value]
                lines.append(f"- `{row['relation_id']}:{row['traversal_direction'].lower()}` → `{row['next_node_type']}` ({row['transition_class']}; {'may continue' if row['may_continue_after_transition'] else 'terminal'}).")
        else:
            lines.append("- None; the transition set is explicitly empty.")
        lines.extend(["", "Terminal/context:"])
        if node["terminal_context_transition_ids"]:
            lines.append("- Terminal context: " + ", ".join(f"`{value}`" for value in node["terminal_context_transition_ids"]) + ".")
        if node["terminal_accounting_consequence_transition_ids"]:
            lines.append("- Terminal accounting consequence: " + ", ".join(f"`{value}`" for value in node["terminal_accounting_consequence_transition_ids"]) + ".")
        if node["anchor_exit_only_transition_ids"]:
            lines.append("- Exact-anchor hop-1 exit only: " + ", ".join(f"`{value}`" for value in node["anchor_exit_only_transition_ids"]) + ".")
        if node["reached_node_state_override"] != "NONE":
            lines.append(f"- `{node['reached_node_state_override']}`.")
        elif not node["noncontinuing_transition_ids"] and not node["anchor_exit_only_transition_ids"]:
            lines.append("- No node-level terminal override; individual transition rules still apply.")
        lines.extend([
            "", "Prohibited:",
            "- " + ", ".join(f"`{value}`" for value in node["prohibited_pattern_ids"]) + ".",
            "", f"Maximum reachable depth from an exact anchor: **{node['maximum_reachable_depth_from_exact_anchor']}**.",
            "", f"Reasoning: {node['reasoning']}", "",
        ])
    lines.extend([
        "## H. Backbone financial lifecycle grammar",
        "",
        "The 18 BACKBONE rows are both orientations of nine exact relations: PO header/line, Invoice/PO, InvoiceLine/POLine, Invoice/InvoiceLine, PaymentAllocation/Payment, PaymentAllocation/Invoice, and three typed GL source relations. These rows permit legitimate components to compose without authoring every complete path. A reached GL_ENTRY is the deliberate exception to ordinary backbone continuation.",
        "",
        "## I. Payment-allocation design",
        "",
        "`PAYMENT_ALLOCATION` remains the provenance-complete bridge: `INVOICE ↔ PAYMENT_ALLOCATION ↔ PAYMENT`. Both allocation edges retain `payment_id`, `invoice_id`, edge ID, and allocation record. The already-frozen `PAYMENT_ALLOCATED_TO_INVOICE` projection is not invented; its two SUPPORTING rows require the same PAYMENT_ALLOCATION provenance. Candidate records are globally deduplicated while every supporting path stays visible. Whether that projection should remain executable is an explicit freeze-review question, not an outcome-tuned choice.",
        "",
        "## J. GL source-transaction design",
        "",
        "Three typed relation pairs connect GL_ENTRY only to BANK_TRANSACTION, INVOICE, or PAYMENT. Every hop requires exact `(transaction_type, source_transaction_id)`, the frozen type mapping, type agreement, provenance, and cutoff eligibility. A GL_ENTRY anchor may use one stored-direction source row at hop 1 and continue from the source. A GL_ENTRY reached from a transaction is terminal. `GL_JOURNAL`, journal grouping, fuzzy source IDs, and account-based expansion remain prohibited.",
        "",
        "## K. Purchase-order / invoice design",
        "",
        "Exact PO, PO line, Invoice, and Invoice line relationships can compose in either safely frozen direction. This naturally represents PO→Invoice→Payment and line-level chains when the constituent edges exist; it does not assume or synthesize any missing relation. Vendor and creator-Employee joins are not available to the grammar.",
        "",
        "## L. Approval-event policy",
        "",
        "Invoice→ApprovalEvent is TERMINAL_CONTEXT and enumerates all exact local events (observed maximum four). An exact ApprovalEvent anchor may take one stored-direction hop to its owning Invoice, then normal lifecycle rules apply. No approver-to-Employee path exists.",
        "",
        "## M. Audit-event policy",
        "",
        "Operational entity→AuditEvent rows are TERMINAL_CONTEXT for Bank Transaction, Invoice, Payment, and Purchase Order. An exact AuditEvent anchor may take one typed stored-direction owner hop before entering the lifecycle. Actor identity, Vendor audit traversal, and `gl_journal` remain prohibited, so audit evidence cannot bridge subjects.",
        "",
        "## N. Vendor and Employee hub policy",
        "",
        f"All {grammar['excluded_frozen_directional_transition_count']} orientations of seven Vendor/Employee relations are excluded. The strongest observed excluded maxima are Vendor→Invoice 592, Vendor→PO 362, Vendor→Payment 217, Employee→VendorChange 146, and Employee→PO 63. `AUDIT_EVENT_FOR_VENDOR` remains excluded despite maximum Vendor→AuditEvent degree one because an exception would change the frozen Vendor policy. Vendor, Employee, and VendorChange have explicit empty outgoing sets.",
        "",
        "## O. Bank-transaction limitation",
        "",
        "**KNOWN STRUCTURAL LIMITATION — BANK SETTLEMENT LINKAGE EXCLUDED.** Bank Transaction anchors have only exact GL consequences and local Audit Events and therefore remain shallow. No PAYMENT↔BANK_TRANSACTION relation is frozen. The proposal does not compensate with amount, date, currency, account, text, embedding, or nearest-match heuristics; a future Tier-B experiment would require separate authorization and audit.",
        "",
        "A second, non-required relation gap is recorded for BANK_STATEMENT→BANK_TRANSACTION membership/reconciliation. Because no such frozen relation exists, BANK_STATEMENT has an explicit empty set; v1.1 neither requires nor synthesizes this navigation.",
        "",
        "## P. Cycle prevention",
        "",
        f"Every path is record-ID-simple and rejects a repeat before enqueue. The simulator rejected {cycles['total']:,} allowed-transition repeat attempts ({', '.join(f'{key}={value:,}' for key, value in cycles['by_attempted_depth'].items())}). Terminal-state checks avoided another {comparison['terminal_return_candidates_stopped_before_adjacency_lookup']:,} one-edge returns before adjacency lookup: {comparison['context_event_return_candidates_stopped']:,} event returns and {comparison['reached_gl_return_candidates_stopped']:,} reached-GL returns. Together these controls account for {comparison['cycle_control_equivalent_total']:,}, matching Phase 6A.1's 8,433 repeated-record candidates despite the different stop-order counter definition.",
        "",
        "## Q. Depth policy",
        "",
        "`MAX_PATH_DEPTH = 3`. Every accepted prefix is retained by exact depth so later research can separate direct, depth-two, and depth-three evidence. No fourth edge is proposed. Whether depth three's incremental evidence value justifies its complexity is reserved for a future independently authorized retrieval evaluation.",
        "",
        "## R. Multiplicity and fan-out",
        "",
        f"Every proposed direction reports degree over all records of its current type, including zeros, with mean, median, nearest-rank p95/p99, and maximum. All proposed maxima are at most eight. `{fanout['maximum_proposed_transition']['transition_id']}` is the only BOUNDED_FANOUT row: mean {fanout['maximum_proposed_transition']['statistics']['mean_out_degree']:.6f}, median {fanout['maximum_proposed_transition']['statistics']['median_out_degree']}, p95 {fanout['maximum_proposed_transition']['statistics']['p95_out_degree']}, p99 {fanout['maximum_proposed_transition']['statistics']['p99_out_degree']}, max {fanout['maximum_proposed_transition']['statistics']['maximum_out_degree']}. It is `CAP_NOT_YET_FROZEN`; this draft applies no arbitrary truncation. Multiplicity remains semantic cardinality, not a ranking device.",
        "",
        "The future 40-record selection budget is distinct from traversal. This simulation selects no evidence and permits candidate sets above 40.",
        "",
        "## S. Forbidden transitions",
        "",
    ])
    for entry in forbidden["forbidden_patterns"]:
        lines.append(f"- `{entry['forbidden_id']}` — {entry['pattern']}. {entry['rationale']}")
    lines.extend([
        "",
        "## T. Structural sequence coverage",
        "",
        f"Overall STRUCTURAL_SEQUENCE_COVERAGE is **{coverage['overall']['represented_sequence_count']}/{coverage['overall']['safe_sequence_count']} ({pct(coverage['overall']['structural_sequence_coverage'])})**, compared with the immutable v1 motif context of 5/76 (6.579%). A sequence counts only when its exact typed/directional transition sequence passes the draft state rules and is emitted at least once in the 416-route topology simulation. It is counted once, not weighted by cases or path instances.",
        "",
    ])
    depth_rows = [
        (depth, row["represented_sequence_count"], row["safe_sequence_count"], pct(row["structural_sequence_coverage"]))
        for depth, row in coverage["by_depth"].items()
    ]
    lines.extend(markdown_table(["Exact depth", "Represented", "Safe denominator", "Coverage"], depth_rows))
    lines.extend(["", "By Phase 6A.1 route anchor type:", ""])
    anchor_rows = []
    for anchor_type, value in coverage["by_anchor_type"].items():
        overall = value["overall"]
        anchor_rows.append((anchor_type, overall["represented_sequence_count"], overall["safe_sequence_count"], pct(overall["structural_sequence_coverage"])))
    lines.extend(markdown_table(["Anchor type", "Represented", "Safe denominator", "Coverage"], anchor_rows))
    lines.extend([
        "",
        "`gl_journal` in this table is the immutable route-label category whose exact resolutions are GL_ENTRY records; it is not a graph node type and does not authorize `GL_JOURNAL`.",
        "",
        f"Excluded safe sequence count: **{coverage['excluded_sequence_count']}**. No legitimate observed safe sequence is omitted; this result follows from the pre-justified transition inventory and is not a target optimized against gold.",
        "",
        "## U. Topology-simulation boundedness",
        "",
        f"The label-independent simulation used 416 frozen route cases and {simulation['resolved_root_count']} exact resolved graph roots. It emitted {simulation['candidate_path_count']:,} accepted path prefixes: depth 1 = {simulation['paths_by_exact_depth']['1']:,}, depth 2 = {simulation['paths_by_exact_depth']['2']:,}, depth 3 = {simulation['paths_by_exact_depth']['3']:,}. Per route case: mean {distribution['mean']:.3f}, p50 {distribution['p50_nearest_rank']}, p75 {distribution['p75_nearest_rank']}, p90 {distribution['p90_nearest_rank']}, p95 {distribution['p95_nearest_rank']}, p99 {distribution['p99_nearest_rank']}, max {distribution['maximum']}. This exactly matches the Phase 6A.1 safe path counts and has no unexplained expansion.",
        "",
        f"Unique records including anchors per route case: mean {unique_distribution['mean']:.3f}, p50 {unique_distribution['p50_nearest_rank']}, p75 {unique_distribution['p75_nearest_rank']}, p90 {unique_distribution['p90_nearest_rank']}, p95 {unique_distribution['p95_nearest_rank']}, p99 {unique_distribution['p99_nearest_rank']}, max {unique_distribution['maximum']}. {simulation['candidate_record_deduplication_design']['cases_with_more_than_40_unique_records_including_anchors']} cases exceed the future 40-record selection reference, which is allowed because no selection is performed here.",
        "",
        f"The maximum-degree responsible transition is `{simulation['max_degree_transition_responsible']['transition_ids'][0]}` at {simulation['max_degree_transition_responsible']['maximum_observed_out_degree']}. The absent hub rows prevented {simulation['hub_attempts_prevented']['path_state_occurrence_count']:,} prohibited path-state edge incidences across the reachable frontier; no Vendor or Employee node was entered. The candidate path-set digest is `{simulation['candidate_path_set_sha256']}`.",
        "",
        f"Accepted emitted paths contain **{simulation['transition_exercise']['accepted_path_transition_count']}/{simulation['transition_exercise']['proposed_transition_count']}** proposed row IDs. The other {simulation['transition_exercise']['not_present_in_accepted_paths_count']} IDs are the five event-anchor exits plus three exact directions that do not survive into accepted paths for this route set. A missing ID may still have been considered at a frontier and rejected by the simple-path or another later rule. Those rows remain justified by frozen semantics, Phase 6A.1 directionality safety, and graph-global fan-out; 76/76 sequence coverage must not be read as accepted-path exercise of every proposed row.",
        "",
        "## V. Mapping from v1 motifs to v1.1 grammar",
        "",
        "The eight frozen v1 motifs remain immutable. The mapping is compatibility documentation, not deletion or migration. Exact typed rows fully represent the seven one-hop motifs; the GL wildcard decomposes into three typed rows; and PO_INVOICE_LINES becomes ordinary composition whose direction is selected from the current type. The two already-excluded payment-bank motifs remain intentionally unrepresentable.",
        "",
    ])
    motif_rows = [
        (row["motif_id"], row["v1_registry_group"], row["representability"], row["direction_status"])
        for row in motif_mapping["mappings"]
    ]
    lines.extend(markdown_table(["v1 motif", "Registry group", "v1.1 representability", "Direction/status"], motif_rows))
    lines.extend([
        "",
        "## W. Risk register",
        "",
    ])
    risk_rows = [(row["risk_id"], row["risk"], row["inherent_rating"], row["residual_rating"], row["mitigation"]) for row in risks["risks"]]
    lines.extend(markdown_table(["ID", "Risk", "Inherent", "Residual", "Mitigation"], risk_rows))
    lines.extend([
        "",
        f"No HIGH residual risk remains. Two MEDIUM residual questions are deliberately carried into freeze review: drift/cap governance for Invoice→GL_ENTRY and the known absence of deterministic bank-settlement linkage.",
        "",
        "## X. Scientific-integrity audit",
        "",
        f"Integrity status is **{integrity['integrity_status']}**. No Phase 5, registry v1, Graph v1, Phase 6A, or Phase 6A.1 artifact was modified. No relation or node type was created. Payment-bank, Tier B, semantic fallback, and synthetic GL_JOURNAL remain disabled. No held-out labels, held-out gold, oracle sources, validation gold, retrieval recall, LLM, API, or new embedding was used. Graph v1.1 was neither implemented nor evaluated.",
        "",
        f"Determinism status is **{determinism['determinism_status']}**: two independent in-process structural runs produced identical transition sets and IDs, structural coverage, path-set digest, fanout statistics, cycle outcomes, and prohibition outcomes.",
        "",
        "## Y. Differences from Graph v1.0",
        "",
        "Graph v1.0 executes immutable complete motifs and cannot compose arbitrary approved steps. This v1.1 draft proposes a separate state-transition architecture whose rows are typed, directional, provenance-aware, cutoff-aware, default-deny, depth-bounded, and simple-path constrained. It preserves all v1 graph and motif artifacts, adds no operational fact, implements no ranking or record selection, and retains complete path explanations for future deduplication.",
        "",
        "The future primary empirical question—outside this phase—is: **Does bounded typed multi-hop traversal add evidence recovery beyond exact one-hop relational expansion?** Relational-RAG remains the benchmark; this design does not recalculate or compare retrieval performance.",
        "",
        "## Z. Recommendation for freeze",
        "",
        "### Research questions",
        "",
        f"- **Q1 — More complete than 6.579% motif coverage? YES.** The draft structurally represents {coverage['overall']['represented_sequence_count']}/{coverage['overall']['safe_sequence_count']} safe sequences ({pct(coverage['overall']['structural_sequence_coverage'])}) versus 5/76.",
        "- **Q2 — Without generic BFS? YES.** Exactly 30 typed rows are whitelisted; every absent edge/type/direction combination is denied.",
        f"- **Q3 — Bounded at depth three with simple paths? YES.** The 416-route simulation remains {simulation['candidate_path_count']:,} paths with p99 {distribution['p99_nearest_rank']} and max {distribution['maximum']}.",
        "- **Q4 — Transactional backbone?** PO header/line, Invoice/PO, InvoiceLine/POLine, Invoice/InvoiceLine, allocation/Payment, allocation/Invoice, and the three typed GL-source relation pairs.",
        "- **Q5 — Terminal context?** ApprovalEvent and AuditEvent are terminal when reached; a reached GL_ENTRY is a terminal accounting consequence. Vendor, Employee, BankStatement, and VendorChange have no outgoing rows.",
        "- **Q6 — Necessary reverse traversals?** Reverse component/header, PO/Invoice, line, allocation, Payment projection, transaction→GL consequence, and entity→local event directions. Each is already frozen reverse-permitted and exact.",
        "- **Q7 — Unsupported executable transition? NO.** Every proposed row uses an already-frozen deterministic relation.",
        "- **Q8 — Deterministic traversal separated from Tier B matching? YES.** Payment-bank and all heuristic matching remain disabled relation gaps.",
        "- **Q9 — Every path operationally explainable? YES.** The path contract retains exact nodes, edges, directions, transition IDs, provenance fields/records, temporal outcomes, depth, and class.",
        "- **Q10 — Ready for independent freeze review without gold evaluation? YES.** All eight readiness gates pass; no retrieval implementation or gold performance evaluation occurred.",
        "",
        "### Eight readiness gates",
        "",
    ])
    lines.extend(markdown_table(["Gate", "Result", "Evidence"], [(row["gate_id"], row["result"], row["evidence"]) for row in gates]))
    lines.extend([
        "",
        "Freeze review should specifically decide whether the frozen direct Payment↔Invoice projection remains executable SUPPORTING evidence and whether a later drift study justifies a deterministic cap for Invoice→GL_ENTRY. Neither question blocks this structural proposal, and neither is decided from retrieval outcomes.",
        "",
        decision,
    ])
    return "\n".join(lines) + "\n"


def load_data() -> dict[str, Any]:
    node_registry = load_json(FREEZE / "graph_node_registry_v1.json")
    relation_registry = load_json(FREEZE / "graph_relation_registry_v1.json")
    motifs = load_json(FREEZE / "graph_path_motifs_v1.json")
    nodes_list = load_jsonl(PHASE6A / "graph/nodes.jsonl")
    edges = load_jsonl(PHASE6A / "graph/edges.jsonl")
    resolutions = load_jsonl(PHASE6A / "retrieval/anchor_resolutions.jsonl")
    routes = load_jsonl(ROUTES)
    directionality = load_json(PHASE6A1 / "relation_directionality_audit.json")
    sequence_inventory = load_json(PHASE6A1 / "path_sequence_inventory.json")
    node_types_from_registry = {row["node_type"] for row in node_registry["node_types"]}
    if node_types_from_registry != set(NODE_TYPES) or node_registry["node_type_count"] != len(NODE_TYPES):
        raise RuntimeError("frozen node universe differs from the required 14-node universe")
    relations = relation_registry["frozen_relations"]
    if len(relations) != 22:
        raise RuntimeError(f"expected 22 frozen relations, observed {len(relations)}")
    if len(nodes_list) != 155391 or len(edges) != 184223:
        raise RuntimeError(f"persisted graph count mismatch: nodes={len(nodes_list)} edges={len(edges)}")
    if len(resolutions) != 416 or len(routes) != 416:
        raise RuntimeError(f"route universe mismatch: resolutions={len(resolutions)} routes={len(routes)}")
    if any(row["resolution_status"] not in {"EXACT_SINGLE", "EXACT_MULTI"} for row in resolutions):
        raise RuntimeError("non-exact route resolution found")
    nodes = {row["record_id"]: row for row in nodes_list}
    if len(nodes) != len(nodes_list):
        raise RuntimeError("duplicate persisted graph record_id")
    nodes_by_type: dict[str, list[str]] = defaultdict(list)
    for row in nodes_list:
        nodes_by_type[row["node_type"]].append(row["record_id"])
    edges_by_relation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        edges_by_relation[edge["relation_type"]].append(edge)
    frozen_relation_types = {row["relation_type"] for row in relations}
    if set(edges_by_relation) != frozen_relation_types:
        raise RuntimeError("persisted edge relation universe differs from frozen relation registry")
    if set(NODE_TYPES) != set(nodes_by_type):
        raise RuntimeError("persisted graph node universe differs from frozen node registry")
    directionality_by_relation = {row["relation_type"]: row for row in directionality["relations"]}
    if set(directionality_by_relation) != frozen_relation_types:
        raise RuntimeError("Phase 6A.1 directionality universe differs from frozen relation registry")
    if len(sequence_inventory["views"]["SAFE_BIDIRECTIONAL_DIAGNOSTIC"]) != 76:
        raise RuntimeError("Phase 6A.1 safe sequence denominator is not 76")
    return {
        "node_registry": node_registry,
        "relation_registry": relation_registry,
        "motifs": motifs,
        "relations": relations,
        "nodes_list": nodes_list,
        "nodes": nodes,
        "nodes_by_type": nodes_by_type,
        "edges": edges,
        "edges_by_relation": edges_by_relation,
        "resolutions": resolutions,
        "routes": routes,
        "phase6a1_directionality_by_relation": directionality_by_relation,
        "phase6a1_sequence_inventory": sequence_inventory,
    }


def run_design_once(data: dict[str, Any]) -> dict[str, Any]:
    transitions, excluded = build_transition_set(data)
    simulation = simulate_topology(data, transitions, excluded)
    coverage = structural_coverage(data, transitions, simulation)
    fanout = build_fanout_analysis(transitions, excluded)
    return {
        "transitions": transitions,
        "excluded": excluded,
        "simulation": simulation,
        "coverage": coverage,
        "fanout": fanout,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    input_verification = verify_inputs()
    data = load_data()

    first = run_design_once(data)
    second = run_design_once(data)
    first_fingerprints = component_fingerprints(
        first["transitions"], first["excluded"], first["simulation"], first["coverage"], first["fanout"],
    )
    second_fingerprints = component_fingerprints(
        second["transitions"], second["excluded"], second["simulation"], second["coverage"], second["fanout"],
    )
    determinism = build_determinism_validation(first_fingerprints, second_fingerprints)
    if determinism["determinism_status"] != "PASS":
        raise RuntimeError("structural simulation determinism check failed")

    transitions = first["transitions"]
    excluded = first["excluded"]
    simulation = first["simulation"]
    coverage = first["coverage"]
    fanout = first["fanout"]
    grammar = build_grammar(data, transitions, excluded, input_verification)
    transition_matrix = build_transition_matrix(transitions)
    node_matrix = build_node_matrix(transitions)
    forbidden = build_forbidden_registry(excluded)
    motif_mapping = build_motif_mapping(data, transitions)
    justifications = build_justifications(transitions)
    risks = build_risk_register(simulation)
    integrity = build_scientific_integrity(input_verification)
    gates = readiness_gates(
        input_verification, grammar, coverage, simulation, determinism, risks, integrity,
        transition_matrix, node_matrix, forbidden, motif_mapping, justifications,
    )
    grammar["freeze_review_readiness_gates"] = gates
    grammar["readiness_gate_result"] = f"{sum(row['passed'] for row in gates)}/{len(gates)} GO"
    report = build_report(
        input_verification, grammar, transition_matrix, node_matrix, forbidden, motif_mapping,
        fanout, coverage, simulation, risks, integrity, determinism, gates,
    )

    payloads: dict[str, dict[str, Any] | str] = {
        "graph_traversal_grammar_v1_1_draft.json": grammar,
        "typed_transition_matrix_v1_1_draft.json": transition_matrix,
        "node_type_traversal_matrix_v1_1_draft.json": node_matrix,
        "forbidden_traversals_v1_1_draft.json": forbidden,
        "v1_motif_to_v1_1_grammar_mapping.json": motif_mapping,
        "grammar_transition_justifications.json": justifications,
        "grammar_fanout_analysis.json": fanout,
        "grammar_structural_coverage.json": coverage,
        "grammar_topology_simulation.json": simulation,
        "grammar_risk_register.json": risks,
        "scientific_integrity.json": integrity,
        "determinism_validation.json": determinism,
        "PHASE6A2_TYPED_GRAMMAR_DESIGN_REVIEW.md": report,
    }
    mandatory_nonself = set(MANDATORY_ARTIFACT_NAMES) - {"phase6a2_artifact_hashes.json"}
    if not mandatory_nonself <= set(payloads):
        raise RuntimeError(f"missing mandatory non-self artifacts: {sorted(mandatory_nonself - set(payloads))}")
    for name, payload in payloads.items():
        path = OUTPUT / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            write_json(path, payload)

    artifact_hashes = {
        name: {"sha256": sha256_file(OUTPUT / name), "bytes": (OUTPUT / name).stat().st_size}
        for name in sorted(payloads)
    }
    hash_inventory = {
        "artifact_type": "graphrag_phase6a2_artifact_hash_inventory",
        "artifact_version": "1.1-draft",
        "status": "PROPOSAL_ONLY",
        "hash_algorithm": "SHA-256",
        "hash_scope": "raw serialized file bytes",
        "self_hash_omitted": True,
        "self_hash_omission_reason": "A hash inventory cannot contain its own stable raw-byte digest; compute the inventory digest externally after serialization.",
        "hashed_artifact_count": len(artifact_hashes),
        "artifacts": artifact_hashes,
        "mandatory_artifact_count": len(MANDATORY_ARTIFACT_NAMES),
        "mandatory_artifact_names": list(MANDATORY_ARTIFACT_NAMES),
        "mandatory_nonself_artifact_hash_count": len(mandatory_nonself),
        "extra_hashed_artifact_names": sorted(set(payloads) - mandatory_nonself),
        "analysis_script": {
            "path": Path(__file__).name,
            "sha256": sha256_file(Path(__file__)),
            "bytes": Path(__file__).stat().st_size,
        },
        "input_verification": input_verification,
        "determinism_status": determinism["determinism_status"],
        "required_artifacts_present_including_this_inventory": mandatory_nonself <= set(payloads),
    }
    write_json(OUTPUT / "phase6a2_artifact_hashes.json", hash_inventory)

    summary = {
        "status": "PASS",
        "proposal_only": True,
        "transition_count": len(transitions),
        "transition_class_counts": grammar["transition_class_counts"],
        "relations_used": len(grammar["frozen_relation_types_used"]),
        "structural_coverage": coverage["overall"],
        "candidate_path_count": simulation["candidate_path_count"],
        "paths_by_depth": simulation["paths_by_exact_depth"],
        "path_set_sha256": simulation["candidate_path_set_sha256"],
        "determinism": determinism["determinism_status"],
        "readiness": grammar["readiness_gate_result"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
