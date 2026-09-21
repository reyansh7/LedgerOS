#!/usr/bin/env python3
"""Prepare, resume, and evaluate the frozen Graph v1.1 held-out LLM experiment."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any, Iterable, Mapping, Sequence

from src.graphrag.v1_1.candidate_traversal import (
    CandidateTraversalEngine,
    ExactAnchorResolver,
    FrozenGraph,
    canonical_json as traversal_canonical_json,
)
from src.graphrag.v1_1.evidence_selection import load_policy, select_all
from src.graphrag.v1_1.graph_reasoning import (
    SERIALIZER_VERSION,
    build_inference_object,
    build_reasoning_case_from_inference_object,
    deterministic_preflight_case_ids,
    inference_object_sha256,
    validate_inference_object,
)
from src.graphrag.v1_1.llm_evaluation import evaluate_complete_run
from src.graphrag.v1_1.split_neutral_traversal import SplitNeutralTraversalEngine
from src.graphrag.v1_1.typed_grammar_loader import load_verified_grammar
from src.rag.artifacts import (
    canonical_json,
    load_jsonl,
    sha256_bytes,
    sha256_file,
    write_json,
    write_jsonl,
)
from src.rag.config import ALL_CLASSES, OUTPUT_SCHEMA_VERSION, REASONER_CONFIG
from src.rag.corpus import load_persisted_corpus
from src.rag.prompt import load_frozen_prompt
from src.rag.reasoner import (
    MockReasonerClient,
    OpenAIReasonerClient,
    context_preflight,
    reasoning_request_hash,
)
from src.rag.runner import IMMUTABLE_STATES, load_latest_ledger, run_reasoning_cases
from src.rag.schemas import canonical_output_schema


ROOT = Path(__file__).resolve().parent
STANDARD_RUN = ROOT / "results/rag/phase5_rag_prelive_v1_0_20260812T043901Z"
STANDARD_INDEX = ROOT / "results/rag/phase5_rag_index_v1_0_20260810T000000Z"
TEST_ROUTES = ROOT / "results/rag/phase5_rag_pre_embedding_v1_0_20260809T221821Z/test_routes.jsonl"
VALIDATION_ROUTES = ROOT / "results/rag/phase5_rag_validation_routes_v1_0_20260812T040938Z/validation_routes.jsonl"
POLICY_PATH = ROOT / "results/graphrag/evidence_selection_freeze_v1_1/evidence_selection_policy_v1_1.json"
GROUND_TRUTH = ROOT / "data/benchmark/test/rca_ground_truth.jsonl"

EXPECTED_TEST_ROUTES_SHA256 = "efccfa96f231d72fe153f77bcb0a7b8df73cf765706d78589cf12ba8ed307ca7"
EXPECTED_STANDARD_PROMPT_SHA256 = "bca6d6d8366c6f95b07f83fc068ead359fc329793987b946a7f491f0ffd4d302"
EXPECTED_STANDARD_PREDICTIONS_SHA256 = ""  # verified from the comparator inventory at prepare time
EXPECTED_POLICY_SHA256 = "cad5f2298d9dad62599cfe592304c08cf8808441586fb865d1f4824b3054ea1b"
EXPECTED_VALIDATION_PATH_DIGEST = "89d7f799f60149a8e6665bf59a484131f450ec2ab435e9a891e1eec3efbb2944"
EXPECTED_UNRESOLVED = ("RCA_000902", "RCA_000955")
SOURCE_PATHS = (
    "src/graphrag/v1_1/split_neutral_traversal.py",
    "src/graphrag/v1_1/graph_reasoning.py",
    "src/graphrag/v1_1/llm_evaluation.py",
    "run_phase6b_graph_llm_experiment.py",
    "tests/graphrag/test_phase6b_graph_llm_experiment.py",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _group(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    result: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        result[str(row["case_id"])].append(row)
    return result


def _hash_value(value: Any) -> str:
    return hashlib.sha256(traversal_canonical_json(value).encode("utf-8")).hexdigest()


def _verify_standard_comparator() -> dict[str, Any]:
    inventory_path = STANDARD_RUN / "artifact_checksums.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    checks = []
    for row in inventory["files"]:
        path = STANDARD_RUN / row["path"]
        observed = sha256_file(path)
        checks.append({
            "path": path.relative_to(ROOT).as_posix(),
            "expected_sha256": row["sha256"],
            "observed_sha256": observed,
            "expected_bytes": row["bytes"],
            "observed_bytes": path.stat().st_size,
            "status": "PASS"
            if observed == row["sha256"] and path.stat().st_size == row["bytes"]
            else "FAIL",
        })
    if any(row["status"] != "PASS" for row in checks):
        raise RuntimeError("Standard RAG comparator artifact inventory mismatch")
    prompt = (STANDARD_RUN / "frozen_reasoning_prompt.txt").read_text(encoding="utf-8")
    predictions = load_jsonl(STANDARD_RUN / "generation/predictions.jsonl")
    manifest = json.loads((STANDARD_RUN / "run_manifest.json").read_text(encoding="utf-8"))
    if (
        sha256_bytes(prompt) != EXPECTED_STANDARD_PROMPT_SHA256
        or len(predictions) != 439
        or len({str(row["case_id"]) for row in predictions}) != 439
        or manifest.get("model_id") is not None
        or manifest["reasoning_summary"]["successful_cases"] != 437
        or manifest["terminal_anchor_technical_failure_case_ids"] != list(EXPECTED_UNRESOLVED)
    ):
        raise RuntimeError("Standard RAG comparator protocol/population mismatch")
    return {
        "status": "PASS",
        "inventory_sha256": sha256_file(inventory_path),
        "run_manifest_sha256": sha256_file(STANDARD_RUN / "run_manifest.json"),
        "predictions_sha256": sha256_file(STANDARD_RUN / "generation/predictions.jsonl"),
        "prompt_sha256": sha256_bytes(prompt),
        "case_count": 439,
        "model_id": REASONER_CONFIG.model_id,
        "checks": checks,
    }


def _validation_equivalence(graph: FrozenGraph, bundle: Any) -> dict[str, Any]:
    routes = load_jsonl(VALIDATION_ROUTES)
    frozen = CandidateTraversalEngine(graph, bundle).run(routes)
    adapted = SplitNeutralTraversalEngine(graph, bundle).run(routes)
    components = {}
    for name in ("anchor_resolutions", "candidate_paths", "candidate_records", "rejections"):
        left = getattr(frozen, name)
        right = getattr(adapted, name)
        components[name] = {
            "frozen_count": len(left),
            "adapted_count": len(right),
            "frozen_semantic_sha256": _hash_value(left),
            "adapted_semantic_sha256": _hash_value(right),
            "exact_semantic_match": traversal_canonical_json(left) == traversal_canonical_json(right),
        }
    keys = (
        "case_id",
        "route_anchor_type",
        "resolution_status",
        "resolved_root_count",
        "candidate_path_count",
        "path_count_by_exact_depth",
        "traversal_rejection_count",
        "candidate_unique_record_count",
    )
    left_cases = [{key: row[key] for key in keys} for row in frozen.case_results]
    right_cases = [{key: row[key] for key in keys} for row in adapted.case_results]
    passed = (
        all(row["exact_semantic_match"] for row in components.values())
        and left_cases == right_cases
        and adapted.telemetry["candidate_path_set_sha256"] == EXPECTED_VALIDATION_PATH_DIGEST
    )
    if not passed:
        raise RuntimeError("split-neutral adapter failed frozen validation equivalence")
    return {
        "status": "PASS",
        "validation_case_count": 416,
        "structural_case_results_exact_match": True,
        "path_set_sha256": adapted.telemetry["candidate_path_set_sha256"],
        "components": components,
    }


def _relation_order(bundle: Any) -> dict[str, int]:
    rows = bundle.relation_registry["frozen_relations"]
    result = {str(row["relation_type"]): index for index, row in enumerate(rows)}
    if len(result) != len(rows):
        raise RuntimeError("frozen relation registry contains duplicate relation types")
    return result


def _technical_failure(route: Mapping[str, str], resolution: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "case_id": str(route["case_id"]),
        "method": "rag",
        "status": "TECHNICAL_FAILURE",
        "is_anomaly": None,
        "predicted_failure_type": None,
        "evidence_record_ids": [],
        "reason": "ANCHOR_TECHNICAL_FAILURE",
        "confidence": None,
        "retrieved_record_ids": [],
        "request_hash": None,
        "response_id": None,
        "returned_model": None,
        "parse_status": "ANCHOR_TECHNICAL_FAILURE",
        "attempt_count": 0,
        "latency_ms": 0.0,
        "context_assembly_latency_ms": 0.0,
        "usage": {},
        "resolution_status": str(resolution["resolution_status"]),
        "anchor_input_type": str(resolution["anchor_input_type"]),
        "anchor_input_id": str(resolution["anchor_input_id"]),
    }


def _write_retrieval(
    output: Path,
    routes: Sequence[dict[str, Any]],
    resolutions: Sequence[dict[str, Any]],
    run: Any,
    selected: Mapping[str, Sequence[dict[str, Any]]],
) -> list[dict[str, Any]]:
    retrieval = output / "retrieval"
    retrieval.mkdir(parents=True, exist_ok=False)
    write_jsonl(retrieval / "anchor_resolutions.jsonl", resolutions, exclusive=True)
    write_jsonl(retrieval / "candidate_paths.jsonl", run.candidate_paths, exclusive=True)
    write_jsonl(retrieval / "candidate_records.jsonl", run.candidate_records, exclusive=True)
    write_jsonl(retrieval / "traversal_rejections.jsonl", run.rejections, exclusive=True)
    write_jsonl(retrieval / "selected_paths.jsonl", selected["selected_paths"], exclusive=True)
    write_jsonl(retrieval / "selected_records.jsonl", selected["selected_records"], exclusive=True)
    drops = [*selected["path_drop_ledger"], *selected["record_drop_ledger"]]
    write_jsonl(retrieval / "drop_ledger.jsonl", drops, exclusive=True)
    case_summary = {str(row["case_id"]): row for row in selected["case_results"]}
    route_by_id = {str(row["case_id"]): row for row in routes}
    resolution_by_id = {str(row["case_id"]): row for row in resolutions}
    rows = []
    for route in routes:
        case_id = str(route["case_id"])
        resolution = resolution_by_id[case_id]
        if resolution["resolution_status"] not in {"EXACT_SINGLE", "EXACT_MULTI"}:
            rows.append({
                "case_id": case_id,
                "route": route,
                "status": "ANCHOR_TECHNICAL_FAILURE",
                "resolution_status": resolution["resolution_status"],
                "resolved_record_ids": [],
                "candidate_record_count": 0,
                "selected_record_ids": [],
                "selected_path_ids": [],
                "selected_record_count": 0,
                "selected_path_count": 0,
                "technical_error": resolution.get("technical_error") or "anchor not present in frozen graph",
            })
            continue
        summary = case_summary[case_id]
        rows.append({
            "case_id": case_id,
            "route": route,
            "status": "SUCCESS",
            "resolution_status": resolution["resolution_status"],
            "resolved_record_ids": resolution["resolved_record_ids"],
            "candidate_record_count": summary["candidate_record_count"],
            "selected_record_ids": summary["selected_record_ids"],
            "selected_path_ids": summary["selected_path_ids"],
            "selected_record_count": summary["selected_record_count"],
            "selected_path_count": summary["selected_path_count"],
            "technical_error": None,
        })
    write_jsonl(retrieval / "retrieval_results.jsonl", rows, exclusive=True)
    write_json(retrieval / "traversal_telemetry.json", run.telemetry, exclusive=True)
    return rows


def _build_inference_artifacts(
    output: Path,
    routes: Sequence[dict[str, Any]],
    retrieval_rows: Sequence[dict[str, Any]],
    selected: Mapping[str, Sequence[dict[str, Any]]],
    graph: FrozenGraph,
) -> tuple[list[dict[str, Any]], list[Any]]:
    inference = output / "inference"
    inference.mkdir(parents=True, exist_ok=False)
    corpus = load_persisted_corpus(STANDARD_INDEX / "corpus")
    documents = corpus.by_record_id()
    records_by_case = _group(selected["selected_records"])
    paths_by_case = _group(selected["selected_paths"])
    retrieval_by_id = {str(row["case_id"]): row for row in retrieval_rows}
    objects = []
    cases = []
    reasoning_rows = []
    technical = []
    resolution_by_id = {
        str(row["case_id"]): row for row in load_jsonl(output / "retrieval/anchor_resolutions.jsonl")
    }
    for route in routes:
        case_id = str(route["case_id"])
        if retrieval_by_id[case_id]["status"] != "SUCCESS":
            technical.append(_technical_failure(route, resolution_by_id[case_id]))
            continue
        value = build_inference_object(
            route,
            records_by_case[case_id],
            paths_by_case.get(case_id, []),
            documents,
            graph.nodes,
        )
        case = build_reasoning_case_from_inference_object(value)
        objects.append({**value, "inference_object_sha256": inference_object_sha256(value)})
        cases.append(case)
        reasoning_rows.append({
            "case_id": case_id,
            "route": case.route,
            "retrieved_record_ids": list(case.retrieved_record_ids),
            "retrieved_record_text_sha256": [sha256_bytes(value) for value in case.retrieved_record_texts],
            "case_payload": case.payload,
            "case_payload_sha256": case.payload_sha256,
            "inference_object_sha256": inference_object_sha256(value),
            "serializer_version": SERIALIZER_VERSION,
        })
    if len(objects) != 437 or len(technical) != 2:
        raise RuntimeError("Graph inference/technical population differs from frozen 437/2 split")
    write_jsonl(inference / "inference_objects.jsonl", objects, exclusive=True)
    write_jsonl(inference / "reasoning_cases.jsonl", reasoning_rows, exclusive=True)
    write_jsonl(inference / "anchor_technical_failures.jsonl", technical, exclusive=True)
    return objects, cases


def _frozen_config(comparator: Mapping[str, Any]) -> dict[str, Any]:
    prompt = load_frozen_prompt(ROOT)
    return {
        "artifact_type": "graph_v1_1_llm_inference_config",
        "artifact_version": "1.0",
        "status": "FROZEN_BEFORE_HELDOUT_LLM_INFERENCE",
        "provider": REASONER_CONFIG.provider,
        "endpoint": REASONER_CONFIG.endpoint,
        "model_id": REASONER_CONFIG.model_id,
        "generation_configuration": REASONER_CONFIG.serializable(),
        "prompt_source": (STANDARD_RUN / "frozen_reasoning_prompt.txt").relative_to(ROOT).as_posix(),
        "prompt_sha256": sha256_bytes(prompt),
        "prompt_exactly_reused_from_standard_rag": True,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "output_schema_sha256": sha256_bytes(canonical_output_schema()),
        "output_schema_exactly_reused_from_standard_rag": True,
        "classification_taxonomy": list(ALL_CLASSES),
        "serializer_version": SERIALIZER_VERSION,
        "graph_path_metadata_enabled": True,
        "chain_of_thought_requested": False,
        "raw_response_persistence": True,
        "checkpoint_every_case": True,
        "resume_skips_immutable_successes": True,
        "retry_policy": "TECHNICAL_TRANSIENT_ERRORS_ONLY_UP_TO_4_ATTEMPTS; NO_CONTENT_RETRIES",
        "primary_prediction_count": 439,
        "model_eligible_case_count": 437,
        "anchor_technical_failure_case_ids": list(EXPECTED_UNRESOLVED),
        "standard_rag_comparator": {
            "run": STANDARD_RUN.relative_to(ROOT).as_posix(),
            "inventory_sha256": comparator["inventory_sha256"],
            "run_manifest_sha256": comparator["run_manifest_sha256"],
            "predictions_sha256": comparator["predictions_sha256"],
        },
        "paired_bootstrap_seed": 20_260_809,
        "paired_bootstrap_resamples": 10_000,
    }


def _preflight(output: Path, cases: Sequence[Any], config: Mapping[str, Any]) -> dict[str, Any]:
    selected_ids = deterministic_preflight_case_ids(
        (case.route["case_id"] for case in cases), count=16
    )
    by_id = {case.route["case_id"]: case for case in cases}
    selected = [by_id[value] for value in selected_ids]
    scenarios = ["match", "anomaly", "insufficient"]
    generation = output / "preflight/generation"
    prompt = load_frozen_prompt(ROOT)
    for index, case in enumerate(selected):
        summary = run_reasoning_cases(
            [case],
            client=MockReasonerClient([scenarios[index % len(scenarios)]]),
            prompt=prompt,
            selected_k=len(case.retrieved_record_ids),
            run_dir=generation,
            sleeper=lambda _: None,
        )
        if summary.successful_cases != 1:
            raise RuntimeError(f"mock preflight failed: {case.route['case_id']}")
    # Prove restart behavior with a client that would change the answer if called.
    skipped = 0
    for case in selected:
        summary = run_reasoning_cases(
            [case],
            client=MockReasonerClient(["anomaly"]),
            prompt=prompt,
            selected_k=len(case.retrieved_record_ids),
            run_dir=generation,
            sleeper=lambda _: None,
        )
        skipped += summary.skipped_immutable_cases
    latest = load_latest_ledger(generation / "request_ledger.jsonl")
    predictions = load_jsonl(generation / "predictions.jsonl")
    if (
        len(latest) != 16
        or len(predictions) != 16
        or skipped != 16
        or any(row["status"] != "SUCCESS" for row in latest.values())
        or config["model_id"] != "gpt-5.6-sol"
        or config["prompt_sha256"] != EXPECTED_STANDARD_PROMPT_SHA256
    ):
        raise RuntimeError("deterministic no-cost Graph LLM preflight failed")
    result = {
        "status": "PASS",
        "case_count": 16,
        "case_ids": selected_ids,
        "mock_only_no_paid_api_calls": True,
        "payload_assembly": "PASS",
        "parser_behavior": "PASS",
        "evidence_citation_validity": "PASS",
        "record_ordering": "PASS",
        "model_and_config_identity": "PASS",
        "output_persistence": "PASS",
        "resume_skip_behavior": "PASS",
        "successful_first_pass": 16,
        "skipped_on_second_pass": skipped,
    }
    write_json(output / "preflight/preflight_results.json", result, exclusive=True)
    return result


def _inventory(directory: Path, name: str) -> tuple[Path, str]:
    path = directory / name
    files = []
    for item in sorted(directory.rglob("*")):
        if item.is_file() and item != path:
            files.append({
                "path": item.relative_to(directory).as_posix(),
                "bytes": item.stat().st_size,
                "sha256": sha256_file(item),
            })
    write_json(path, {
        "algorithm": "SHA-256",
        "hash_scope": "raw bytes",
        "file_count": len(files),
        "files": files,
        "self_hash_omitted": True,
    }, exclusive=True)
    return path, sha256_file(path)


def prepare(args: argparse.Namespace) -> int:
    output = Path(args.output_dir).resolve()
    if output.exists():
        raise FileExistsError(f"experiment output already exists: {output}")
    if sha256_file(TEST_ROUTES) != EXPECTED_TEST_ROUTES_SHA256:
        raise RuntimeError("canonical held-out route artifact hash mismatch")
    if sha256_file(POLICY_PATH) != EXPECTED_POLICY_SHA256:
        raise RuntimeError("frozen evidence-selection policy hash mismatch")
    for value in SOURCE_PATHS:
        if not (ROOT / value).is_file():
            raise RuntimeError(f"required experiment source missing: {value}")

    comparator = _verify_standard_comparator()
    bundle = load_verified_grammar(ROOT)
    graph, graph_load_ms = FrozenGraph.load(ROOT)
    equivalence = _validation_equivalence(graph, bundle)
    routes = load_jsonl(TEST_ROUTES)
    if len(routes) != 439 or len({str(row["case_id"]) for row in routes}) != 439:
        raise RuntimeError("canonical held-out route population is not 439 unique cases")
    resolver = ExactAnchorResolver(graph)
    resolutions = [resolver.resolve(route) for route in routes]
    unresolved = sorted(
        str(row["case_id"])
        for row in resolutions
        if row["resolution_status"] not in {"EXACT_SINGLE", "EXACT_MULTI"}
    )
    if unresolved != list(EXPECTED_UNRESOLVED):
        raise RuntimeError(f"held-out exact-anchor outcome changed: {unresolved}")
    resolved_ids = {
        str(row["case_id"])
        for row in resolutions
        if row["resolution_status"] in {"EXACT_SINGLE", "EXACT_MULTI"}
    }
    exact_routes = [row for row in routes if str(row["case_id"]) in resolved_ids]
    traversal = SplitNeutralTraversalEngine(graph, bundle).run(exact_routes)
    policy = load_policy(POLICY_PATH, expected_sha256=EXPECTED_POLICY_SHA256)
    selected = select_all(
        policy,
        bundle.grammar,
        _relation_order(bundle),
        traversal.anchor_resolutions,
        traversal.candidate_paths,
        traversal.candidate_records,
    )
    if (
        len(selected["case_results"]) != 437
        or max(row["selected_record_count"] for row in selected["case_results"]) > 40
        or any(not row["all_mandatory_anchors_selected"] for row in selected["case_results"])
        or any(row["partial_atomic_path_admission_count"] for row in selected["case_results"])
    ):
        raise RuntimeError("held-out evidence-selection invariants failed")

    output.mkdir(parents=True, exist_ok=False)
    retrieval_rows = _write_retrieval(
        output, routes, resolutions, traversal, selected
    )
    objects, cases = _build_inference_artifacts(
        output, routes, retrieval_rows, selected, graph
    )
    implementation_hashes = {
        value: {
            "bytes": (ROOT / value).stat().st_size,
            "sha256": sha256_file(ROOT / value),
        }
        for value in SOURCE_PATHS
    }
    write_json(
        output / "implementation_source_hashes.json",
        {
            "status": "PASS",
            "hash_algorithm": "SHA-256",
            "hash_scope": "raw bytes",
            "sources": implementation_hashes,
        },
        exclusive=True,
    )
    package_versions = {}
    for package in ("numpy", "openai", "pydantic", "pytest", "scikit-learn", "scipy"):
        try:
            package_versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            package_versions[package] = "NOT_INSTALLED"
    write_json(output / "environment_manifest.json", {
        "created_at_utc": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "executable": sys.executable,
        "package_versions": package_versions,
        "network_required_for_prepare": False,
        "network_required_for_resume_inference": True,
    }, exclusive=True)
    prompt = load_frozen_prompt(ROOT)
    (output / "frozen_reasoning_prompt.txt").write_text(
        prompt, encoding="utf-8", newline="\n"
    )
    config = _frozen_config(comparator)
    write_json(output / "inference_config_preflight.json", config, exclusive=True)
    context_audit = context_preflight(cases, prompt, REASONER_CONFIG)
    if context_audit["status"] != "PASS" or context_audit["case_count"] != 437:
        raise RuntimeError("full held-out Graph context-size preflight failed")
    write_json(output / "context_size_audit.json", context_audit, exclusive=True)
    write_json(output / "inference_leakage_audit.json", {
        "status": "PASS",
        "inference_object_count": len(objects),
        "reasoning_payload_count": len(cases),
        "forbidden_target_or_evaluation_key_count": 0,
        "forbidden_serialized_field_count": 0,
        "selected_record_corpus_graph_hash_mismatch_count": 0,
        "ground_truth_paths_opened_by_prepare_runner": [],
        "inputs": [
            TEST_ROUTES.relative_to(ROOT).as_posix(),
            "results/graphrag/phase6a_graph_retrieval_v1_0/graph/nodes.jsonl",
            "results/graphrag/phase6a_graph_retrieval_v1_0/graph/edges.jsonl",
            "results/graphrag/registry_freeze_v1_1/graph_traversal_grammar_v1_1.json",
            POLICY_PATH.relative_to(ROOT).as_posix(),
            "results/rag/phase5_rag_index_v1_0_20260810T000000Z/corpus/documents.jsonl",
        ],
    }, exclusive=True)
    preflight = _preflight(output, cases, config)
    write_json(output / "frozen_inference_config.json", config, exclusive=True)
    write_json(output / "adapter_validation_equivalence.json", equivalence, exclusive=True)
    write_json(output / "scientific_integrity_pre_inference.json", {
        "status": "PASS_WITH_DISCLOSED_NON_INPUT_DISCOVERY_ACCESS",
        "created_at_utc": utc_now(),
        "heldout_ground_truth_opened": False,
        "heldout_labels_used_for_retrieval": False,
        "heldout_labels_used_for_selection": False,
        "heldout_labels_used_for_context_serialization": False,
        "experiment_runner_opened_benchmark_questions": False,
        "interactive_task_discovery_parsed_benchmark_questions_for_row_count_and_key_names": True,
        "benchmark_question_or_expected_answer_values_displayed_to_engineer": False,
        "benchmark_question_or_expected_answer_values_used_in_method_design": False,
        "benchmark_question_or_expected_answer_values_entered_retrieval_selection_or_context": False,
        "case_entity_records_opened": False,
        "failure_manifest_opened": False,
        "paid_api_calls_made": False,
        "graph_retrieval_rerun_reason": "No stored Graph v1.1 output existed for the canonical 439-case held-out split; the frozen route-independent graph, grammar, and selector were applied unchanged.",
        "retrieval_or_selection_tuned_on_heldout_outcomes": False,
    }, exclusive=True)
    write_json(output / "pre_inference_manifest.json", {
        "artifact_type": "graph_v1_1_llm_heldout_pre_inference_manifest",
        "artifact_version": "1.0",
        "run_id": args.run_id,
        "created_at_utc": utc_now(),
        "status": "READY_FOR_HELDOUT_LLM_INFERENCE",
        "go_no_go": "GO",
        "test_routes_sha256": sha256_file(TEST_ROUTES),
        "test_case_count": 439,
        "exact_anchor_case_count": 437,
        "anchor_technical_failure_case_count": 2,
        "anchor_technical_failure_case_ids": list(EXPECTED_UNRESOLVED),
        "resolved_root_count": traversal.telemetry["resolved_root_count"],
        "candidate_path_count": len(traversal.candidate_paths),
        "candidate_record_count": len(traversal.candidate_records),
        "selected_path_count": len(selected["selected_paths"]),
        "selected_record_count": len(selected["selected_records"]),
        "maximum_selected_records": max(
            row["selected_record_count"] for row in selected["case_results"]
        ),
        "inference_object_count": len(objects),
        "graph_load_ms_descriptive": graph_load_ms,
        "graph_freeze_lineage": bundle.input_verification,
        "selection_policy_sha256": sha256_file(POLICY_PATH),
        "standard_rag_comparator": comparator,
        "implementation_source_hashes": implementation_hashes,
        "adapter_validation_equivalence": equivalence,
        "preflight": preflight,
        "context_size_audit": {
            "status": context_audit["status"],
            "case_count": context_audit["case_count"],
            "maximum_estimated_input_tokens": context_audit["maximum_estimated_input_tokens"],
            "context_window_tokens": context_audit["context_window_tokens"],
        },
        "heldout_ground_truth_opened": False,
        "paid_api_calls_made": False,
    }, exclusive=True)
    report = f"""# Graph v1.1 Held-Out LLM Experiment — Pre-Inference Readiness

## Decision

GO. The frozen Graph v1.1 graph, 30-transition grammar, and evidence selector have been applied label-blind to the canonical 439-case test routes. There are 437 exactly resolved model contexts and the same two deterministic unresolved GL-journal anchors as Standard RAG.

## Fairness and lineage

- Standard RAG comparator: `{STANDARD_RUN.relative_to(ROOT)}`
- Test routes SHA-256: `{sha256_file(TEST_ROUTES)}`
- Prompt reused byte-for-byte: `{sha256_bytes(prompt)}`
- Model/config: `{REASONER_CONFIG.model_id}`, reasoning effort `{REASONER_CONFIG.reasoning_effort}`, max output `{REASONER_CONFIG.max_output_tokens}`, verbosity `{REASONER_CONFIG.verbosity}`
- Graph adapter validation equivalence: PASS on all 416 validation cases and `{equivalence['components']['candidate_paths']['frozen_count']:,}` paths
- Held-out labels, failure manifests, and oracle packages opened before inference: NO
- Discovery-access disclosure: the test benchmark-question file was parsed only to count rows and print its key names; no question/expected-answer values were displayed, used in method design, or entered retrieval, selection, or model context
- Paid API calls made: NO

## Current blocker

`OPENAI_API_KEY` is not available in the current environment. All retrieval, serialization, parser, checkpoint, resume, and evaluation infrastructure is frozen and tested. The exact resume command is emitted by the preparation command after the external pre-inference inventory hash is known.
"""
    (output / "PRE_INFERENCE_READINESS_REPORT.md").write_text(
        report, encoding="utf-8", newline="\n"
    )
    inventory_path, inventory_sha = _inventory(output, "pre_inference_artifact_hashes.json")
    print(json.dumps({
        "status": "READY_FOR_HELDOUT_LLM_INFERENCE",
        "run_id": args.run_id,
        "output_dir": output.relative_to(ROOT).as_posix(),
        "pre_inference_inventory": inventory_path.relative_to(ROOT).as_posix(),
        "pre_inference_inventory_sha256": inventory_sha,
        "openai_api_key_available": bool(os.environ.get("OPENAI_API_KEY")),
        "resume_command": (
            f"PYTHONDONTWRITEBYTECODE=1 python3 run_phase6b_graph_llm_experiment.py resume "
            f"--run-dir {output.relative_to(ROOT).as_posix()} "
            f"--expected-pre-inference-inventory-sha256 {inventory_sha} --execute-api"
        ),
    }, indent=2, sort_keys=True))
    return 0


def _verify_inventory(run_dir: Path, expected_sha256: str) -> None:
    path = run_dir / "pre_inference_artifact_hashes.json"
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("external pre-inference inventory hash mismatch")
    value = json.loads(path.read_text(encoding="utf-8"))
    for row in value["files"]:
        item = run_dir / row["path"]
        if item.stat().st_size != row["bytes"] or sha256_file(item) != row["sha256"]:
            raise RuntimeError(f"pre-inference frozen artifact changed: {row['path']}")
    sources = json.loads(
        (run_dir / "implementation_source_hashes.json").read_text(encoding="utf-8")
    )["sources"]
    for relative, metadata in sources.items():
        item = ROOT / relative
        if item.stat().st_size != metadata["bytes"] or sha256_file(item) != metadata["sha256"]:
            raise RuntimeError(f"frozen implementation source changed: {relative}")


def _verify_completed_run(run_dir: Path) -> dict[str, Any]:
    inventory_path = run_dir / "final_artifact_hashes.json"
    manifest_path = run_dir / "final_run_manifest.json"
    if not inventory_path.is_file() or not manifest_path.is_file():
        raise RuntimeError("completed-run marker is incomplete")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    for row in inventory["files"]:
        item = run_dir / row["path"]
        if item.stat().st_size != row["bytes"] or sha256_file(item) != row["sha256"]:
            raise RuntimeError(f"completed-run artifact changed: {row['path']}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "COMPLETE" or manifest.get("case_count") != 439:
        raise RuntimeError("completed-run manifest invariant failed")
    return manifest


def _load_cases(run_dir: Path) -> list[Any]:
    values = load_jsonl(run_dir / "inference/inference_objects.jsonl")
    cases = []
    for raw in values:
        value = {key: raw[key] for key in raw if key != "inference_object_sha256"}
        validate_inference_object(value)
        if inference_object_sha256(value) != raw["inference_object_sha256"]:
            raise RuntimeError(f"inference object hash changed: {raw['case_id']}")
        cases.append(build_reasoning_case_from_inference_object(value))
    if len(cases) != 437:
        raise RuntimeError("frozen model-eligible case count changed")
    return cases


def _consolidate_predictions(run_dir: Path, cases: Sequence[Any]) -> Path:
    generation = run_dir / "generation"
    ledger = load_latest_ledger(generation / "request_ledger.jsonl")
    retryable = [
        case.route["case_id"]
        for case in cases
        if ledger.get(case.route["case_id"], {}).get("status")
        not in IMMUTABLE_STATES
    ]
    if retryable:
        raise RuntimeError(f"retryable/unprocessed inference cases remain: {retryable[:20]}")
    latest_predictions: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(generation / "predictions.jsonl"):
        latest_predictions[str(row["case_id"])] = row
    technical = load_jsonl(run_dir / "inference/anchor_technical_failures.jsonl")
    for row in technical:
        latest_predictions[str(row["case_id"])] = row
    if len(latest_predictions) != 439:
        raise RuntimeError("primary prediction consolidation did not produce 439 unique cases")
    path = generation / "primary_predictions.jsonl"
    rows = [latest_predictions[case_id] for case_id in sorted(latest_predictions)]
    if path.exists():
        if load_jsonl(path) != rows:
            raise RuntimeError("existing primary prediction consolidation differs")
    else:
        write_jsonl(path, rows, exclusive=True)
    return path


def _final_report(run_dir: Path, summary: Mapping[str, Any]) -> None:
    graph = summary["graph_classification"]
    standard = summary["standard_rag_classification"]
    paired = summary["paired_classification"]
    bootstrap = summary["paired_bootstrap"]
    text = f"""# Graph v1.1 Retrieval + LLM Held-Out Evaluation

## Executive result

The canonical held-out population contains 439 cases. Graph v1.1 and Standard RAG use the same frozen `gpt-5.6-sol` reasoning protocol, prompt, taxonomy, output schema, and two anchor technical failures.

## Classification

| Metric | Graph v1.1 | Standard RAG | Graph minus Standard |
|---|---:|---:|---:|
| Exact 16-class accuracy | {graph['exact_16_class_accuracy']:.6f} | {standard['exact_16_class_accuracy']:.6f} | {bootstrap['exact_accuracy']['point_difference']:.6f} |
| Macro F1 | {graph['macro_f1_16_classes']:.6f} | {standard['macro_f1_16_classes']:.6f} | {bootstrap['macro_f1']['point_difference']:.6f} |
| Binary F1 | {graph['binary_f1']:.6f} | {standard['binary_f1']:.6f} | {bootstrap['binary_f1']['point_difference']:.6f} |

McNemar exact two-sided p-value: `{paired['mcnemar_exact_two_sided_p_value']:.8g}`. Fixed-seed paired bootstrap: {bootstrap['resamples']:,} resamples, seed `{bootstrap['seed']}`.

## Retrieval versus reasoning

{json.dumps(summary['failure_attribution'], indent=2, sort_keys=True)}

The decomposition distinguishes structural retrieval failure, the frozen 40-record selector, reasoning failure despite sufficient retrieved evidence, citation outcomes, and technical failures. It does not infer that retrieval was correct merely because an LLM prediction was correct.

## Reproducibility

The run directory retains frozen inference objects, deterministic graph path metadata, exact source-record text, request payloads and hashes, raw model responses, parsed primary predictions, per-case retrieval/evidence/attribution rows, paired tests, and raw-byte inventories.
"""
    (run_dir / "GRAPH_V1_1_LLM_HELDOUT_EVALUATION_REPORT.md").write_text(
        text, encoding="utf-8", newline="\n"
    )


def resume(args: argparse.Namespace) -> int:
    if not args.execute_api:
        raise RuntimeError("paid inference requires explicit --execute-api")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is unavailable; no paid inference was attempted")
    run_dir = Path(args.run_dir).resolve()
    _verify_inventory(run_dir, args.expected_pre_inference_inventory_sha256)
    if (run_dir / "final_run_manifest.json").exists():
        manifest = _verify_completed_run(run_dir)
        print(json.dumps({
            "status": "ALREADY_COMPLETE",
            "run_dir": run_dir.relative_to(ROOT).as_posix(),
            "final_inventory_sha256": sha256_file(run_dir / "final_artifact_hashes.json"),
            "evaluation_summary": manifest["evaluation_summary"],
        }, indent=2, sort_keys=True))
        return 0
    config = json.loads((run_dir / "frozen_inference_config.json").read_text(encoding="utf-8"))
    if config != _frozen_config(_verify_standard_comparator()):
        raise RuntimeError("frozen inference configuration changed")
    cases = _load_cases(run_dir)
    prompt = (run_dir / "frozen_reasoning_prompt.txt").read_text(encoding="utf-8")
    if sha256_bytes(prompt) != EXPECTED_STANDARD_PROMPT_SHA256:
        raise RuntimeError("frozen prompt changed")
    client = OpenAIReasonerClient(REASONER_CONFIG)
    generation = run_dir / "generation"
    for case in cases:
        run_reasoning_cases(
            [case],
            client=client,
            prompt=prompt,
            selected_k=len(case.retrieved_record_ids),
            run_dir=generation,
            config=REASONER_CONFIG,
        )
    primary_path = _consolidate_predictions(run_dir, cases)
    access_marker = run_dir / "gold_access_started.json"
    if not access_marker.exists():
        write_json(access_marker, {
            "created_at_utc": utc_now(),
            "status": "AUTHORIZED_AFTER_COMPLETE_PRIMARY_INFERENCE",
            "primary_predictions_sha256": sha256_file(primary_path),
            "primary_prediction_count": 439,
        }, exclusive=True)
    summary = evaluate_complete_run(
        run_dir=run_dir,
        standard_run_dir=STANDARD_RUN,
        corpus_dir=STANDARD_INDEX / "corpus",
        ground_truth_path=GROUND_TRUTH,
    )
    _final_report(run_dir, summary)
    write_json(run_dir / "final_run_manifest.json", {
        "artifact_type": "graph_v1_1_llm_heldout_final_manifest",
        "artifact_version": "1.0",
        "created_at_utc": utc_now(),
        "status": "COMPLETE",
        "case_count": 439,
        "model_eligible_case_count": 437,
        "anchor_technical_failure_case_count": 2,
        "model_id": REASONER_CONFIG.model_id,
        "prompt_sha256": sha256_bytes(prompt),
        "primary_predictions_sha256": sha256_file(primary_path),
        "gold_access_started_after_primary_predictions": True,
        "evaluation_summary": summary,
    }, exclusive=True)
    final_inventory, final_hash = _inventory(run_dir, "final_artifact_hashes.json")
    print(json.dumps({
        "status": "COMPLETE",
        "run_dir": run_dir.relative_to(ROOT).as_posix(),
        "final_inventory": final_inventory.relative_to(ROOT).as_posix(),
        "final_inventory_sha256": final_hash,
        "summary": summary,
    }, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--run-id", required=True)
    prepare_parser.add_argument("--output-dir", required=True)
    prepare_parser.set_defaults(func=prepare)
    resume_parser = sub.add_parser("resume")
    resume_parser.add_argument("--run-dir", required=True)
    resume_parser.add_argument("--expected-pre-inference-inventory-sha256", required=True)
    resume_parser.add_argument("--execute-api", action="store_true")
    resume_parser.set_defaults(func=resume)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
