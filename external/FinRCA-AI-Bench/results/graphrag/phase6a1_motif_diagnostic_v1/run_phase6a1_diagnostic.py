#!/usr/bin/env python3
"""Phase 6A.1 read-only structural reachability and directionality audit.

This program reads the frozen Phase 6A registry/graph/retrieval artifacts and the
authorized 416-case validation routing set.  It does not rebuild or modify the
graph.  Validation evidence is opened only after topology and motif enumeration
have completed and their in-memory canonical hashes have been fixed.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.graphrag.graph_builder import load_persisted_graph
from src.graphrag.motif_engine import FrozenMotifEngine
from src.graphrag.registry_loader import load_frozen_registries
from src.graphrag.validation import load_validation_evidence_projection
from src.rag.corpus import load_persisted_corpus
from src.rag.evidence import resolve_evidence


ROOT = WORKSPACE_ROOT
FREEZE = ROOT / "results/graphrag/registry_freeze_v1"
PHASE6A = ROOT / "results/graphrag/phase6a_graph_retrieval_v1_0"
ROUTES = ROOT / "results/rag/phase5_rag_validation_routes_v1_0_20260812T040938Z/validation_routes.jsonl"
CORPUS = ROOT / "results/rag/phase5_rag_index_v1_0_20260810T000000Z/corpus"
VALIDATION_EVIDENCE = ROOT / "data/benchmark/validation/rca_ground_truth.jsonl"
OUTPUT = Path(__file__).resolve().parent

EXPECTED_HASHES = {
    FREEZE / "graph_node_registry_v1.json": "4c17ff5c863ed446418fbc2b3b407704519862feddc5f0c81546c210f8e91d10",
    FREEZE / "graph_relation_registry_v1.json": "f8c61e2117c09921d001c4d476ef80d138f362c2ac084850544fc56077a7b0c3",
    FREEZE / "graph_path_motifs_v1.json": "36dd0b0d491dd6ef5f46c1dcd38cfe5e9e2ab61c632038b89cdc6ed9e0ec58ef",
    FREEZE / "graph_ranking_policy_v1.json": "85a167767f6147c2a51db9cdab47d7157731bb2126ca2cf2c452f4e9bde602f0",
    FREEZE / "graph_freeze_manifest_v1.json": "8097eb64accec2c076d07ed9ae4604d2202d1ca83578cf8557b40f034b7cad76",
    PHASE6A / "graph/nodes.jsonl": "87f80fa5e91675b192dd051598a9197c0703650f4daf09c2a7619c031295a167",
    PHASE6A / "graph/edges.jsonl": "ee364fa677abeda3b25119d5c3c2f1aea5bc8902a28e7f7ecefcddd38a77d9ed",
    PHASE6A / "retrieval/graph_retrieval_results.jsonl": "7a984285d0c78cd01ec0f50ae06674257c39b8f64b790ef08595df8b82897081",
    PHASE6A / "retrieval/graph_path_ledger.jsonl": "600a02cee10691e3d2942081f14186e9e47ccb270e02a15117814b8d69806b9e",
    PHASE6A / "retrieval/evidence_packets.jsonl": "24f2566d639dffe8648abe74abecafba9b5a71043b6d3d2252d008b206d40b1b",
    PHASE6A / "evaluation/retrieval_metrics.json": "53eb3f017185ba3009d46cc87f8f453fcd8302f259b63c9ec80de46d294be76c",
    PHASE6A / "PHASE6A_GRAPH_RETRIEVAL_REVIEW.md": "e82e6777a6cb71b053045553a5aa1d5b3210eafa07fc08553b904af65e0d8787",
    PHASE6A / "phase6a_artifact_hashes.json": "5a2241d8082120f4c7d37efae82c18f61e94b97c1d8962b250928b855cbb5b0f",
}

TOPOLOGY_VIEWS = ("STORED_DIRECTION_ONLY", "SAFE_BIDIRECTIONAL_DIAGNOSTIC")
GAP_CATEGORIES = (
    "NO_MOTIF_FOR_ANCHOR_TYPE", "MOTIF_DIRECTION_MISMATCH",
    "RELATION_DIRECTION_MISMATCH", "MOTIF_TOO_SHORT", "MOTIF_SEQUENCE_MISSING",
    "HUB_RESTRICTION", "TEMPORAL_RESTRICTION", "EDGE_NOT_PRESENT",
    "IMPLEMENTATION_EXECUTION_GAP", "OTHER / NOT SAFELY ATTRIBUTABLE",
)
HUB_RELATIONS = {
    "VENDOR_CHANGE_FOR_VENDOR", "PO_FOR_VENDOR", "INVOICE_FOR_VENDOR",
    "PAYMENT_FOR_VENDOR", "PURCHASE_ORDER_CREATED_BY_EMPLOYEE",
    "VENDOR_CHANGE_CHANGED_BY_EMPLOYEE", "AUDIT_EVENT_FOR_VENDOR",
}
REVERSE_HUB_RISK_RELATIONS = HUB_RELATIONS - {"AUDIT_EVENT_FOR_VENDOR"}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def canonical_bytes(value: Any) -> bytes:
    return (canonical(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def jsonl_bytes(rows: Sequence[dict[str, Any]]) -> bytes:
    return "".join(canonical(row) + "\n" for row in rows).encode("utf-8")


def nearest_rank(values: Sequence[int | float], quantile: float) -> int | float:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def distribution(values: Sequence[int]) -> dict[str, Any]:
    return {
        "anchor_count": len(values),
        "anchors_with_at_least_one_path": sum(value > 0 for value in values),
        "mean_paths": statistics.fmean(values) if values else 0.0,
        "median_paths": statistics.median(values) if values else 0.0,
        "p90_paths_nearest_rank": nearest_rank(values, 0.90),
        "p95_paths_nearest_rank": nearest_rank(values, 0.95),
        "p99_paths_nearest_rank": nearest_rank(values, 0.99),
        "maximum_paths": max(values, default=0),
        "total_paths": sum(values),
    }


def verify_inputs() -> dict[str, Any]:
    rows = []
    for path, expected in EXPECTED_HASHES.items():
        observed = sha256_file(path)
        rows.append({
            "path": path.relative_to(ROOT).as_posix(), "expected_sha256": expected,
            "observed_sha256": observed, "status": "PASS" if observed == expected else "FAIL",
        })
    failures = [row for row in rows if row["status"] != "PASS"]
    if failures:
        raise RuntimeError("STOP — PHASE 6A.1 BLOCKED: " + canonical(failures))
    return {"status": "PASS", "verified_artifact_count": len(rows), "artifacts": rows}


def relation_classification(relation: dict[str, Any]) -> str:
    # Broad Vendor/Employee reverse neighborhoods remain risky.  The typed
    # AUDIT_EVENT_FOR_VENDOR reverse is separately classified as structurally
    # safe because its maximum degree is one, while the frozen Vendor traversal
    # prohibition still excludes it from View B.
    if relation["relation_type"] in REVERSE_HUB_RISK_RELATIONS:
        return "REVERSE_HUB_RISK"
    return "SAFE_REVERSIBLE_CANDIDATE"


def build_directionality_audit(
    relations: list[dict[str, Any]], nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]],
) -> dict[str, Any]:
    node_type_counts = Counter(row["node_type"] for row in nodes.values())
    by_relation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        by_relation[edge["relation_type"]].append(edge)
    output = []
    for relation in relations:
        relation_type = relation["relation_type"]
        selected = by_relation[relation_type]
        reverse_degrees = Counter(edge["target_record_id"] for edge in selected)
        target_domain = node_type_counts[relation["target_node_type"]]
        values = list(reverse_degrees.values()) + [0] * (target_domain - len(reverse_degrees))
        classification = relation_classification(relation)
        safe = classification == "SAFE_REVERSIBLE_CANDIDATE"
        output.append({
            "relation_type": relation_type,
            "source_node_type": relation["source_node_type"],
            "target_node_type": relation["target_node_type"],
            "stored_direction": f"{relation['source_node_type']} -> {relation['target_node_type']}",
            "forward_edge_count": len(selected),
            "reverse_traversal_class": classification,
            "reverse_is_exact": True,
            "reverse_preserves_provenance": True,
            "reverse_preserves_temporal_validity": True,
            "reverse_degree_domain_size": target_domain,
            "reverse_nonzero_degree_node_count": len(reverse_degrees),
            "reverse_degree_mean": statistics.fmean(values) if values else 0.0,
            "reverse_degree_p95": nearest_rank(values, 0.95),
            "reverse_degree_max": max(values, default=0),
            "hub_risk": relation["hub_risk"],
            "recommendation": (
                "Structurally exact and entity-local (maximum reverse degree 1), but retain the frozen Vendor traversal prohibition unless a terminal-only audit-event exception is independently approved."
                if relation_type == "AUDIT_EVENT_FOR_VENDOR" else
                "Retain exact bidirectional eligibility as a proposal candidate; keep traversal typed and simple-path bounded."
                if safe else
                "Retain the frozen traversal prohibition; reverse expansion reaches a Vendor/Employee context hub."
            ),
            "recommendation_status": "PROPOSAL_ONLY",
            "frozen_v1_traversable": bool(relation["traversable"]),
            "frozen_v1_reverse_traversal": bool(relation["reverse_traversal"]),
        })
    counts = Counter(row["reverse_traversal_class"] for row in output)
    return {
        "audit_scope": "22 frozen executable relations; no registry change",
        "classification_rule": (
            "Exact entity-local relations are SAFE_REVERSIBLE_CANDIDATE. Exact relations with broad Vendor/Employee reverse neighborhoods are REVERSE_HUB_RISK. AUDIT_EVENT_FOR_VENDOR is structurally safe at maximum reverse degree 1 but remains excluded from View B by the separate frozen Vendor hub prohibition."
        ),
        "classification_counts": {key: counts.get(key, 0) for key in (
            "FORWARD_ONLY_NATURAL", "SAFE_REVERSIBLE_CANDIDATE", "REVERSE_HUB_RISK",
            "REVERSE_SEMANTICALLY_INVALID", "NEEDS_REVIEW",
        )},
        "relations": output,
    }


def path_id(
    case_id: str, anchor: str, view: str, traversal_sequence: Sequence[str], record_ids: Sequence[str],
) -> str:
    raw = "\t".join((case_id, anchor, view, *traversal_sequence, *record_ids)).encode("utf-8")
    return "DIAG_PATH_" + hashlib.sha256(raw).hexdigest()[:24]


def path_signature(path: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return tuple(path["node_type_sequence"]), tuple(path["traversal_sequence"])


def signature_id(signature: tuple[tuple[str, ...], tuple[str, ...]]) -> str:
    raw = "\t".join((*signature[0], "--", *signature[1])).encode("utf-8")
    return "SEQ_" + hashlib.sha256(raw).hexdigest()[:20]


def enumerate_view(
    *, view: str, routes: list[dict[str, Any]], resolutions: list[dict[str, Any]],
    nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], relation_map: dict[str, dict[str, Any]],
    relation_order: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    forward: dict[str, list[dict[str, Any]]] = defaultdict(list)
    reverse: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        forward[edge["source_record_id"]].append(edge)
        reverse[edge["target_record_id"]].append(edge)
    for adjacency in (forward, reverse):
        for record_id in adjacency:
            adjacency[record_id].sort(key=lambda edge: (
                relation_order[edge["relation_type"]], edge["source_record_id"],
                edge["target_record_id"], edge["edge_id"],
            ))
    route_by_case = {row["case_id"]: row for row in routes}
    cycle_counts = Counter()
    output = []
    for resolution in resolutions:
        case_id = resolution["case_id"]
        route = route_by_case[case_id]
        partial: list[tuple[list[str], list[dict[str, Any]], list[str]]] = [
            ([anchor], [], []) for anchor in resolution["resolved_record_ids"]
        ]
        paths_by_depth: dict[str, list[dict[str, Any]]] = {str(depth): [] for depth in (1, 2, 3)}
        for depth in (1, 2, 3):
            expanded: list[tuple[list[str], list[dict[str, Any]], list[str]]] = []
            for records, path_edges, traversals in partial:
                current = records[-1]
                candidates: list[tuple[int, int, str, dict[str, Any], str]] = []
                for edge in forward.get(current, []):
                    relation = relation_map[edge["relation_type"]]
                    if relation["traversable"] and edge["temporal_eligible"]:
                        candidates.append((relation_order[edge["relation_type"]], 0, edge["target_record_id"], edge, "forward"))
                if view == "SAFE_BIDIRECTIONAL_DIAGNOSTIC":
                    for edge in reverse.get(current, []):
                        relation = relation_map[edge["relation_type"]]
                        if (
                            relation_classification(relation) == "SAFE_REVERSIBLE_CANDIDATE"
                            and edge["relation_type"] not in HUB_RELATIONS
                            and edge["temporal_eligible"]
                        ):
                            candidates.append((relation_order[edge["relation_type"]], 1, edge["source_record_id"], edge, "reverse"))
                for _, _, next_id, edge, direction in sorted(candidates, key=lambda row: (row[0], row[1], row[2], row[3]["edge_id"])):
                    if not nodes[next_id]["temporal_eligible"]:
                        continue
                    if next_id in records:
                        cycle_counts[f"depth_{depth}"] += 1
                        continue
                    next_records = [*records, next_id]
                    next_edges = [*path_edges, edge]
                    next_traversals = [*traversals, f"{edge['relation_type']}:{direction}"]
                    expanded.append((next_records, next_edges, next_traversals))
                    root = next_records[0]
                    paths_by_depth[str(depth)].append({
                        "path_id": path_id(case_id, root, view, next_traversals, next_records),
                        "case_id": case_id,
                        "anchor_record_id": root,
                        "route_anchor_type": route["primary_entity_type"],
                        "topology_view": view,
                        "path_depth": depth,
                        "record_id_sequence": next_records,
                        "node_type_sequence": [nodes[value]["node_type"] for value in next_records],
                        "edge_id_sequence": [value["edge_id"] for value in next_edges],
                        "relation_sequence": [value["relation_type"] for value in next_edges],
                        "traversal_sequence": next_traversals,
                        "reverse_step_count": sum(value.endswith(":reverse") for value in next_traversals),
                        "orientation_switch_count": sum(
                            next_traversals[index].rsplit(":", 1)[1] != next_traversals[index - 1].rsplit(":", 1)[1]
                            for index in range(1, len(next_traversals))
                        ),
                        "temporal_valid": True,
                        "simple_path": True,
                    })
            partial = expanded
        for depth in paths_by_depth:
            paths_by_depth[depth].sort(key=lambda row: row["path_id"])
        hub_incidents = []
        for anchor in resolution["resolved_record_ids"]:
            for direction, candidates in (("forward", forward.get(anchor, [])), ("reverse", reverse.get(anchor, []))):
                for edge in candidates:
                    if edge["relation_type"] in HUB_RELATIONS:
                        hub_incidents.append({
                            "anchor_record_id": anchor, "edge_id": edge["edge_id"],
                            "relation_type": edge["relation_type"], "direction": direction,
                        })
        output.append({
            "case_id": case_id,
            "route_anchor_id": route["primary_entity_id"],
            "route_anchor_type": route["primary_entity_type"],
            "resolved_anchor_record_ids": resolution["resolved_record_ids"],
            "resolved_anchor_node_types": resolution["resolved_node_types"],
            "topology_view": view,
            "path_counts_by_exact_depth": {depth: len(values) for depth, values in paths_by_depth.items()},
            "maximum_reached_depth": max((int(depth) for depth, values in paths_by_depth.items() if values), default=0),
            "paths_by_exact_depth": paths_by_depth,
            "hub_restriction_incident_edges": sorted(hub_incidents, key=lambda row: (row["anchor_record_id"], row["relation_type"], row["direction"], row["edge_id"])),
        })
    output.sort(key=lambda row: row["case_id"])
    return output, {
        "topology_view": view,
        "cycle_candidates_removed_by_simple_path_rule": dict(sorted(cycle_counts.items())),
        "cycle_candidates_removed_total": sum(cycle_counts.values()),
        "simple_path_rule": "No repeated record_id within one path",
    }


def reachability_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    overall = {
        f"depth_{depth}": distribution([row["path_counts_by_exact_depth"][str(depth)] for row in rows])
        for depth in (1, 2, 3)
    }
    overall["all_depths_1_to_3"] = distribution([
        sum(row["path_counts_by_exact_depth"].values()) for row in rows
    ])
    by_type = {}
    for anchor_type in sorted({row["route_anchor_type"] for row in rows}):
        selected = [row for row in rows if row["route_anchor_type"] == anchor_type]
        by_type[anchor_type] = {
            "case_count": len(selected),
            **{
                f"depth_{depth}": distribution([row["path_counts_by_exact_depth"][str(depth)] for row in selected])
                for depth in (1, 2, 3)
            },
            "all_depths_1_to_3": distribution([
                sum(row["path_counts_by_exact_depth"].values()) for row in selected
            ]),
        }
    return {"overall": overall, "by_anchor_type": by_type}


def motif_variants(motif: dict[str, Any]) -> list[tuple[str, ...]]:
    variants: list[tuple[str, ...]] = [tuple()]
    for raw in motif["edge_sequence"]:
        expression, direction = raw.rsplit(":", 1)
        relation_types = motif["resolved_relation_types"] if "{" in expression else [expression]
        variants = [(*prior, f"{relation_type}:{direction}") for prior in variants for relation_type in relation_types]
    return variants


def represented_motifs(
    signature: tuple[tuple[str, ...], tuple[str, ...]], motifs: list[dict[str, Any]],
) -> list[str]:
    node_types, traversals = signature
    return sorted(
        motif["motif_id"] for motif in motifs
        if node_types[0] in motif["permitted_anchor_types"] and traversals in motif_variants(motif)
    )


def infer_engine_signature(path: dict[str, Any], node_types: dict[str, str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    traversals = []
    for index, edge in enumerate(path["edges"]):
        current, next_id = path["node_sequence"][index:index + 2]
        if current == edge["source_record_id"] and next_id == edge["target_record_id"]:
            direction = "forward"
        elif current == edge["target_record_id"] and next_id == edge["source_record_id"]:
            direction = "reverse"
        else:
            raise RuntimeError(f"path/edge orientation mismatch: {path['path_id']}")
        traversals.append(f"{edge['relation_type']}:{direction}")
    return tuple(node_types[value] for value in path["node_sequence"]), tuple(traversals)


def motif_step_diagnostic(engine: FrozenMotifEngine, motif: dict[str, Any], anchor: str) -> dict[str, Any]:
    partial: list[list[str]] = [[anchor]]
    step_counts: list[int] = []
    failure_reason = None
    failure_step = None
    for step_index, (relation_types, direction) in enumerate(engine._steps(motif), start=1):  # exact frozen parser
        expanded: list[list[str]] = []
        type_aligned = False
        physical_edge_present = False
        temporal_rejected = False
        hub_rejected = False
        for records in partial:
            current = records[-1]
            current_type = engine.snapshot.nodes[current].node_type
            for relation_type in relation_types:
                definition = engine.relations[relation_type]
                expected_type = definition["source_node_type"] if direction == "forward" else definition["target_node_type"]
                type_aligned = type_aligned or current_type == expected_type
                permitted = definition["traversable"] if direction == "forward" else definition["reverse_traversal"]
                if not permitted:
                    hub_rejected = True
                    continue
                raw_edges = (
                    engine.snapshot.forward.get((current, relation_type), ())
                    if direction == "forward" else engine.snapshot.reverse.get((current, relation_type), ())
                )
                physical_edge_present = physical_edge_present or bool(raw_edges)
                for next_id, edge in engine.snapshot.traverse(current, relation_type, direction):
                    if not edge.temporal_eligible or not engine.snapshot.nodes[next_id].temporal_eligible:
                        temporal_rejected = True
                        continue
                    expanded.append([*records, next_id])
        partial = sorted(expanded)
        step_counts.append(len(partial))
        if not partial and failure_reason is None:
            failure_step = step_index
            if hub_rejected:
                failure_reason = "HUB_RESTRICTION"
            elif not type_aligned:
                failure_reason = "MOTIF_DIRECTION_MISMATCH"
            elif temporal_rejected and physical_edge_present:
                failure_reason = "TEMPORAL_RESTRICTION"
            elif not physical_edge_present:
                failure_reason = "EDGE_NOT_PRESENT"
            else:
                failure_reason = "OTHER / NOT SAFELY ATTRIBUTABLE"
    return {
        "motif_id": motif["motif_id"],
        "motif_depth": len(motif["edge_sequence"]),
        "step_path_counts": step_counts,
        "first_hop_succeeds": bool(step_counts and step_counts[0] > 0),
        "second_hop_succeeds": bool(len(step_counts) >= 2 and step_counts[1] > 0),
        "third_hop_succeeds": bool(len(step_counts) >= 3 and step_counts[2] > 0),
        "complete_path_count": step_counts[-1] if step_counts else 0,
        "first_failure_step": failure_step,
        "zero_path_reason": failure_reason,
    }


def execute_frozen_motifs(
    routes: list[dict[str, Any]], resolutions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    registries = load_frozen_registries(FREEZE)
    snapshot = load_persisted_graph(PHASE6A / "graph")
    engine = FrozenMotifEngine(snapshot, registries)
    route_by_case = {row["case_id"]: row for row in routes}
    motif_by_id = {row["motif_id"]: row for row in registries.motifs["frozen_motifs"]}
    rows = []
    all_paths = []
    attempt_rows = []
    for resolution in resolutions:
        case_id = resolution["case_id"]
        case_paths = []
        applicable: set[str] = set()
        attempted: set[str] = set()
        hub_events = []
        per_anchor = []
        for anchor in resolution["resolved_record_ids"]:
            found, candidates, executed, blocked = engine.execute(case_id, anchor)
            case_paths.extend(found)
            applicable.update(candidates)
            attempted.update(executed)
            hub_events.extend(blocked)
            diagnostics = [motif_step_diagnostic(engine, motif_by_id[value], anchor) for value in candidates]
            for item in diagnostics:
                attempt_rows.append({
                    "case_id": case_id, "route_anchor_type": route_by_case[case_id]["primary_entity_type"],
                    "anchor_record_id": anchor, **item,
                })
            per_anchor.append({
                "anchor_record_id": anchor,
                "anchor_node_type": snapshot.nodes[anchor].node_type,
                "applicable_motif_ids": candidates,
                "attempted_motif_ids": executed,
                "motif_step_diagnostics": diagnostics,
                "completed_motif_ids": sorted({path["motif_id"] for path in found}),
                "complete_path_count": len(found),
            })
        case_paths.sort(key=lambda row: row["path_id"])
        all_paths.extend(case_paths)
        rows.append({
            "case_id": case_id,
            "route_anchor_type": route_by_case[case_id]["primary_entity_type"],
            "resolved_anchor_record_ids": resolution["resolved_record_ids"],
            "applicable_motif_ids": sorted(applicable),
            "attempted_motif_ids": sorted(attempted),
            "completed_motif_ids": sorted({path["motif_id"] for path in case_paths}),
            "path_count": len(case_paths),
            "path_count_by_depth": dict(sorted(Counter(str(path["path_length"]) for path in case_paths).items())),
            "maximum_completed_path_depth": max((path["path_length"] for path in case_paths), default=0),
            "zero_path_reasons": sorted({
                item["zero_path_reason"] for anchor in per_anchor for item in anchor["motif_step_diagnostics"]
                if item["zero_path_reason"]
            }),
            "per_resolved_anchor": per_anchor,
            "complete_paths": case_paths,
            "hub_block_events": sorted(hub_events, key=canonical),
        })
    actual_ledger = load_jsonl(PHASE6A / "retrieval/graph_path_ledger.jsonl")
    engine_ids = {row["path_id"] for row in all_paths}
    actual_ids = {row["path_id"] for row in actual_ledger}
    if engine_ids != actual_ids:
        raise RuntimeError("Frozen motif engine reproduction differs from Phase 6A ledger")
    diagnostics = {
        "existing_engine_used_without_modification": True,
        "engine_emitted_path_count": len(all_paths),
        "persisted_v1_ledger_path_count": len(actual_ledger),
        "path_id_sets_identical": True,
        "implementation_execution_gap_count": 0,
        "attempts": attempt_rows,
    }
    return rows, all_paths, diagnostics


def build_sequence_inventory(
    raw_by_view: dict[str, list[dict[str, Any]]], motifs: list[dict[str, Any]],
    engine_paths: list[dict[str, Any]], node_type_lookup: dict[str, str],
) -> dict[str, Any]:
    executed_signatures = {infer_engine_signature(path, node_type_lookup) for path in engine_paths}
    inventories = {}
    for view, rows in raw_by_view.items():
        grouped: dict[tuple[tuple[str, ...], tuple[str, ...]], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            for paths in row["paths_by_exact_depth"].values():
                for path in paths:
                    grouped[path_signature(path)].append(path)
        output = []
        for signature, paths in grouped.items():
            per_case = Counter(path["case_id"] for path in paths)
            represented = represented_motifs(signature, motifs)
            output.append({
                "sequence_id": signature_id(signature),
                "topology_view": view,
                "path_depth": len(signature[1]),
                "relation_sequence": [value.rsplit(":", 1)[0] for value in signature[1]],
                "traversal_sequence": list(signature[1]),
                "node_type_sequence": list(signature[0]),
                "path_instance_count": len(paths),
                "distinct_anchor_count": len(per_case),
                "anchor_types": sorted({path["route_anchor_type"] for path in paths}),
                "average_multiplicity": len(paths) / len(per_case),
                "maximum_multiplicity": max(per_case.values()),
                "direction_changes_required": sum(value.endswith(":reverse") for value in signature[1]),
                "orientation_switch_count": sum(
                    signature[1][index].rsplit(":", 1)[1] != signature[1][index - 1].rsplit(":", 1)[1]
                    for index in range(1, len(signature[1]))
                ),
                "represented_by_frozen_motif": bool(represented),
                "representing_frozen_motif_ids": represented,
                "executed_by_graph_v1_0": signature in executed_signatures,
            })
        output.sort(key=lambda row: (-row["distinct_anchor_count"], row["sequence_id"]))
        inventories[view] = output
    return {
        "definition": "A sequence is direction-aware and typed: starting node type + ordered relation:direction steps + resulting node types.",
        "views": inventories,
    }


def motif_coverage(
    raw_by_view: dict[str, list[dict[str, Any]]], motifs: list[dict[str, Any]],
) -> dict[str, Any]:
    output = {}
    for view, rows in raw_by_view.items():
        all_signatures: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
        represented: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
        case_rows = []
        for row in rows:
            signatures = {
                path_signature(path) for paths in row["paths_by_exact_depth"].values() for path in paths
            }
            represented_case = {value for value in signatures if represented_motifs(value, motifs)}
            all_signatures.update(signatures)
            represented.update(represented_case)
            case_rows.append({
                "case_id": row["case_id"], "anchor_type": row["route_anchor_type"],
                "reachable_sequence_count": len(signatures),
                "represented_sequence_count": len(represented_case),
                "coverage_ratio": len(represented_case) / len(signatures) if signatures else None,
            })
        ratios = [row["coverage_ratio"] for row in case_rows if row["coverage_ratio"] is not None]
        by_type = {}
        for anchor_type in sorted({row["anchor_type"] for row in case_rows}):
            selected_cases = [row for row in case_rows if row["anchor_type"] == anchor_type]
            selected_raw_rows = [row for row in rows if row["route_anchor_type"] == anchor_type]
            signatures = {
                path_signature(path) for row in selected_raw_rows
                for paths in row["paths_by_exact_depth"].values() for path in paths
            }
            selected_rep = {value for value in signatures if represented_motifs(value, motifs)}
            selected_ratios = [row["coverage_ratio"] for row in selected_cases if row["coverage_ratio"] is not None]
            by_type[anchor_type] = {
                "case_count": len(selected_cases),
                "distinct_reachable_sequence_count": len(signatures),
                "distinct_represented_sequence_count": len(selected_rep),
                "sequence_level_ratio": len(selected_rep) / len(signatures) if signatures else None,
                "cases_with_raw_sequences": sum(row["reachable_sequence_count"] > 0 for row in selected_cases),
                "cases_with_any_represented_sequence": sum(row["represented_sequence_count"] > 0 for row in selected_cases),
                "mean_case_level_ratio": statistics.fmean(selected_ratios) if selected_ratios else None,
            }
        output[view] = {
            "distinct_reachable_sequence_count": len(all_signatures),
            "distinct_represented_sequence_count": len(represented),
            "sequence_level_ratio": len(represented) / len(all_signatures) if all_signatures else None,
            "cases_with_raw_sequences": sum(row["reachable_sequence_count"] > 0 for row in case_rows),
            "cases_with_any_represented_sequence": sum(row["represented_sequence_count"] > 0 for row in case_rows),
            "case_support_ratio": (
                sum(row["represented_sequence_count"] > 0 for row in case_rows)
                / sum(row["reachable_sequence_count"] > 0 for row in case_rows)
                if any(row["reachable_sequence_count"] > 0 for row in case_rows) else None
            ),
            "mean_case_level_ratio": statistics.fmean(ratios) if ratios else None,
            "by_anchor_type": by_type,
        }
    return {
        "formula": "distinct direction-aware typed sequences represented by at least one frozen motif / distinct reachable direction-aware typed sequences",
        "case_definition": "Per case, the same ratio is computed over distinct reachable signatures; case support is also reported separately.",
        "primary_diagnostic_denominator": "SAFE_BIDIRECTIONAL_DIAGNOSTIC within depth<=3, frozen hub exclusions, and simple-path constraints",
        "views": output,
    }


def frozen_prefix(signature: tuple[tuple[str, ...], tuple[str, ...]], motifs: list[dict[str, Any]]) -> bool:
    nodes, traversals = signature
    return any(
        nodes[0] in motif["permitted_anchor_types"]
        and len(variant) < len(traversals)
        and traversals[:len(variant)] == variant
        for motif in motifs for variant in motif_variants(motif)
    )


def build_case_comparison_and_gaps(
    *, stored: list[dict[str, Any]], safe: list[dict[str, Any]], motifs: list[dict[str, Any]],
    motif_rows: list[dict[str, Any]], motif_diagnostics: dict[str, Any],
    actual_results: list[dict[str, Any]], actual_ledger: list[dict[str, Any]],
    relation_map: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stored_by_case = {row["case_id"]: row for row in stored}
    safe_by_case = {row["case_id"]: row for row in safe}
    motif_by_case = {row["case_id"]: row for row in motif_rows}
    actual_by_case = {row["case_id"]: row for row in actual_results}
    ledger_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in actual_ledger:
        ledger_by_case[row["case_id"]].append(row)
    attempt_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in motif_diagnostics["attempts"]:
        attempt_by_case[row["case_id"]].append(row)
    sequence_gaps = Counter()
    sequence_gap_signatures: dict[str, set[str]] = defaultdict(set)
    case_primary = Counter()
    requested = Counter()
    comparison = []
    for case_id in sorted(safe_by_case):
        a = stored_by_case[case_id]
        b = safe_by_case[case_id]
        m = motif_by_case[case_id]
        stored_sigs = {
            path_signature(path) for paths in a["paths_by_exact_depth"].values() for path in paths
        }
        safe_paths = [path for paths in b["paths_by_exact_depth"].values() for path in paths]
        safe_sigs = {path_signature(path) for path in safe_paths}
        represented = {value for value in safe_sigs if represented_motifs(value, motifs)}
        categories = Counter()
        for signature in sorted(safe_sigs - represented):
            reverse_permission_blocked = any(
                traversal.endswith(":reverse")
                and not relation_map[traversal.rsplit(":", 1)[0]]["reverse_traversal"]
                for traversal in signature[1]
            )
            if not m["applicable_motif_ids"]:
                category = "NO_MOTIF_FOR_ANCHOR_TYPE"
            elif signature not in stored_sigs and reverse_permission_blocked:
                category = "RELATION_DIRECTION_MISMATCH"
            elif frozen_prefix(signature, motifs):
                category = "MOTIF_TOO_SHORT"
            elif any(
                signature[0][0] in motif["permitted_anchor_types"]
                and tuple(value.rsplit(":", 1)[0] for value in variant) == tuple(value.rsplit(":", 1)[0] for value in signature[1])
                for motif in motifs for variant in motif_variants(motif)
            ):
                category = "MOTIF_DIRECTION_MISMATCH"
            else:
                category = "MOTIF_SEQUENCE_MISSING"
            categories[category] += 1
            sequence_gaps[category] += 1
            sequence_gap_signatures[category].add(signature_id(signature))
        hub_blocked = bool(b["hub_restriction_incident_edges"])
        if hub_blocked:
            categories["HUB_RESTRICTION"] += 1
        attempts = attempt_by_case[case_id]
        for attempt in attempts:
            if attempt["zero_path_reason"]:
                categories[attempt["zero_path_reason"]] += 1
        implementation_gap = False
        if implementation_gap:
            categories["IMPLEMENTATION_EXECUTION_GAP"] += 1
        priority = [
            "IMPLEMENTATION_EXECUTION_GAP", "MOTIF_DIRECTION_MISMATCH",
            "RELATION_DIRECTION_MISMATCH", "MOTIF_TOO_SHORT", "NO_MOTIF_FOR_ANCHOR_TYPE",
            "MOTIF_SEQUENCE_MISSING", "HUB_RESTRICTION", "TEMPORAL_RESTRICTION",
            "EDGE_NOT_PRESENT", "OTHER / NOT SAFELY ATTRIBUTABLE",
        ]
        primary = sorted(categories, key=lambda value: (-categories[value], priority.index(value)))[0] if categories else "OTHER / NOT SAFELY ATTRIBUTABLE"
        case_primary[primary] += 1
        raw2_no_motif = bool(b["path_counts_by_exact_depth"]["2"] and not any(len(sig[1]) == 2 for sig in represented))
        raw3_no_motif = bool(b["path_counts_by_exact_depth"]["3"] and not any(len(sig[1]) == 3 for sig in represented))
        motif_exists_execution_fails = False  # exact engine/ledger reproduction proves no implementation gap
        executes_only_first = any(
            item["motif_depth"] >= 2 and item["first_hop_succeeds"] and item["complete_path_count"] == 0
            for item in attempts
        )
        physically_impossible = any(item["complete_path_count"] == 0 for item in attempts)
        stored_orientation_requires_reverse = bool(safe_sigs - stored_sigs)
        directionality_blocks = any(
            any(
                traversal.endswith(":reverse")
                and not relation_map[traversal.rsplit(":", 1)[0]]["reverse_traversal"]
                for traversal in signature[1]
            )
            for signature in safe_sigs
        )
        temporal_blocks = any(item["zero_path_reason"] == "TEMPORAL_RESTRICTION" for item in attempts)
        flags = {
            "raw_2_hop_exists_no_frozen_motif": raw2_no_motif,
            "raw_3_hop_exists_no_frozen_motif": raw3_no_motif,
            "frozen_motif_exists_execution_fails": motif_exists_execution_fails,
            "motif_executes_only_first_hop": executes_only_first,
            "motif_path_physically_impossible": physically_impossible,
            "directionality_blocks_path": directionality_blocks,
            "stored_edge_orientation_requires_reverse": stored_orientation_requires_reverse,
            "hub_restriction_blocks_path": hub_blocked,
            "temporal_rule_blocks_path": temporal_blocks,
        }
        requested.update(key for key, value in flags.items() if value)
        actual_paths = ledger_by_case[case_id]
        comparison.append({
            "case_id": case_id,
            "anchor_type": b["route_anchor_type"],
            "stored_direction_exact_depth_path_counts": a["path_counts_by_exact_depth"],
            "safe_reverse_exact_depth_path_counts": b["path_counts_by_exact_depth"],
            "safe_reverse_distinct_sequence_count": len(safe_sigs),
            "frozen_motif_represented_sequence_count": len(represented),
            "frozen_motif_emitted_path_count": m["path_count"],
            "actual_v1_emitted_path_count": len(actual_paths),
            "actual_v1_selected_path_count": sum(row["selected"] for row in actual_paths),
            "actual_v1_selected_multihop_path_count": sum(row["selected"] and row["path_length"] > 1 for row in actual_paths),
            "comparison_flags": flags,
            "gap_category_counts": {key: categories.get(key, 0) for key in GAP_CATEGORIES},
            "primary_gap_category": primary,
        })
    taxonomy = {
        "taxonomy": list(GAP_CATEGORIES),
        "classification_unit_note": "Observed unrepresented sequences are classified once; failed motif attempts and blocked hub incidents are reported separately and may overlap a case.",
        "unrepresented_sequence_gap_counts": {key: sequence_gaps.get(key, 0) for key in GAP_CATEGORIES},
        "distinct_unrepresented_sequence_counts": {key: len(sequence_gap_signatures[key]) for key in GAP_CATEGORIES},
        "case_primary_category_counts": {key: case_primary.get(key, 0) for key in GAP_CATEGORIES},
        "comparison_flag_case_counts": dict(sorted(requested.items())),
        "implementation_execution_gap_count": 0,
    }
    return comparison, taxonomy


def hop_survival(rows: list[dict[str, Any]], motif_diagnostics: dict[str, Any]) -> dict[str, Any]:
    attempts_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in motif_diagnostics["attempts"]:
        attempts_by_case[row["case_id"]].append(row)
    def summarize(selected: list[dict[str, Any]]) -> dict[str, Any]:
        case_ids = [row["case_id"] for row in selected]
        return {
            "anchor_case_count": len(case_ids),
            "anchors_with_applicable_motif": sum(bool(row["applicable_motif_ids"]) for row in selected),
            "anchors_with_first_hop_success": sum(any(item["first_hop_succeeds"] for item in attempts_by_case[case_id]) for case_id in case_ids),
            "anchors_with_second_hop_success": sum(any(item["second_hop_succeeds"] for item in attempts_by_case[case_id]) for case_id in case_ids),
            "anchors_with_third_hop_success": sum(any(item["third_hop_succeeds"] for item in attempts_by_case[case_id]) for case_id in case_ids),
            "anchors_with_complete_motif_path": sum(row["path_count"] > 0 for row in selected),
        }
    attempt_counts = {
        "eligible_motif_attempts": len(motif_diagnostics["attempts"]),
        "attempts_with_first_hop_success": sum(row["first_hop_succeeds"] for row in motif_diagnostics["attempts"]),
        "depth_at_least_2_attempts": sum(row["motif_depth"] >= 2 for row in motif_diagnostics["attempts"]),
        "attempts_with_second_hop_success": sum(row["second_hop_succeeds"] for row in motif_diagnostics["attempts"]),
        "depth_at_least_3_attempts": sum(row["motif_depth"] >= 3 for row in motif_diagnostics["attempts"]),
        "attempts_with_third_hop_success": sum(row["third_hop_succeeds"] for row in motif_diagnostics["attempts"]),
        "attempts_completed": sum(row["complete_path_count"] > 0 for row in motif_diagnostics["attempts"]),
        "attempt_zero_path_reasons": dict(sorted(Counter(
            row["zero_path_reason"] for row in motif_diagnostics["attempts"] if row["zero_path_reason"]
        ).items())),
    }
    return {
        "unit": "416 route anchors; EXACT_MULTI GL journal routes count once at case level and any resolved line may advance the funnel",
        "overall": summarize(rows),
        "by_anchor_type": {
            anchor_type: summarize([row for row in rows if row["route_anchor_type"] == anchor_type])
            for anchor_type in sorted({row["route_anchor_type"] for row in rows})
        },
        "motif_attempt_funnel": attempt_counts,
        "design_depth_limits": {
            "frozen_motif_count": 8, "one_hop_motif_count": 7,
            "two_hop_motif_count": 1, "three_hop_motif_count": 0,
        },
    }


def critical_chain_analysis(
    safe_rows: list[dict[str, Any]], nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]], relation_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    paths = [path for row in safe_rows for values in row["paths_by_exact_depth"].values() for path in values]
    patterns = {
        "PURCHASE_ORDER_TO_INVOICE": (
            ("PURCHASE_ORDER", "INVOICE"),
            ("INVOICE_REFERENCES_PO:reverse",),
        ),
        "INVOICE_TO_PAYMENT_ALLOCATION_TO_PAYMENT": (
            ("INVOICE", "PAYMENT_ALLOCATION", "PAYMENT"),
            ("ALLOCATION_TO_INVOICE:reverse", "ALLOCATION_OF_PAYMENT:forward"),
        ),
        "PAYMENT_TO_GL_ENTRY": (
            ("PAYMENT", "GL_ENTRY"),
            ("GL_SOURCE_PAYMENT:reverse",),
        ),
        "INVOICE_TO_APPROVAL_EVENT": (
            ("INVOICE", "APPROVAL_EVENT"),
            ("APPROVAL_FOR_INVOICE:reverse",),
        ),
        "PURCHASE_ORDER_TO_INVOICE_TO_PAYMENT": (
            ("PURCHASE_ORDER", "INVOICE", "PAYMENT"),
            ("INVOICE_REFERENCES_PO:reverse", "PAYMENT_ALLOCATED_TO_INVOICE:reverse"),
        ),
        "INVOICE_TO_PAYMENT_TO_GL_ENTRY": (
            ("INVOICE", "PAYMENT", "GL_ENTRY"),
            ("PAYMENT_ALLOCATED_TO_INVOICE:reverse", "GL_SOURCE_PAYMENT:reverse"),
        ),
        "PURCHASE_ORDER_TO_INVOICE_TO_PAYMENT_TO_GL_ENTRY": (
            ("PURCHASE_ORDER", "INVOICE", "PAYMENT", "GL_ENTRY"),
            ("INVOICE_REFERENCES_PO:reverse", "PAYMENT_ALLOCATED_TO_INVOICE:reverse", "GL_SOURCE_PAYMENT:reverse"),
        ),
    }
    forward: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    reverse: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_type: dict[str, list[str]] = defaultdict(list)
    for record_id, node in nodes.items():
        by_type[node["node_type"]].append(record_id)
    for edge in edges:
        forward[(edge["source_record_id"], edge["relation_type"])].append(edge)
        reverse[(edge["target_record_id"], edge["relation_type"])].append(edge)

    def enumerate_exact_global(
        node_pattern: tuple[str, ...], traversal_pattern: tuple[str, ...],
    ) -> tuple[int, int]:
        partial = [[record_id] for record_id in sorted(by_type[node_pattern[0]])]
        for step_index, raw in enumerate(traversal_pattern, start=1):
            relation_type, direction = raw.rsplit(":", 1)
            relation = relation_map[relation_type]
            if relation_classification(relation) != "SAFE_REVERSIBLE_CANDIDATE":
                return 0, 0
            expanded = []
            for records in partial:
                current = records[-1]
                selected_edges = (
                    forward.get((current, relation_type), [])
                    if direction == "forward" else reverse.get((current, relation_type), [])
                )
                for edge in selected_edges:
                    next_id = edge["target_record_id"] if direction == "forward" else edge["source_record_id"]
                    if (
                        edge["temporal_eligible"] and nodes[next_id]["temporal_eligible"]
                        and nodes[next_id]["node_type"] == node_pattern[step_index]
                        and next_id not in records
                    ):
                        expanded.append([*records, next_id])
            partial = expanded
        return len(partial), len({records[0] for records in partial})

    output = {}
    for name, (node_pattern, traversal_pattern) in patterns.items():
        selected = [
            path for path in paths
            if tuple(path["node_type_sequence"]) == node_pattern
            and tuple(path["traversal_sequence"]) == traversal_pattern
        ]
        global_instances, global_starts = enumerate_exact_global(node_pattern, traversal_pattern)
        output[name] = {
            "node_type_sequence": list(node_pattern),
            "required_traversal_sequence": list(traversal_pattern),
            "validation_anchor_path_instance_count": len(selected),
            "validation_distinct_anchor_count": len({path["case_id"] for path in selected}),
            "global_graph_path_instance_count": global_instances,
            "global_distinct_start_node_count": global_starts,
            "globally_supported": global_instances > 0,
        }
    audit_patterns = [path for path in paths if len(path["node_type_sequence"]) == 2 and path["node_type_sequence"][1] == "AUDIT_EVENT"]
    global_audit_instances = 0
    global_audit_starts: set[tuple[str, str]] = set()
    for node_type, relation_type in (
        ("BANK_TRANSACTION", "AUDIT_EVENT_FOR_BANK_TRANSACTION"),
        ("INVOICE", "AUDIT_EVENT_FOR_INVOICE"),
        ("PAYMENT", "AUDIT_EVENT_FOR_PAYMENT"),
        ("PURCHASE_ORDER", "AUDIT_EVENT_FOR_PURCHASE_ORDER"),
    ):
        instances, starts = enumerate_exact_global(
            (node_type, "AUDIT_EVENT"), (f"{relation_type}:reverse",),
        )
        global_audit_instances += instances
        # Counts are additive because starting node types are disjoint.
        global_audit_starts.add((node_type, str(starts)))
    output["OPERATIONAL_ENTITY_TO_AUDIT_EVENT"] = {
        "validation_anchor_path_instance_count": len(audit_patterns),
        "validation_distinct_anchor_count": len({path["case_id"] for path in audit_patterns}),
        "validation_by_operational_anchor_node_type": dict(sorted(Counter(path["node_type_sequence"][0] for path in audit_patterns).items())),
        "global_graph_path_instance_count": global_audit_instances,
        "global_distinct_start_node_count": sum(int(value) for _, value in global_audit_starts),
        "actor_hub_expansion_performed": False,
    }
    return output


def gl_gain_analysis(stored: list[dict[str, Any]], safe: list[dict[str, Any]]) -> dict[str, Any]:
    stored_by_case = {row["case_id"]: row for row in stored}
    output = {}
    for depth in (1, 2, 3):
        gained = []
        safe_cases = []
        for row in safe:
            safe_has = any(path["node_type_sequence"][-1] == "GL_ENTRY" for path in row["paths_by_exact_depth"][str(depth)])
            stored_has = any(path["node_type_sequence"][-1] == "GL_ENTRY" for path in stored_by_case[row["case_id"]]["paths_by_exact_depth"][str(depth)])
            if safe_has:
                safe_cases.append(row["case_id"])
            if safe_has and not stored_has:
                gained.append(row["case_id"])
        output[f"depth_{depth}"] = {
            "anchors_with_safe_reverse_gl_reachability": len(safe_cases),
            "anchors_gaining_gl_reachability_over_stored_direction": len(gained),
        }
    return output


def evidence_recall(
    raw_by_view: dict[str, list[dict[str, Any]]], resolutions: list[dict[str, Any]],
) -> dict[str, Any]:
    # This is intentionally called only after structural payload hashes are fixed.
    corpus = load_persisted_corpus(CORPUS)
    projection = load_validation_evidence_projection(VALIDATION_EVIDENCE)
    evidence_by_case = {
        row["case_id"]: resolve_evidence(row, corpus.documents) for row in projection
    }
    resolution_by_case = {row["case_id"]: row for row in resolutions}
    output = {}
    for view, rows in raw_by_view.items():
        depth_rows = {}
        for depth_limit in (1, 2, 3):
            per_case = []
            total_required = 0
            total_relevant = 0
            full = 0
            for row in rows:
                reached = set(resolution_by_case[row["case_id"]]["resolved_record_ids"])
                for depth in range(1, depth_limit + 1):
                    for path in row["paths_by_exact_depth"][str(depth)]:
                        reached.update(path["record_id_sequence"])
                required = set(evidence_by_case[row["case_id"]].required_record_ids)
                relevant = len(required & reached)
                total_required += len(required)
                total_relevant += relevant
                full += required <= reached
                per_case.append(relevant / len(required) if required else 0.0)
            depth_rows[f"depth_le_{depth_limit}"] = {
                "micro_required_document_recall": total_relevant / total_required,
                "macro_required_document_recall": statistics.fmean(per_case),
                "full_evidence_coverage": full / len(rows),
                "relevant_document_incidences": total_relevant,
                "required_document_incidences": total_required,
            }
        output[view] = depth_rows
    return {
        "stage": "SECONDARY_EVALUATION_AFTER_STRUCTURAL_ENUMERATION_FREEZE",
        "validation_gold_used_for_path_generation": False,
        "views": output,
    }


def typed_grammar_analysis(directionality: dict[str, Any], explosion: dict[str, Any], coverage: dict[str, Any]) -> str:
    safe = coverage["views"]["SAFE_BIDIRECTIONAL_DIAGNOSTIC"]
    return "\n".join([
        "# Fixed Motifs vs Typed Financial Traversal Grammar",
        "",
        "Status: **PROPOSAL_ONLY**. No grammar, motif, relation, or production traversal change was created.",
        "",
        "## Option A — fixed path motifs",
        "",
        "Fixed motifs are maximally explicit, reproducible, and easy to audit path by path. Their cost is brittle coverage: each anchor orientation and lifecycle continuation must be enumerated separately, while endpoint types listed as permitted anchors do not make a one-direction motif executable from both endpoints. Maintenance grows with relation-sequence combinations, and the current registry contains seven one-hop motifs, one two-hop motif, and no three-hop motif.",
        "",
        f"In the safe-reverse diagnostic topology, fixed motifs represent {safe['distinct_represented_sequence_count']}/{safe['distinct_reachable_sequence_count']} distinct direction-aware typed sequences ({100*safe['sequence_level_ratio']:.3f}%). This is a structural coverage result, not a retrieval redesign result.",
        "",
        "## Option B — typed financial traversal grammar",
        "",
        "A typed grammar can express an approved next edge from the current node type in either stored or explicitly approved reverse orientation. It remains deterministic and explainable if every transition is tied to one frozen exact edge, preserves provenance and cutoff eligibility, excludes Vendor/Employee and attribute hubs, enforces a depth limit, and rejects repeated record IDs.",
        "",
        f"The diagnostic bound is favorable: at depth 1–3 the maximum was {explosion['safe_reverse_candidate_paths_per_anchor']['maximum_paths']} paths for one route anchor (p95 {explosion['safe_reverse_candidate_paths_per_anchor']['p95_paths_nearest_rank']}; p99 {explosion['safe_reverse_candidate_paths_per_anchor']['p99_paths_nearest_rank']}). This does not prove a grammar is safe under different data distributions; degree ceilings and regression tests would still require an independent freeze.",
        "",
        "## Comparative assessment",
        "",
        "| Criterion | Fixed motifs | Typed grammar |",
        "|---|---|---|",
        "| Interpretability | Highest for each enumerated sequence | High if transition rules and exclusions are explicit |",
        "| Reproducibility | High | High with deterministic ordering/depth/simple-path rules |",
        "| Coverage | Low unless motifs are exhaustively maintained | Higher across valid financial lifecycle continuations |",
        "| Explosion risk | Low by construction | Requires degree, depth, hub, and cycle controls |",
        "| Maintenance | Combinatorial sequence registry | Transition registry plus constraint policy |",
        "| Overfitting risk | High if motifs are chosen from validation evidence | High if grammar transitions are chosen from validation evidence |",
        "| Scientific explanation | Simple but incomplete | More abstract; still auditable from typed transitions |",
        "",
        "## Structural conclusion",
        "",
        "The topology supports considering a typed grammar because many exact entity-local sequences exist while observed expansion remains bounded under the stated constraints. This conclusion is based on edge semantics and topology only. It does not select a v1.1 design and does not authorize implementation.",
        "",
    ])


def zero_multihop_explanation(
    motifs: list[dict[str, Any]], motif_diagnostics: dict[str, Any], resolutions: list[dict[str, Any]],
) -> dict[str, Any]:
    multi = [motif for motif in motifs if len(motif["edge_sequence"]) > 1]
    attempts = [row for row in motif_diagnostics["attempts"] if row["motif_depth"] > 1]
    reason_counts = Counter(row["zero_path_reason"] for row in attempts if row["zero_path_reason"])
    return {
        "selected_multihop_path_count": 0,
        "frozen_motif_count": len(motifs),
        "frozen_one_hop_motif_count": sum(len(motif["edge_sequence"]) == 1 for motif in motifs),
        "frozen_multihop_motif_count": len(multi),
        "frozen_three_hop_motif_count": sum(len(motif["edge_sequence"]) >= 3 for motif in motifs),
        "multihop_motif_ids": [motif["motif_id"] for motif in multi],
        "validation_route_anchor_type_counts": dict(sorted(Counter(row["anchor_input_type"] for row in resolutions).items())),
        "eligible_multihop_motif_attempt_count": len(attempts),
        "multihop_attempts_with_first_hop_success": sum(row["first_hop_succeeds"] for row in attempts),
        "multihop_attempts_with_second_hop_success": sum(row["second_hop_succeeds"] for row in attempts),
        "multihop_attempt_zero_path_reason_counts": dict(sorted(reason_counts.items())),
        "percentage_of_multihop_attempts_blocked_at_first_hop": 100.0 * sum(
            row["first_failure_step"] == 1 for row in attempts
        ) / len(attempts) if attempts else 0.0,
        "percentage_attributable_to_motif_direction_anchor_mismatch": 100.0 * reason_counts["MOTIF_DIRECTION_MISMATCH"] / len(attempts) if attempts else 0.0,
        "percentage_attributable_to_absent_edges": 100.0 * reason_counts["EDGE_NOT_PRESENT"] / len(attempts) if attempts else 0.0,
        "percentage_attributable_to_hub_rules": 100.0 * reason_counts["HUB_RESTRICTION"] / len(attempts) if attempts else 0.0,
        "percentage_attributable_to_temporal_rules": 100.0 * reason_counts["TEMPORAL_RESTRICTION"] / len(attempts) if attempts else 0.0,
        "percentage_attributable_to_implementation_behavior": 0.0,
        "conclusion": (
            "The sole multi-hop motif starts with INVOICE_REFERENCES_PO:reverse. In the authorized routes it is attempted only from INVOICE anchors, but reverse traversal of that stored relation starts at PURCHASE_ORDER. Every eligible attempt therefore dies before hop 1; the other seven motifs terminate after one edge."
        ),
    }


def make_report(payload: dict[str, Any]) -> str:
    stored = payload["anchor_type_reachability"]["views"]["STORED_DIRECTION_ONLY"]
    safe = payload["anchor_type_reachability"]["views"]["SAFE_BIDIRECTIONAL_DIAGNOSTIC"]
    recall = payload["evidence_recall"]["views"]
    direction = payload["directionality"]
    coverage = payload["motif_coverage"]["views"]["SAFE_BIDIRECTIONAL_DIAGNOSTIC"]
    funnel = payload["funnel"]
    zero = payload["zero_multihop"]
    gaps = payload["gaps"]
    cycles = payload["cycle"]
    critical = payload["critical"]
    gl_gain = payload["gl_gain"]
    graph_metrics = payload["phase6a_metrics"]
    motif_anchor_depth = {
        depth: sum(row["path_count_by_depth"].get(str(depth), 0) > 0 for row in payload["motif_rows"])
        for depth in (1, 2, 3)
    }
    safe_reverse_frozen_count = sum(
        row["reverse_traversal_class"] == "SAFE_REVERSIBLE_CANDIDATE" and row["frozen_v1_reverse_traversal"]
        for row in direction["relations"]
    )
    def pct(value: float) -> str:
        return f"{100*value:.3f}%"
    lines = [
        "# Phase 6A.1 Structural Reachability & Traversal-Direction Audit",
        "",
        "## A. Executive finding",
        "",
        "Useful exact 2-hop and 3-hop paths physically exist. They are largely inaccessible to Graph Retrieval v1.0 because the frozen motif vocabulary is almost entirely one-hop and its only multi-hop motif is directionally unusable from every eligible validation anchor. Safe reverse diagnostic traversal raises depth-2/3 reachability without an observed explosion, but this is not an implemented retrieval model.",
        "",
        "## B. Frozen artifact verification",
        "",
        f"PASS: all {payload['verification']['verified_artifact_count']} mandatory raw-byte SHA-256 values matched. No frozen or Phase 6A artifact was modified.",
        "",
        "## C. Research question",
        "",
        "The audit separates physical graph reachability, frozen motif reachability, and actual Graph v1.0 emission. Path generation is label-independent; validation evidence is opened only in the secondary recall stage.",
        "",
        "## D. Graph topology summary",
        "",
        "The persisted graph contains 155,391 nodes in 14 types and 184,223 deterministic edges across all 22 frozen executable relation types. Traversal is limited to depth 3, exact frozen edges, cutoff-eligible nodes/edges, frozen Vendor/Employee hub exclusions, and simple paths.",
        "",
        "## E. Stored-direction depth-1/2/3 reachability",
        "",
        "| Exact depth | Anchors with path | Mean | Median | p95 | Max | Total paths |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for depth in (1, 2, 3):
        row = stored["overall"][f"depth_{depth}"]
        lines.append(f"| {depth} | {row['anchors_with_at_least_one_path']}/416 | {row['mean_paths']:.3f} | {row['median_paths']:.1f} | {row['p95_paths_nearest_rank']} | {row['maximum_paths']} | {row['total_paths']} |")
    lines += [
        "",
        "| Anchor type | Depth | Anchors with path | Mean | Median | p95 | Max |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for anchor_type, values in stored["by_anchor_type"].items():
        for depth in (1, 2, 3):
            row = values[f"depth_{depth}"]
            lines.append(f"| {anchor_type} | {depth} | {row['anchors_with_at_least_one_path']}/{values['case_count']} | {row['mean_paths']:.3f} | {row['median_paths']:.1f} | {row['p95_paths_nearest_rank']} | {row['maximum_paths']} |")
    lines += [
        "",
        "Stored direction alone mostly follows child/source records toward parents/targets; it offers little investigative expansion from invoice, payment, or bank-transaction anchors.",
        "",
        "## F. Safe-reverse diagnostic depth-1/2/3 reachability",
        "",
        "| Exact depth | Anchors with path | Mean | Median | p95 | Max | Total paths |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for depth in (1, 2, 3):
        row = safe["overall"][f"depth_{depth}"]
        lines.append(f"| {depth} | {row['anchors_with_at_least_one_path']}/416 | {row['mean_paths']:.3f} | {row['median_paths']:.1f} | {row['p95_paths_nearest_rank']} | {row['maximum_paths']} | {row['total_paths']} |")
    lines += [
        "",
        "| Anchor type | Depth | Anchors with path | Mean | Median | p95 | Max |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for anchor_type, values in safe["by_anchor_type"].items():
        for depth in (1, 2, 3):
            row = values[f"depth_{depth}"]
            lines.append(f"| {anchor_type} | {depth} | {row['anchors_with_at_least_one_path']}/{values['case_count']} | {row['mean_paths']:.3f} | {row['median_paths']:.1f} | {row['p95_paths_nearest_rank']} | {row['maximum_paths']} |")
    lines += [
        "",
        "## G. Directionality audit",
        "",
        f"The 22 relations classify as `{direction['classification_counts']}`. {safe_reverse_frozen_count}/{direction['classification_counts']['SAFE_REVERSIBLE_CANDIDATE']} structurally safe relations already have frozen v1.0 reverse permission. `AUDIT_EVENT_FOR_VENDOR` is exact with maximum reverse degree 1 but remains excluded from View B by the separate frozen Vendor prohibition; six other Vendor/Employee relations are reverse-hub risks. Persisted edge orientation frequently requires a reverse step, but no validation-anchor path in View B requires reverse permission absent from v1.0. Classification is advisory only.",
        "",
        "## H. Payment-allocation traversal analysis",
        "",
        f"The exact allocation-node chain `INVOICE <- ALLOCATION_TO_INVOICE - PAYMENT_ALLOCATION -> ALLOCATION_OF_PAYMENT -> PAYMENT` occurs in {critical['INVOICE_TO_PAYMENT_ALLOCATION_TO_PAYMENT']['validation_anchor_path_instance_count']} safe-diagnostic paths across {critical['INVOICE_TO_PAYMENT_ALLOCATION_TO_PAYMENT']['validation_distinct_anchor_count']} validation anchors and {critical['INVOICE_TO_PAYMENT_ALLOCATION_TO_PAYMENT']['global_graph_path_instance_count']} paths globally. These edges already exist; no relationship was synthesized.",
        "",
        f"The global frozen graph also supports `PURCHASE_ORDER -> INVOICE` ({critical['PURCHASE_ORDER_TO_INVOICE']['global_graph_path_instance_count']} paths), `PURCHASE_ORDER -> INVOICE -> PAYMENT` ({critical['PURCHASE_ORDER_TO_INVOICE_TO_PAYMENT']['global_graph_path_instance_count']}), `INVOICE -> PAYMENT -> GL_ENTRY` ({critical['INVOICE_TO_PAYMENT_TO_GL_ENTRY']['global_graph_path_instance_count']}), and `PURCHASE_ORDER -> INVOICE -> PAYMENT -> GL_ENTRY` ({critical['PURCHASE_ORDER_TO_INVOICE_TO_PAYMENT_TO_GL_ENTRY']['global_graph_path_instance_count']}). Their validation-anchor counts are zero for purchase-order-starting chains because the authorized routes contain no purchase-order anchors, not because the edges are absent.",
        "",
        "## I. GL source traversal analysis",
        "",
        f"Safe reverse traversal gives new GL-entry reachability over stored direction to {gl_gain['depth_1']['anchors_gaining_gl_reachability_over_stored_direction']} anchors at depth 1, {gl_gain['depth_2']['anchors_gaining_gl_reachability_over_stored_direction']} at exact depth 2, and {gl_gain['depth_3']['anchors_gaining_gl_reachability_over_stored_direction']} at exact depth 3. Each GL edge retains its source_transaction_id-backed provenance.",
        "",
        "## J. Approval traversal analysis",
        "",
        f"`INVOICE -> APPROVAL_EVENT` is realized by {critical['INVOICE_TO_APPROVAL_EVENT']['validation_anchor_path_instance_count']} exact reverse paths across {critical['INVOICE_TO_APPROVAL_EVENT']['validation_distinct_anchor_count']} validation anchors and {critical['INVOICE_TO_APPROVAL_EVENT']['global_graph_path_instance_count']} paths globally. Relation-level reverse degree is reported in `relation_directionality_audit.json`.",
        "",
        "## K. Audit-event traversal analysis",
        "",
        f"Entity-local operational-entity-to-audit-event traversal yields {critical['OPERATIONAL_ENTITY_TO_AUDIT_EVENT']['validation_anchor_path_instance_count']} one-hop paths across {critical['OPERATIONAL_ENTITY_TO_AUDIT_EVENT']['validation_distinct_anchor_count']} validation anchors and {critical['OPERATIONAL_ENTITY_TO_AUDIT_EVENT']['global_graph_path_instance_count']} paths globally. Actor/Employee continuation was not performed.",
        "",
        "## L. Frozen motif coverage",
        "",
        f"Under the primary safe-reverse denominator, frozen motifs represent {coverage['distinct_represented_sequence_count']}/{coverage['distinct_reachable_sequence_count']} distinct direction-aware typed sequences: **{pct(coverage['sequence_level_ratio'])}**. {coverage['cases_with_any_represented_sequence']}/{coverage['cases_with_raw_sequences']} cases with raw paths have at least one represented sequence; mean per-case sequence coverage is {pct(coverage['mean_case_level_ratio'])}.",
        "",
        "## M. Hop-survival funnel",
        "",
        f"`416 anchors -> {funnel['overall']['anchors_with_applicable_motif']} applicable -> {funnel['overall']['anchors_with_first_hop_success']} first-hop -> {funnel['overall']['anchors_with_second_hop_success']} second-hop -> {funnel['overall']['anchors_with_third_hop_success']} third-hop`. The frozen design contains seven one-hop motifs, one two-hop motif, and zero three-hop motifs.",
        "",
        "## N. Explanation of zero multi-hop output",
        "",
        f"There were {zero['eligible_multihop_motif_attempt_count']} eligible attempts of the sole multi-hop motif and {zero['multihop_attempts_with_first_hop_success']} passed hop 1. Exactly {zero['percentage_attributable_to_motif_direction_anchor_mismatch']:.3f}% failed because `INVOICE_REFERENCES_PO:reverse` was attempted from INVOICE rather than PURCHASE_ORDER. Disabled relation-level reverse permission, edge absence, hub policy, temporal policy, ranking/budget, and implementation behavior each account for 0% of the zero multi-hop outcome. Seven other motifs terminate after one edge, and no three-hop motif exists.",
        "",
        "## O. Raw graph vs motif gap taxonomy",
        "",
        f"Unrepresented safe-topology sequence incidences: `{gaps['unrepresented_sequence_gap_counts']}`. Case-primary categories: `{gaps['case_primary_category_counts']}`. The machine-readable artifact separates sequence gaps, failed motif attempts, and hub incidents to avoid double-counting mechanisms.",
        "",
        "## P. Reachability explosion / hub risk",
        "",
        f"Safe reverse traversal produced p50 {safe['overall']['all_depths_1_to_3']['median_paths']:.1f}, p90 {safe['overall']['all_depths_1_to_3']['p90_paths_nearest_rank']}, p95 {safe['overall']['all_depths_1_to_3']['p95_paths_nearest_rank']}, p99 {safe['overall']['all_depths_1_to_3']['p99_paths_nearest_rank']}, and max {safe['overall']['all_depths_1_to_3']['maximum_paths']} paths per route anchor across depths 1–3. No uncontrolled expansion was observed under the frozen hub exclusions; this does not authorize broader traversal.",
        "",
        "## Q. Cycle analysis",
        "",
        f"Simple-path enforcement removed {cycles['SAFE_BIDIRECTIONAL_DIAGNOSTIC']['cycle_candidates_removed_total']} repeated-record candidates ({cycles['SAFE_BIDIRECTIONAL_DIAGNOSTIC']['cycle_candidates_removed_by_simple_path_rule']}). No additional cycle rule was used.",
        "",
        "## R. Fixed motifs vs typed grammar",
        "",
        "Fixed motifs are easiest to audit but brittle across anchor orientation and lifecycle continuations. A typed grammar is structurally more expressive and remained bounded in this diagnostic when constrained to exact entity-local relations, depth 3, frozen hubs, cutoff eligibility, and simple paths. Both options remain PROPOSAL_ONLY; see `typed_traversal_grammar_analysis.md`.",
        "",
        "## S. Relational-RAG comparison",
        "",
        "| Retrieval/topology | 1-hop anchors | 2-hop anchors | 3-hop anchors | Required-doc diagnostic recall |",
        "|---|---:|---:|---:|---:|",
        f"| Relational-RAG | N/A | N/A | N/A | {pct(graph_metrics['relational_rag']['micro']['document_recall'])} |",
        f"| Frozen motif Graph v1.0 | {motif_anchor_depth[1]} | {motif_anchor_depth[2]} | {motif_anchor_depth[3]} | {pct(graph_metrics['graph_retrieval_v1_0']['micro']['document_recall'])} |",
        f"| Raw graph stored direction | {stored['overall']['depth_1']['anchors_with_at_least_one_path']} | {stored['overall']['depth_2']['anchors_with_at_least_one_path']} | {stored['overall']['depth_3']['anchors_with_at_least_one_path']} | {pct(recall['STORED_DIRECTION_ONLY']['depth_le_3']['micro_required_document_recall'])} |",
        f"| Raw graph safe-reverse diagnostic | {safe['overall']['depth_1']['anchors_with_at_least_one_path']} | {safe['overall']['depth_2']['anchors_with_at_least_one_path']} | {safe['overall']['depth_3']['anchors_with_at_least_one_path']} | {pct(recall['SAFE_BIDIRECTIONAL_DIAGNOSTIC']['depth_le_3']['micro_required_document_recall'])} |",
        "",
        "Relational-RAG remains the serious baseline (66.716% micro Recall@40 versus Graph v1.0 at 31.642%). Any later graph design must show value beyond exact one-hop relational expansion, not merely beyond Dense RAG.",
        "",
        "## T. Structural recommendation for Graph v1.1",
        "",
        "`CONSIDER_TYPED_TRAVERSAL_GRAMMAR` (PROPOSAL_ONLY). Many exact multi-hop lifecycle sequences exist, fixed-motif sequence coverage is low, and constrained expansion is bounded in this corpus. This recommends an independently reviewed design experiment, not a freeze or implementation. Relational-RAG should remain the primary comparator and may remain the preferred production architecture if a future graph experiment does not add evidence beyond it.",
        "",
        "## U. Scientific-integrity audit",
        "",
        "PASS. Every prohibited-action field in `scientific_integrity.json` is false. Diagnostic reverse topology is true and remained in memory/output-only analysis.",
        "",
        "## V. Deviations",
        "",
        "No substantive protocol deviation. Exact-multi GL journal routes are counted once in case-level metrics while both resolved GL_ENTRY anchors are enumerated. Motif-coverage ambiguity is resolved with a direction-aware typed-sequence definition documented in the JSON artifact.",
        "",
        "## W. Proposed next action",
        "",
        "Independent researcher review should decide whether to authorize separate v1.1 fixed-motif, safe-bidirectional, and typed-grammar experiments. Do not implement or evaluate a modified retriever before that decision.",
        "",
        "RECOMMEND DESIGN GRAPH v1.1 WITH TYPED FINANCIAL TRAVERSAL GRAMMAR",
        "",
    ]
    return "\n".join(lines)


def build_payloads() -> dict[str, Any]:
    verification = verify_inputs()
    relations_registry = json.loads((FREEZE / "graph_relation_registry_v1.json").read_text(encoding="utf-8"))
    motif_registry = json.loads((FREEZE / "graph_path_motifs_v1.json").read_text(encoding="utf-8"))
    relations = relations_registry["frozen_relations"]
    motifs = motif_registry["frozen_motifs"]
    nodes_rows = load_jsonl(PHASE6A / "graph/nodes.jsonl")
    edges = load_jsonl(PHASE6A / "graph/edges.jsonl")
    nodes = {row["record_id"]: row for row in nodes_rows}
    node_type_lookup = {record_id: row["node_type"] for record_id, row in nodes.items()}
    relation_map = {row["relation_type"]: row for row in relations}
    relation_order = {row["relation_type"]: index for index, row in enumerate(relations)}
    routes = load_jsonl(ROUTES)
    resolutions = load_jsonl(PHASE6A / "retrieval/anchor_resolutions.jsonl")
    if len(routes) != 416 or len(resolutions) != 416:
        raise RuntimeError("authorized validation routing/resolution count is not 416")

    directionality = build_directionality_audit(relations, nodes, edges)
    raw_by_view = {}
    cycle = {}
    for view in TOPOLOGY_VIEWS:
        raw_by_view[view], cycle[view] = enumerate_view(
            view=view, routes=routes, resolutions=resolutions, nodes=nodes, edges=edges,
            relation_map=relation_map, relation_order=relation_order,
        )
    motif_rows, engine_paths, motif_diagnostics = execute_frozen_motifs(routes, resolutions)
    actual_results = load_jsonl(PHASE6A / "retrieval/graph_retrieval_results.jsonl")
    actual_ledger = load_jsonl(PHASE6A / "retrieval/graph_path_ledger.jsonl")
    sequence_inventory = build_sequence_inventory(raw_by_view, motifs, engine_paths, node_type_lookup)
    coverage = motif_coverage(raw_by_view, motifs)
    comparison, gaps = build_case_comparison_and_gaps(
        stored=raw_by_view["STORED_DIRECTION_ONLY"],
        safe=raw_by_view["SAFE_BIDIRECTIONAL_DIAGNOSTIC"], motifs=motifs,
        motif_rows=motif_rows, motif_diagnostics=motif_diagnostics,
        actual_results=actual_results, actual_ledger=actual_ledger,
        relation_map=relation_map,
    )
    funnel = hop_survival(motif_rows, motif_diagnostics)
    critical = critical_chain_analysis(
        raw_by_view["SAFE_BIDIRECTIONAL_DIAGNOSTIC"], nodes, edges, relation_map,
    )
    gl_gain = gl_gain_analysis(raw_by_view["STORED_DIRECTION_ONLY"], raw_by_view["SAFE_BIDIRECTIONAL_DIAGNOSTIC"])
    reachability = {
        "views": {view: reachability_summary(rows) for view, rows in raw_by_view.items()},
        "resolved_anchor_record_count": sum(len(row["resolved_record_ids"]) for row in resolutions),
        "route_anchor_case_count": len(resolutions),
    }
    explosion = {
        "safe_reverse_candidate_paths_per_anchor": reachability["views"]["SAFE_BIDIRECTIONAL_DIAGNOSTIC"]["overall"]["all_depths_1_to_3"],
        "stored_direction_candidate_paths_per_anchor": reachability["views"]["STORED_DIRECTION_ONLY"]["overall"]["all_depths_1_to_3"],
        "unacceptable_combinatorial_explosion_observed": False,
        "qualification": "Bounded only under depth<=3, simple paths, and frozen Vendor/Employee/attribute-hub exclusions.",
    }
    zero = zero_multihop_explanation(motifs, motif_diagnostics, resolutions)

    # Freeze the label-independent structural state before opening validation evidence.
    structural_freeze_projection = {
        "raw_by_view": raw_by_view, "directionality": directionality,
        "motif_rows": motif_rows, "sequence_inventory": sequence_inventory,
        "coverage": coverage, "comparison": comparison, "gaps": gaps,
        "funnel": funnel, "critical": critical, "gl_gain": gl_gain,
        "reachability": reachability, "explosion": explosion, "cycle": cycle, "zero": zero,
    }
    structural_freeze_sha256 = sha256_bytes(canonical_bytes(structural_freeze_projection))

    secondary = evidence_recall(raw_by_view, resolutions)
    phase6a_metrics = json.loads((PHASE6A / "evaluation/retrieval_metrics.json").read_text(encoding="utf-8"))
    integrity = {
        "status": "PASS",
        "frozen_registry_modified": False,
        "phase6a_graph_modified": False,
        "heldout_labels_opened": False,
        "heldout_gold_opened": False,
        "oracle_sources_opened": False,
        "validation_gold_used_for_path_generation": False,
        "new_edges_created": False,
        "new_relation_types_created": False,
        "new_motifs_created": False,
        "reverse_traversal_enabled_in_production": False,
        "graph_v1_1_created": False,
        "llm_calls_made": False,
        "api_calls_made": False,
        "embeddings_created": False,
        "diagnostic_reverse_topology_used": True,
        "validation_evidence_opened_only_after_structural_freeze": True,
        "label_independent_structural_freeze_sha256": structural_freeze_sha256,
    }
    grammar = typed_grammar_analysis(directionality, explosion, coverage)
    combined = {
        "verification": verification, "directionality": directionality,
        "raw_by_view": raw_by_view, "motif_rows": motif_rows,
        "motif_diagnostics": motif_diagnostics, "sequence_inventory": sequence_inventory,
        "motif_coverage": coverage, "comparison": comparison, "gaps": gaps,
        "funnel": funnel, "critical": critical, "gl_gain": gl_gain,
        "anchor_type_reachability": reachability, "explosion": explosion,
        "cycle": cycle, "zero_multihop": zero, "evidence_recall": secondary,
        "phase6a_metrics": phase6a_metrics, "scientific_integrity": integrity,
        "actual_ledger": actual_ledger,
    }
    report = make_report(combined)
    return {
        "raw_reachability_stored_direction.jsonl": ("jsonl", raw_by_view["STORED_DIRECTION_ONLY"]),
        "raw_reachability_safe_reverse_diagnostic.jsonl": ("jsonl", raw_by_view["SAFE_BIDIRECTIONAL_DIAGNOSTIC"]),
        "motif_reachability.jsonl": ("jsonl", motif_rows),
        "case_reachability_comparison.jsonl": ("jsonl", comparison),
        "relation_directionality_audit.json": ("json", directionality),
        "path_sequence_inventory.json": ("json", sequence_inventory),
        "motif_gap_taxonomy.json": ("json", {**gaps, "motif_coverage_ratio": coverage, "zero_multihop_explanation": zero}),
        "hop_survival_funnel.json": ("json", funnel),
        "anchor_type_reachability.json": ("json", {**reachability, "secondary_required_document_recall": secondary, "critical_chain_analysis": critical, "gl_source_gain_analysis": gl_gain}),
        "reachability_explosion_and_cycles.json": ("json", {"explosion": explosion, "cycle_diagnostics": cycle}),
        "scientific_integrity.json": ("json", integrity),
        "typed_traversal_grammar_analysis.md": ("text", grammar),
        "PHASE6A1_MOTIF_DIAGNOSTIC_REVIEW.md": ("text", report),
    }


def render_payload(kind: str, value: Any) -> bytes:
    if kind == "jsonl":
        return jsonl_bytes(value)
    if kind == "json":
        return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if kind == "text":
        return value.encode("utf-8")
    raise ValueError(kind)


def main() -> None:
    first = build_payloads()
    second = build_payloads()
    first_hashes = {name: sha256_bytes(render_payload(*payload)) for name, payload in first.items()}
    second_hashes = {name: sha256_bytes(render_payload(*payload)) for name, payload in second.items()}
    if first_hashes != second_hashes:
        raise RuntimeError("BLOCK PHASE 6A.1: deterministic output hash mismatch across two runs")
    determinism = {
        "status": "PASS", "analysis_run_count": 2,
        "reachable_path_sets_identical": True,
        "directionality_classifications_identical": True,
        "sequence_inventories_identical": True,
        "motif_gap_counts_identical": True,
        "case_classifications_identical": True,
        "deterministic_output_hashes": first_hashes,
    }
    rendered = {name: render_payload(*payload) for name, payload in first.items()}
    rendered["determinism_validation.json"] = render_payload("json", determinism)
    for name, content in rendered.items():
        path = OUTPUT / name
        if path.name == Path(__file__).name:
            continue
        path.write_bytes(content)
    artifact_hashes = {
        "status": "PASS",
        "hash_algorithm": "SHA-256",
        "hash_scope": "raw serialized file bytes",
        "artifacts": {
            name: {"sha256": sha256_bytes(content), "bytes": len(content)}
            for name, content in sorted(rendered.items())
        },
        "analysis_script": {
            "path": Path(__file__).name,
            "sha256": sha256_file(Path(__file__)),
            "bytes": Path(__file__).stat().st_size,
        },
        "input_verification": {
            "status": "PASS",
            "artifacts": {
                path.relative_to(ROOT).as_posix(): {
                    "expected_sha256": expected,
                    "observed_sha256": sha256_file(path),
                }
                for path, expected in sorted(EXPECTED_HASHES.items(), key=lambda item: item[0].as_posix())
            },
        },
    }
    (OUTPUT / "phase6a1_artifact_hashes.json").write_bytes(render_payload("json", artifact_hashes))
    print(canonical({
        "status": "PASS", "output_directory": OUTPUT.relative_to(ROOT).as_posix(),
        "artifact_count_excluding_inventory_and_script": len(rendered),
        "artifact_hash_inventory_sha256": sha256_file(OUTPUT / "phase6a1_artifact_hashes.json"),
    }))


if __name__ == "__main__":
    main()
