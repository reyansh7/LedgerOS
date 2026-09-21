#!/usr/bin/env python3
"""Deterministic, label-blind GraphRAG pre-freeze audit over the frozen Phase 5 corpus.

This script intentionally does not open underlying benchmark source tables, labels,
oracle/evidence files, earlier predictions, or any GraphRAG implementation artifact.
It reads only the frozen Phase 5 index/corpus, the operational schema registry, and
the frozen RAG leakage registry/specification.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from itertools import zip_longest
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.rag.config import (  # noqa: E402
    AVAILABILITY_FIELDS,
    DECISION_CUTOFF,
    EXPECTED_DOCUMENT_COUNT,
    EXPECTED_TEXT_MANIFEST_SHA256,
    FORBIDDEN_ARTIFACT_NAMES,
    FORBIDDEN_KEYS,
    RECORD_TYPES,
    SPEC_RELATIVE_PATH,
    SPEC_SHA256,
)
from src.schema import PRIMARY_KEYS, TABLE_SCHEMAS  # noqa: E402


OUT_DIR = Path(__file__).resolve().parent
PHASE5_DIR = ROOT / "results/rag/phase5_rag_index_v1_0_20260810T000000Z"
CORPUS_DIR = PHASE5_DIR / "corpus"
MANIFEST_PATH = PHASE5_DIR / "index_manifest.json"
DOCUMENTS_PATH = CORPUS_DIR / "documents.jsonl"
METADATA_PATH = CORPUS_DIR / "metadata.jsonl"
RECORD_IDS_PATH = CORPUS_DIR / "record_ids.txt"
EMBEDDINGS_PATH = PHASE5_DIR / "embeddings.npy"
LEDGER_PATH = PHASE5_DIR / "embedding_ledger.jsonl"
CUTOFF = datetime.fromisoformat(DECISION_CUTOFF)

EXPECTED_MANIFEST_SHA256 = "527b5980f1544dda5eab4581f8cb9c498e2a8e7633e4c061dd232b8cff05e3a6"
EXPECTED_VECTOR_COUNT = 155_391
EXPECTED_DIMENSIONS = 1_536
EXPECTED_CORPUS_HASHES = {
    "documents.jsonl": "43fe8841d3cbfc64c403349c2336c631c9f6ca9dc35f3e86af1c4ae993441b8c",
    "metadata.jsonl": "e30183ea1e17af182ad24a3177e776a869ed55718872ba6cc1a169506b4f96fb",
    "record_ids.txt": "1850249832dbb9c75ddddfa8e82615dd1db138cdd83cb2dc455029035e1b0058",
}
EXPECTED_EMBEDDINGS_SHA256 = "128e3cd5c4215e9e1f6cdc664b838c1c3aef72b8eb0bc1191d19bf7bf763043a"
EXPECTED_LEDGER_SHA256 = "83d9d5bc16029d61c16716ff6e4562c3b157411eaeb4dbb2736e35019bfca237"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def nonempty(value: Any) -> bool:
    return value is not None and (not isinstance(value, str) or value != "")


def parse_datetime(value: Any) -> datetime | None:
    if not nonempty(value):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def parse_record_text(text: str) -> tuple[dict[str, Any], list[str]]:
    fields: dict[str, Any] = {}
    headers: list[str] = []
    lines = text.splitlines()
    for line in lines[2:]:
        key, separator, serialized = line.partition(":")
        if not separator:
            continue
        normalized = key.strip().lower()
        headers.append(normalized)
        try:
            fields[normalized] = json.loads(serialized.strip())
        except json.JSONDecodeError:
            fields[normalized] = serialized.strip()
    return fields, headers


def nearest_rank_percentile(values: list[int] | list[float], percentile: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def degree_stats(values: Iterable[int]) -> dict[str, Any]:
    materialized = list(values)
    if not materialized:
        return {
            "domain_size": 0,
            "maximum_degree": 0,
            "mean_degree": 0.0,
            "median_degree": 0.0,
            "p95_degree_nearest_rank": 0,
            "zero_degree_count": 0,
        }
    return {
        "domain_size": len(materialized),
        "maximum_degree": max(materialized),
        "mean_degree": round(mean(materialized), 6),
        "median_degree": round(float(median(materialized)), 6),
        "p95_degree_nearest_rank": nearest_rank_percentile(materialized, 0.95),
        "zero_degree_count": sum(value == 0 for value in materialized),
    }


def identifier_prefix(value: Any) -> str:
    if not nonempty(value):
        return "<EMPTY>"
    match = re.match(r"^([A-Za-z]+[_-])", str(value))
    if match:
        return match.group(1)
    match = re.match(r"^([A-Za-z]+)", str(value))
    return match.group(1) if match else "<OTHER>"


def canonical_value(record: dict[str, Any]) -> str | None:
    components = []
    for field in PRIMARY_KEYS[record["source_table"]]:
        value = record["fields"].get(field)
        if not nonempty(value):
            return None
        components.append(str(value))
    return "|".join(components)


def describe_cardinality(source_degrees: list[int], target_degrees: list[int]) -> str:
    source_max = max(source_degrees, default=0)
    target_max = max(target_degrees, default=0)
    if source_max <= 1 and target_max <= 1:
        return "1:1"
    if source_max <= 1 and target_max > 1:
        return "N:1 (many source nodes to one target node)"
    if source_max > 1 and target_max <= 1:
        return "1:N (one source node to many target nodes)"
    return "M:N"


def pct(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 6) if denominator else 0.0


def md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(md_escape(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def scan_key_paths(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() in FORBIDDEN_KEYS:
                hits.append(child_path)
            hits.extend(scan_key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(scan_key_paths(child, f"{path}[{index}]") )
    return hits


SEMANTIC_LEAKAGE_PATTERNS = {
    "failure_target": re.compile(r"(?i)\b(?:NO_FAILURE|F(?:0[1-9]|1[0-5])(?:_[A-Z][A-Z0-9_]*)?)\b"),
    "anomaly_label": re.compile(r"(?i)\b(?:anomaly|anomalous)\b"),
    "expected_rca_or_answer": re.compile(r"(?i)\b(?:expected\s+(?:rca|answer|resolution)|rca\s+ground\s*truth)\b"),
    "root_cause": re.compile(r"(?i)\broot[ _-]?cause\b"),
    "oracle_or_evidence_contract": re.compile(r"(?i)\b(?:oracle\s+evidence|evidence\s+contract|oracle\s+mapping)\b"),
    "difficulty_hop_or_tier_label": re.compile(r"(?i)\b(?:reasoning\s+hops?|hop\s+labels?|difficulty\s+labels?|benchmark\s+tier)\b"),
    "causal_or_mutation_label": re.compile(r"(?i)\b(?:causal\s+labels?|mutation\s+logs?)\b"),
    "case_entity_oracle_mapping": re.compile(r"(?i)\bcase\s+entity\s+oracle\s+mappings?\b"),
    "prior_model_or_baseline_output": re.compile(r"(?i)\b(?:prior|previous|baseline)\s+(?:model\s+)?(?:predictions?|outputs?)\b"),
    "supervised_benchmark_feature": re.compile(r"(?i)\bsupervised\s+benchmark\s+features?\b"),
}


def load_and_verify() -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    manifest_sha = sha256_file(MANIFEST_PATH)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    corpus_hashes = {
        "documents.jsonl": sha256_file(DOCUMENTS_PATH),
        "metadata.jsonl": sha256_file(METADATA_PATH),
        "record_ids.txt": sha256_file(RECORD_IDS_PATH),
    }
    embeddings_sha = sha256_file(EMBEDDINGS_PATH)
    ledger_sha = sha256_file(LEDGER_PATH)
    matrix = np.load(EMBEDDINGS_PATH, mmap_mode="r", allow_pickle=False)

    verification = {
        "authoritative_directory": str(PHASE5_DIR.relative_to(ROOT)),
        "index_manifest_sha256": {"expected": EXPECTED_MANIFEST_SHA256, "actual": manifest_sha},
        "corpus_file_sha256": {
            name: {"expected": EXPECTED_CORPUS_HASHES[name], "actual": actual}
            for name, actual in corpus_hashes.items()
        },
        "embedding_matrix_sha256": {"expected": EXPECTED_EMBEDDINGS_SHA256, "actual": embeddings_sha},
        "embedding_ledger_sha256": {"expected": EXPECTED_LEDGER_SHA256, "actual": ledger_sha},
        "vector_count": {"expected": EXPECTED_VECTOR_COUNT, "manifest": manifest.get("vector_count"), "matrix": matrix.shape[0]},
        "dimensions": {"expected": EXPECTED_DIMENSIONS, "manifest": manifest.get("dimensions"), "matrix": matrix.shape[1]},
        "matrix_dtype": str(matrix.dtype),
        "matrix_c_contiguous": bool(matrix.flags.c_contiguous),
    }

    gate_errors: list[str] = []
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        gate_errors.append("index manifest SHA-256 mismatch")
    for name, actual in corpus_hashes.items():
        if actual != EXPECTED_CORPUS_HASHES[name] or manifest["corpus"].get(name.replace(".jsonl", "_sha256").replace(".txt", "_sha256")) not in {None, actual}:
            gate_errors.append(f"{name} SHA-256 mismatch")
    if embeddings_sha != EXPECTED_EMBEDDINGS_SHA256 or embeddings_sha != manifest.get("embedding_matrix_sha256"):
        gate_errors.append("embedding matrix SHA-256 mismatch")
    if ledger_sha != EXPECTED_LEDGER_SHA256 or ledger_sha != manifest.get("embedding_ledger_sha256"):
        gate_errors.append("embedding ledger SHA-256 mismatch")
    if tuple(matrix.shape) != (EXPECTED_VECTOR_COUNT, EXPECTED_DIMENSIONS):
        gate_errors.append("embedding matrix shape mismatch")
    if manifest.get("vector_count") != EXPECTED_VECTOR_COUNT or manifest.get("dimensions") != EXPECTED_DIMENSIONS:
        gate_errors.append("manifest count/dimensions mismatch")
    if manifest["corpus"].get("text_manifest_sha256") != EXPECTED_TEXT_MANIFEST_SHA256:
        gate_errors.append("manifest logical text-manifest hash mismatch")

    records_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    logical_digest = hashlib.sha256()
    alignment_mismatches: list[dict[str, Any]] = []
    document_hash_mismatches: list[str] = []
    schema_mismatches: list[dict[str, Any]] = []
    ordinal_mismatches: list[dict[str, Any]] = []
    metadata_document_mismatches: list[str] = []
    metadata_relational_mismatches: list[dict[str, Any]] = []
    leakage_key_hits: list[dict[str, Any]] = []
    leakage_content_hits: list[dict[str, Any]] = []
    header_counts: Counter[str] = Counter()
    json_line_count = 0

    with (
        DOCUMENTS_PATH.open(encoding="utf-8") as documents,
        METADATA_PATH.open(encoding="utf-8") as metadata,
        RECORD_IDS_PATH.open(encoding="utf-8") as record_ids,
    ):
        for ordinal, triple in enumerate(zip_longest(documents, metadata, record_ids)):
            document_line, metadata_line, record_id_line = triple
            if None in triple:
                gate_errors.append("canonical corpus files have unequal line counts")
                break
            assert document_line is not None and metadata_line is not None and record_id_line is not None
            document = json.loads(document_line)
            meta = json.loads(metadata_line)
            listed_record_id = record_id_line.rstrip("\n")
            json_line_count += 2

            if document.get("record_id") != meta.get("record_id") or document.get("record_id") != listed_record_id:
                if len(alignment_mismatches) < 20:
                    alignment_mismatches.append({
                        "ordinal": ordinal,
                        "document_record_id": document.get("record_id"),
                        "metadata_record_id": meta.get("record_id"),
                        "record_ids_value": listed_record_id,
                    })
            if document.get("document_ordinal") != ordinal or meta.get("document_ordinal") != ordinal:
                if len(ordinal_mismatches) < 20:
                    ordinal_mismatches.append({"ordinal": ordinal, "record_id": document.get("record_id")})

            document_without_text = {key: value for key, value in document.items() if key != "text"}
            if document_without_text != meta and len(metadata_document_mismatches) < 20:
                metadata_document_mismatches.append(document.get("record_id", f"ordinal:{ordinal}"))

            text = document.get("text", "")
            actual_document_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if actual_document_sha != document.get("document_sha256"):
                if len(document_hash_mismatches) < 20:
                    document_hash_mismatches.append(document.get("record_id", f"ordinal:{ordinal}"))
            logical_digest.update(f"{document['record_id']}\t{actual_document_sha}\n".encode("utf-8"))

            fields, headers = parse_record_text(text)
            header_counts.update(headers)
            table = document.get("source_table")
            record_type = document.get("record_type")
            expected_fields = TABLE_SCHEMAS.get(table)
            if expected_fields != headers:
                if len(schema_mismatches) < 20:
                    schema_mismatches.append({
                        "record_id": document.get("record_id"),
                        "expected": expected_fields,
                        "actual": headers,
                    })
            if RECORD_TYPES.get(table) != record_type:
                gate_errors.append(f"source table/type mismatch at {document.get('record_id')}")

            for key, value in document.get("primary_key", {}).items():
                if fields.get(key) != value and len(metadata_relational_mismatches) < 20:
                    metadata_relational_mismatches.append({"record_id": document["record_id"], "field": key, "kind": "primary_key"})
            for key, value in document.get("relational_ids", {}).items():
                if fields.get(key) != value and len(metadata_relational_mismatches) < 20:
                    metadata_relational_mismatches.append({"record_id": document["record_id"], "field": key, "kind": "relational_id"})

            record = {
                "record_id": document["record_id"],
                "record_type": record_type,
                "source_table": table,
                "primary_key": document["primary_key"],
                "relational_ids": document["relational_ids"],
                "available_at": document["available_at"],
                "source_file": document["source_file"],
                "source_system": document["source_system"],
                "fields": fields,
            }
            records_by_type[record_type].append(record)

            for filename, parsed, raw_line in (
                ("documents.jsonl", document, document_line),
                ("metadata.jsonl", meta, metadata_line),
            ):
                for path in scan_key_paths(parsed):
                    if len(leakage_key_hits) < 100:
                        leakage_key_hits.append({"file": filename, "ordinal": ordinal, "path": path})
                for category, pattern in SEMANTIC_LEAKAGE_PATTERNS.items():
                    match = pattern.search(raw_line)
                    if match and len(leakage_content_hits) < 100:
                        leakage_content_hits.append({
                            "file": filename,
                            "ordinal": ordinal,
                            "category": category,
                            "matched_marker": match.group(0),
                        })
                source_file = parsed.get("source_file", "")
                if Path(source_file).name in FORBIDDEN_ARTIFACT_NAMES and len(leakage_content_hits) < 100:
                    leakage_content_hits.append({
                        "file": filename,
                        "ordinal": ordinal,
                        "category": "forbidden_source_artifact",
                        "matched_marker": source_file,
                    })
            for header in headers:
                normalized_header = re.sub(r"[^a-z0-9]+", "_", header.lower()).strip("_")
                if normalized_header in FORBIDDEN_KEYS and len(leakage_key_hits) < 100:
                    leakage_key_hits.append({
                        "file": "documents.jsonl",
                        "ordinal": ordinal,
                        "path": f"$.text.{normalized_header}",
                    })

    logical_sha = logical_digest.hexdigest()
    corpus_count = sum(len(rows) for rows in records_by_type.values())
    verification.update({
        "corpus_line_counts": {
            "documents.jsonl": corpus_count,
            "metadata.jsonl": corpus_count,
            "record_ids.txt": corpus_count,
        },
        "corpus_count": {"expected": EXPECTED_DOCUMENT_COUNT, "actual": corpus_count},
        "logical_text_manifest_sha256": {"expected": EXPECTED_TEXT_MANIFEST_SHA256, "actual": logical_sha},
        "per_document_text_sha256_mismatch_count": len(document_hash_mismatches),
        "alignment_mismatch_count": len(alignment_mismatches),
        "ordinal_mismatch_count": len(ordinal_mismatches),
        "metadata_document_mismatch_count": len(metadata_document_mismatches),
        "metadata_relational_mismatch_count": len(metadata_relational_mismatches),
        "schema_mismatch_count": len(schema_mismatches),
        "details": {
            "alignment_mismatches": alignment_mismatches,
            "ordinal_mismatches": ordinal_mismatches,
            "document_hash_mismatches": document_hash_mismatches,
            "metadata_document_mismatches": metadata_document_mismatches,
            "metadata_relational_mismatches": metadata_relational_mismatches,
            "schema_mismatches": schema_mismatches,
        },
    })

    if corpus_count != EXPECTED_DOCUMENT_COUNT:
        gate_errors.append("corpus record count mismatch")
    if logical_sha != EXPECTED_TEXT_MANIFEST_SHA256:
        gate_errors.append("logical text-manifest SHA-256 mismatch")
    if any((alignment_mismatches, ordinal_mismatches, document_hash_mismatches, metadata_document_mismatches, metadata_relational_mismatches, schema_mismatches)):
        gate_errors.append("canonical corpus alignment/schema integrity mismatch")

    leakage = {
        "audit_version": "graph_leakage_audit_v1",
        "decision_cutoff": DECISION_CUTOFF,
        "scope": [
            str(DOCUMENTS_PATH.relative_to(ROOT)),
            str(METADATA_PATH.relative_to(ROOT)),
            str(RECORD_IDS_PATH.relative_to(ROOT)),
        ],
        "registry_sources": {
            "frozen_spec": str(SPEC_RELATIVE_PATH),
            "frozen_spec_expected_sha256": SPEC_SHA256,
            "frozen_spec_actual_sha256": sha256_file(ROOT / SPEC_RELATIVE_PATH),
            "runtime_registry": "src/rag/config.py::FORBIDDEN_KEYS/FORBIDDEN_ARTIFACT_NAMES",
        },
        "scan": {
            "json_lines_scanned": json_line_count,
            "documents_scanned": corpus_count,
            "structured_key_path_scan": True,
            "serialized_field_header_scan": True,
            "semantic_marker_scan": sorted(SEMANTIC_LEAKAGE_PATTERNS),
            "source_artifact_name_scan": True,
            "distinct_serialized_field_headers": len(header_counts),
        },
        "prohibited_key_or_header_hit_count": len(leakage_key_hits),
        "prohibited_content_hit_count": len(leakage_content_hits),
        "prohibited_key_or_header_hits": leakage_key_hits,
        "prohibited_content_hits": leakage_content_hits,
        "status": "PASS" if not leakage_key_hits and not leakage_content_hits else "FAIL_BLOCKED",
        "statement": "No held-out ground-truth, oracle, evidence-contract, mutation, causal-edge, prior-prediction, or model-output artifact was opened for this audit.",
    }
    if leakage["registry_sources"]["frozen_spec_actual_sha256"] != SPEC_SHA256:
        gate_errors.append("frozen prohibited-field specification SHA-256 mismatch")
    if leakage["status"] != "PASS":
        gate_errors.append("prohibited benchmark information found in graph source corpus")

    verification["gate_errors"] = sorted(set(gate_errors))
    verification["status"] = "PASS" if not gate_errors else "BLOCKED"
    return verification, records_by_type, leakage


def build_domains(records_by_type: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, dict[str, list[dict[str, Any]]]], dict[str, dict[str, dict[str, list[dict[str, Any]]]]]]:
    canonical_domains: dict[str, dict[str, list[dict[str, Any]]]] = {}
    field_domains: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    for record_type, records in records_by_type.items():
        canonical_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
        fields_map: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for record in records:
            value = canonical_value(record)
            if value is not None:
                canonical_map[value].append(record)
        canonical_domains[record_type] = dict(canonical_map)
        for field in TABLE_SCHEMAS[records[0]["source_table"]]:
            domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for record in records:
                value = record["fields"].get(field)
                if nonempty(value):
                    domain[str(value)].append(record)
            fields_map[field] = dict(domain)
        field_domains[record_type] = fields_map
    return canonical_domains, field_domains


GRAPH_FIELD_POLICY = {
    "VENDOR": {"permitted": ["vendor_id"], "candidate": [], "important": ["vendor_id", "tax_id_hash", "bank_account_token", "bank_routing_token"]},
    "VENDOR_CHANGE": {"permitted": ["change_id", "vendor_id", "changed_by"], "candidate": [], "important": ["change_id", "vendor_id", "changed_by"]},
    "PURCHASE_ORDER": {"permitted": ["po_id", "vendor_id", "created_by"], "candidate": [], "important": ["po_id", "vendor_id", "created_by"]},
    "PO_LINE": {"permitted": ["po_line_id", "po_id"], "candidate": [], "important": ["po_line_id", "po_id", "item_id"]},
    "INVOICE": {"permitted": ["invoice_id", "po_id", "vendor_id"], "candidate": [], "important": ["invoice_id", "po_id", "vendor_id", "invoice_number", "duplicate_reference"]},
    "INVOICE_LINE": {"permitted": ["invoice_line_id", "invoice_id", "po_line_id"], "candidate": [], "important": ["invoice_line_id", "invoice_id", "po_line_id", "item_id"]},
    "APPROVAL_EVENT": {"permitted": ["approval_event_id", "invoice_id"], "candidate": ["approver_id"], "important": ["approval_event_id", "invoice_id", "approver_id"]},
    "PAYMENT": {"permitted": ["payment_id", "vendor_id"], "candidate": ["reference_number"], "important": ["payment_id", "vendor_id", "reference_number", "bank_account_id"]},
    "PAYMENT_ALLOCATION": {"permitted": ["payment_id", "invoice_id"], "candidate": [], "important": ["payment_id", "invoice_id", "allocation_date"]},
    "GL_ENTRY": {"permitted": ["journal_line_id", "transaction_type", "source_transaction_id"], "candidate": [], "important": ["journal_line_id", "journal_id", "transaction_type", "source_transaction_id"]},
    "BANK_TRANSACTION": {"permitted": ["bank_transaction_id"], "candidate": ["payment_reference"], "important": ["bank_transaction_id", "payment_reference", "bank_reference", "bank_account_id", "counterparty_token"]},
    "BANK_STATEMENT": {"permitted": ["bank_statement_id"], "candidate": [], "important": ["bank_statement_id", "bank_account_id"]},
    "EMPLOYEE": {"permitted": ["employee_id"], "candidate": [], "important": ["employee_id"]},
    "AUDIT_EVENT": {"permitted": ["event_id", "entity_type", "entity_id"], "candidate": ["actor_id"], "important": ["event_id", "entity_type", "entity_id", "actor_id"]},
}

ATTRIBUTE_TRAVERSAL_PROHIBITIONS = {
    "bank_account_id", "bank_account_token", "bank_routing_token", "gl_account", "department",
    "cost_center", "currency", "payment_currency", "source_system", "journal_id", "item_id",
}


def build_node_registry(
    records_by_type: dict[str, list[dict[str, Any]]],
    canonical_domains: dict[str, dict[str, list[dict[str, Any]]]],
    field_domains: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    node_entries: list[dict[str, Any]] = []
    global_record_ids: dict[str, int] = Counter()
    for records in records_by_type.values():
        global_record_ids.update(record["record_id"] for record in records)

    all_duplicate_record_ids = sorted(key for key, count in global_record_ids.items() if count > 1)
    all_duplicate_canonical: list[dict[str, Any]] = []
    all_malformed: list[dict[str, Any]] = []
    all_missing_pk: list[dict[str, Any]] = []

    expected_type_order = [RECORD_TYPES[table] for table in TABLE_SCHEMAS]
    for record_type in expected_type_order:
        records = records_by_type.get(record_type, [])
        if not records:
            continue
        table = records[0]["source_table"]
        pk_fields = list(PRIMARY_KEYS[table])
        duplicates = sorted(value for value, matching in canonical_domains[record_type].items() if len(matching) > 1)
        malformed: list[dict[str, Any]] = []
        missing: list[dict[str, Any]] = []
        for record in records:
            missing_fields = [field for field in pk_fields if not nonempty(record["fields"].get(field))]
            if missing_fields:
                missing.append({"record_id": record["record_id"], "missing_fields": missing_fields})
                continue
            suffix = "|".join(str(record["fields"][field]) for field in pk_fields)
            expected_record_id = f"{table}:{suffix}"
            if record["record_id"] != expected_record_id:
                malformed.append({"record_id": record["record_id"], "expected": expected_record_id})

        all_duplicate_canonical.extend({"node_type": record_type, "canonical_id": value} for value in duplicates)
        all_malformed.extend({"node_type": record_type, **item} for item in malformed)
        all_missing_pk.extend({"node_type": record_type, **item} for item in missing)

        policy = GRAPH_FIELD_POLICY[record_type]
        temporal_field = AVAILABILITY_FIELDS[table]
        if record_type == "PO_LINE":
            temporal_description = "inherits PURCHASE_ORDER.po_date via exact po_id"
        elif record_type == "INVOICE_LINE":
            temporal_description = "inherits INVOICE.created_at via exact invoice_id"
        elif record_type == "EMPLOYEE":
            temporal_description = "delivered cutoff snapshot; no row timestamp"
        else:
            temporal_description = temporal_field
        context_only = sorted(field for field in TABLE_SCHEMAS[table] if field not in policy["permitted"])
        prohibited = context_only

        if len(pk_fields) == 1:
            format_string = f"{table}:{{{pk_fields[0]}}}"
        else:
            format_string = f"{table}:" + "|".join(f"{{{field}}}" for field in pk_fields)
        node_entries.append({
            "node_type": record_type,
            "canonical_primary_key": pk_fields,
            "canonical_record_id_format": format_string,
            "source_table": table,
            "source_type": record_type,
            "temporal_eligibility_field": temporal_description,
            "important_identifier_fields": policy["important"],
            "permitted_graph_use_fields": policy["permitted"],
            "candidate_or_conditional_graph_use_fields": policy["candidate"],
            "context_only_fields": context_only,
            "fields_prohibited_from_graph_traversal": prohibited,
            "record_count": len(records),
            "canonical_id_unique": not duplicates,
            "duplicate_canonical_id_count": len(duplicates),
            "malformed_record_id_count": len(malformed),
            "missing_primary_key_count": len(missing),
        })

    payment_orphans = []
    payment_domain = canonical_domains.get("PAYMENT", {})
    invoice_domain = canonical_domains.get("INVOICE", {})
    for record in records_by_type.get("PAYMENT_ALLOCATION", []):
        missing_targets = []
        if str(record["fields"].get("payment_id")) not in payment_domain:
            missing_targets.append("payment_id")
        if str(record["fields"].get("invoice_id")) not in invoice_domain:
            missing_targets.append("invoice_id")
        if missing_targets:
            payment_orphans.append({"record_id": record["record_id"], "orphaned_components": missing_targets})

    integrity = {
        "duplicate_record_id_count": len(all_duplicate_record_ids),
        "duplicate_record_ids": all_duplicate_record_ids[:100],
        "duplicate_canonical_id_count": len(all_duplicate_canonical),
        "duplicate_canonical_ids": all_duplicate_canonical[:100],
        "malformed_record_id_count": len(all_malformed),
        "malformed_record_ids": all_malformed[:100],
        "missing_primary_key_count": len(all_missing_pk),
        "missing_primary_keys": all_missing_pk[:100],
        "orphaned_composite_key_component_count": len(payment_orphans),
        "orphaned_composite_key_components": payment_orphans[:100],
    }
    registry = {
        "registry_version": "graph_node_registry_v1_draft",
        "decision_cutoff": DECISION_CUTOFF,
        "source_corpus_text_manifest_sha256": EXPECTED_TEXT_MANIFEST_SHA256,
        "synthetic_node_types_introduced": [],
        "explicit_exclusion": "GL_JOURNAL is not a node type; journal_id remains a GL_ENTRY grouping/context attribute.",
        "node_types": node_entries,
        "integrity": integrity,
        "total_record_count": sum(item["record_count"] for item in node_entries),
    }
    return registry, integrity


def exact_relation(
    relation_key: str,
    records_by_type: dict[str, list[dict[str, Any]]],
    field_domains: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
    source_type: str,
    source_field: str,
    target_type: str,
    target_field: str,
    condition: Callable[[dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    source_records = [record for record in records_by_type[source_type] if condition is None or condition(record)]
    target_records = records_by_type[target_type]
    target_domain = field_domains[target_type][target_field]
    pairs: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    unresolved: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    unresolved_count = 0
    ambiguous_count = 0
    populated = 0
    for source in source_records:
        value = source["fields"].get(source_field)
        if not nonempty(value):
            continue
        populated += 1
        targets = target_domain.get(str(value), [])
        if len(targets) == 1:
            pairs.append((source, targets[0], source))
        elif not targets:
            unresolved_count += 1
            if len(unresolved) < 20:
                unresolved.append({"source_record_id": source["record_id"], "unresolved_id": value})
        else:
            ambiguous_count += 1
            if len(ambiguous) < 20:
                ambiguous.append({"source_record_id": source["record_id"], "ambiguous_id": value, "target_count": len(targets)})

    source_degree = Counter(source["record_id"] for source, _, _ in pairs)
    target_degree = Counter(target["record_id"] for _, target, _ in pairs)
    source_degrees = [source_degree[record["record_id"]] for record in source_records]
    target_degrees = [target_degree[record["record_id"]] for record in target_records]
    resolved = len(pairs)
    return {
        "relation_key": relation_key,
        "source_node_type": source_type,
        "source_field": source_field,
        "target_node_type": target_type,
        "target_field": target_field,
        "source_row_count": len(source_records),
        "non_null_relationship_count": populated,
        "resolved_target_count": resolved,
        "unresolved_target_count": unresolved_count,
        "ambiguous_target_count": ambiguous_count,
        "resolution_rate_percent_of_populated": pct(resolved, populated),
        "unique_target_count": len(target_degree),
        "cardinality_observed": describe_cardinality(source_degrees, target_degrees),
        "source_out_degree_all_domain": degree_stats(source_degrees),
        "target_in_degree_all_domain": degree_stats(target_degrees),
        "target_in_degree_nonzero": degree_stats(list(target_degree.values())),
        "examples_of_unresolved_ids": unresolved,
        "examples_of_ambiguous_ids": ambiguous,
        "_pairs": pairs,
    }


def relation_from_provenance_pairs(
    relation_key: str,
    source_type: str,
    target_type: str,
    source_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    provenance_pairs: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
) -> dict[str, Any]:
    unique_pairs: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = {}
    provenance_counts: Counter[tuple[str, str]] = Counter()
    for source, target, provenance in provenance_pairs:
        pair_key = (source["record_id"], target["record_id"])
        unique_pairs.setdefault(pair_key, (source, target, provenance))
        provenance_counts[pair_key] += 1
    pairs = list(unique_pairs.values())
    source_degree: dict[str, set[str]] = defaultdict(set)
    target_degree: dict[str, set[str]] = defaultdict(set)
    for source, target, _ in pairs:
        source_degree[source["record_id"]].add(target["record_id"])
        target_degree[target["record_id"]].add(source["record_id"])
    unique_target_count = len(target_degree)
    source_degrees = [len(source_degree.get(record["record_id"], set())) for record in source_records]
    target_degrees = [len(target_degree.get(record["record_id"], set())) for record in target_records]
    return {
        "relation_key": relation_key,
        "source_node_type": source_type,
        "target_node_type": target_type,
        "provenance_record_count": len(provenance_pairs),
        "unique_source_target_pair_count": len(pairs),
        "parallel_provenance_pair_count": sum(count > 1 for count in provenance_counts.values()),
        "source_row_count": len(source_records),
        "non_null_relationship_count": len(provenance_pairs),
        "resolved_target_count": len(provenance_pairs),
        "unresolved_target_count": 0,
        "ambiguous_target_count": 0,
        "resolution_rate_percent_of_populated": 100.0 if provenance_pairs else 0.0,
        "unique_target_count": unique_target_count,
        "cardinality_observed": describe_cardinality(source_degrees, target_degrees),
        "source_out_degree_all_domain": degree_stats(source_degrees),
        "target_in_degree_all_domain": degree_stats(target_degrees),
        "target_in_degree_nonzero": degree_stats([len(value) for value in target_degree.values() if value]),
        "examples_of_unresolved_ids": [],
        "examples_of_ambiguous_ids": [],
        "_pairs": provenance_pairs,
    }


def serializable_relation_audit(value: dict[str, Any]) -> dict[str, Any]:
    return {key: child for key, child in value.items() if not key.startswith("_")}


def build_base_relation_audits(
    records_by_type: dict[str, list[dict[str, Any]]],
    field_domains: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    specifications = [
        ("PO_LINE_TO_PURCHASE_ORDER", "PO_LINE", "po_id", "PURCHASE_ORDER", "po_id"),
        ("INVOICE_TO_PURCHASE_ORDER", "INVOICE", "po_id", "PURCHASE_ORDER", "po_id"),
        ("INVOICE_LINE_TO_PO_LINE", "INVOICE_LINE", "po_line_id", "PO_LINE", "po_line_id"),
        ("INVOICE_LINE_TO_INVOICE", "INVOICE_LINE", "invoice_id", "INVOICE", "invoice_id"),
        ("APPROVAL_EVENT_TO_INVOICE", "APPROVAL_EVENT", "invoice_id", "INVOICE", "invoice_id"),
        ("PAYMENT_ALLOCATION_TO_PAYMENT", "PAYMENT_ALLOCATION", "payment_id", "PAYMENT", "payment_id"),
        ("PAYMENT_ALLOCATION_TO_INVOICE", "PAYMENT_ALLOCATION", "invoice_id", "INVOICE", "invoice_id"),
        ("VENDOR_CHANGE_TO_VENDOR", "VENDOR_CHANGE", "vendor_id", "VENDOR", "vendor_id"),
        ("PURCHASE_ORDER_TO_VENDOR", "PURCHASE_ORDER", "vendor_id", "VENDOR", "vendor_id"),
        ("INVOICE_TO_VENDOR", "INVOICE", "vendor_id", "VENDOR", "vendor_id"),
        ("PAYMENT_TO_VENDOR", "PAYMENT", "vendor_id", "VENDOR", "vendor_id"),
    ]
    audits = []
    internal: dict[str, dict[str, Any]] = {}
    for spec in specifications:
        audit = exact_relation(spec[0], records_by_type, field_domains, *spec[1:])
        internal[spec[0]] = audit
        audits.append(serializable_relation_audit(audit))

    allocation_payment = internal["PAYMENT_ALLOCATION_TO_PAYMENT"]
    allocation_invoice = internal["PAYMENT_ALLOCATION_TO_INVOICE"]
    payment_target_by_provenance = {
        provenance["record_id"]: target for _, target, provenance in allocation_payment["_pairs"]
    }
    invoice_target_by_provenance = {
        provenance["record_id"]: target for _, target, provenance in allocation_invoice["_pairs"]
    }
    derived_pairs = []
    for provenance_id in sorted(set(payment_target_by_provenance) & set(invoice_target_by_provenance)):
        provenance = next(
            record for record in records_by_type["PAYMENT_ALLOCATION"] if record["record_id"] == provenance_id
        )
        derived_pairs.append((payment_target_by_provenance[provenance_id], invoice_target_by_provenance[provenance_id], provenance))
    derived = relation_from_provenance_pairs(
        "PAYMENT_TO_INVOICE_VIA_ALLOCATION",
        "PAYMENT",
        "INVOICE",
        records_by_type["PAYMENT"],
        records_by_type["INVOICE"],
        derived_pairs,
    )
    internal[derived["relation_key"]] = derived
    audits.append(serializable_relation_audit(derived))
    return audits, internal


def actor_class(value: str) -> str:
    upper = value.upper()
    if upper.startswith("SYSTEM-") or upper.startswith("SYSTEM_"):
        return "explicit_system_actor"
    if any(token in upper for token in ("SERVICE", "WORKFLOW", "PROCESSOR", "ENGINE", "INTERFACE", "BOT")):
        return "service_actor_style"
    if upper in {"EMP-MANUAL-AP", "TREASURY-PORTAL-USER"}:
        return "shared_role_or_portal_actor_style"
    return "unclassified_unmatched_actor"


def build_employee_audit(
    records_by_type: dict[str, list[dict[str, Any]]],
    field_domains: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    specs = [
        ("APPROVAL_EVENT_APPROVER_EMPLOYEE", "APPROVAL_EVENT", "approver_id"),
        ("AUDIT_EVENT_ACTOR_EMPLOYEE", "AUDIT_EVENT", "actor_id"),
        ("VENDOR_CHANGE_CHANGED_BY_EMPLOYEE", "VENDOR_CHANGE", "changed_by"),
        ("PURCHASE_ORDER_CREATED_BY_EMPLOYEE", "PURCHASE_ORDER", "created_by"),
    ]
    field_audits = []
    internal: dict[str, dict[str, Any]] = {}
    employee_ids = set(field_domains["EMPLOYEE"]["employee_id"])
    for relation_key, source_type, source_field in specs:
        relation = exact_relation(
            relation_key,
            records_by_type,
            field_domains,
            source_type,
            source_field,
            "EMPLOYEE",
            "employee_id",
        )
        internal[relation_key] = relation
        populated_values = [
            str(record["fields"][source_field]) for record in records_by_type[source_type]
            if nonempty(record["fields"].get(source_field))
        ]
        unmatched = [value for value in populated_values if value not in employee_ids]
        unmatched_counts = Counter(unmatched)
        category_counts = Counter()
        for value, count in unmatched_counts.items():
            category_counts[actor_class(value)] += count
        all_system_like = bool(unmatched) and "unclassified_unmatched_actor" not in category_counts
        if not unmatched:
            classification = "APPROVED_TIER_A"
        elif all_system_like:
            classification = "CONDITIONAL"
        else:
            classification = "NON_TRAVERSABLE"
        field_audits.append({
            "relation_key": relation_key,
            "source_node_type": source_type,
            "source_field": source_field,
            "source_row_count": len(records_by_type[source_type]),
            "total_populated_values": len(populated_values),
            "exact_employee_matches": relation["resolved_target_count"],
            "unmatched_values": len(unmatched),
            "distinct_unmatched_values": len(unmatched_counts),
            "percentage_resolved": pct(relation["resolved_target_count"], len(populated_values)),
            "unmatched_actor_style_counts": dict(sorted(category_counts.items())),
            "all_unmatched_appear_system_service_or_shared_role": all_system_like,
            "representative_unmatched_examples": [
                {"value": value, "count": count, "classification": actor_class(value)}
                for value, count in sorted(unmatched_counts.items())[:20]
            ],
            "proposed_relation_classification": classification,
            "edge_policy": "Create an Employee edge only for an exact employee_id match. Preserve unmatched actor_id/approver_id text as context; do not discard or synthesize Employee nodes.",
            "degree_statistics": {
                "source_out_degree_all_domain": relation["source_out_degree_all_domain"],
                "employee_in_degree_all_domain": relation["target_in_degree_all_domain"],
            },
        })
    return {
        "audit_version": "employee_reference_audit_v1",
        "employee_record_count": len(records_by_type["EMPLOYEE"]),
        "source_fields": field_audits,
        "system_actor_policy": "Unmatched actor values remain operational context and are never silently discarded or converted to Employee nodes.",
    }, internal


def build_gl_audit(
    records_by_type: dict[str, list[dict[str, Any]]],
    canonical_domains: dict[str, dict[str, list[dict[str, Any]]]],
    field_domains: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, list[str]]]:
    rows = records_by_type["GL_ENTRY"]
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in rows:
        by_type[str(record["fields"].get("transaction_type"))].append(record)
    type_audits = []
    relation_audits: dict[str, dict[str, Any]] = {}
    mapping_by_target: dict[str, list[str]] = defaultdict(list)
    for transaction_type in sorted(by_type):
        type_rows = by_type[transaction_type]
        populated = [record for record in type_rows if nonempty(record["fields"].get("source_transaction_id"))]
        prefix_distribution = Counter(identifier_prefix(record["fields"].get("source_transaction_id")) for record in populated)
        exact_counts = Counter()
        ambiguous_rows = []
        unresolved_rows = []
        ambiguous_count = 0
        unresolved_count = 0
        distinct_unresolved: set[str] = set()
        resolved_types: Counter[str] = Counter()
        for record in populated:
            source_id = str(record["fields"]["source_transaction_id"])
            matches = [node_type for node_type, domain in canonical_domains.items() if source_id in domain]
            for node_type in matches:
                exact_counts[node_type] += 1
            if len(matches) == 1:
                resolved_types[matches[0]] += 1
            elif len(matches) > 1:
                ambiguous_count += 1
                if len(ambiguous_rows) < 20:
                    ambiguous_rows.append({"record_id": record["record_id"], "source_transaction_id": source_id, "matched_node_types": matches})
            else:
                unresolved_count += 1
                distinct_unresolved.add(source_id)
                if len(unresolved_rows) < 20:
                    unresolved_rows.append({"record_id": record["record_id"], "source_transaction_id": source_id})
        unique_target_types = sorted(resolved_types)
        deterministic = (
            len(unique_target_types) == 1
            and sum(resolved_types.values()) == len(populated)
            and ambiguous_count == 0
        )
        proposed_target = unique_target_types[0] if deterministic else None
        type_audits.append({
            "transaction_type": transaction_type,
            "count": len(type_rows),
            "non_null_source_transaction_id_count": len(populated),
            "source_transaction_id_prefix_distribution": dict(sorted(prefix_distribution.items())),
            "exact_match_counts_by_operational_node_type": {
                node_type: exact_counts[node_type] for node_type in sorted(canonical_domains)
            },
            "ambiguous_cross_type_match_count": ambiguous_count,
            "unresolved_value_count": unresolved_count,
            "distinct_unresolved_value_count": len(distinct_unresolved),
            "representative_unresolved_examples": unresolved_rows,
            "representative_ambiguous_examples": ambiguous_rows,
            "resolved_type_distribution": dict(sorted(resolved_types.items())),
            "proposed_target_node_type": proposed_target,
            "deterministic_type_mapping_supported": deterministic,
            "proposed_status": "READY_FOR_FREEZE" if deterministic else "UNRESOLVED",
        })
        if deterministic and proposed_target:
            mapping_by_target[proposed_target].append(transaction_type)
            relation_key = f"GL_ENTRY_{transaction_type.upper()}_TO_{proposed_target}"
            target_pk = PRIMARY_KEYS[records_by_type[proposed_target][0]["source_table"]]
            if len(target_pk) != 1:
                raise RuntimeError(f"unexpected composite GL target: {proposed_target}")
            relation_audits[relation_key] = exact_relation(
                relation_key,
                records_by_type,
                field_domains,
                "GL_ENTRY",
                "source_transaction_id",
                proposed_target,
                target_pk[0],
                condition=lambda record, wanted=transaction_type: record["fields"].get("transaction_type") == wanted,
            )

    proposed_mapping = {
        item["transaction_type"]: {
            "permitted_target_node_types": [item["proposed_target_node_type"]] if item["proposed_target_node_type"] else [],
            "status": item["proposed_status"],
        }
        for item in type_audits
    }
    audit = {
        "audit_version": "gl_transaction_type_audit_v1",
        "gl_entry_count": len(rows),
        "distinct_transaction_type_count": len(type_audits),
        "transaction_types": type_audits,
        "proposed_mapping_registry": proposed_mapping,
        "proposed_edge_policy": [
            "source_transaction_id is nonempty",
            "transaction_type is in the frozen approved registry",
            "source_transaction_id exactly matches one canonical target ID",
            "target type agrees with transaction_type",
            "both records are cutoff-eligible",
        ],
        "prohibited_methods": ["nearest-ID matching", "semantic similarity", "ambiguous target selection"],
    }
    return audit, relation_audits, {key: sorted(value) for key, value in mapping_by_target.items()}


ENTITY_TYPE_EXPECTATIONS = {
    "bank_transaction": "BANK_TRANSACTION",
    "invoice": "INVOICE",
    "payment": "PAYMENT",
    "purchase_order": "PURCHASE_ORDER",
    "vendor": "VENDOR",
}


def build_audit_event_entity_audit(
    records_by_type: dict[str, list[dict[str, Any]]],
    canonical_domains: dict[str, dict[str, list[dict[str, Any]]]],
    field_domains: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, list[str]]]:
    rows = records_by_type["AUDIT_EVENT"]
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in rows:
        by_type[str(record["fields"].get("entity_type"))].append(record)
    journal_domain = field_domains["GL_ENTRY"]["journal_id"]
    type_audits = []
    relation_audits: dict[str, dict[str, Any]] = {}
    mapping_by_target: dict[str, list[str]] = defaultdict(list)
    for entity_type in sorted(by_type):
        type_rows = by_type[entity_type]
        populated = [record for record in type_rows if nonempty(record["fields"].get("entity_id"))]
        exact_counts = Counter()
        resolved_types: Counter[str] = Counter()
        unresolved_examples = []
        ambiguous_examples = []
        unresolved_count = 0
        ambiguous_count = 0
        journal_group_degrees = []
        for record in populated:
            entity_id = str(record["fields"]["entity_id"])
            matches = [node_type for node_type, domain in canonical_domains.items() if entity_id in domain]
            for node_type in matches:
                exact_counts[node_type] += 1
            if len(matches) == 1:
                resolved_types[matches[0]] += 1
            elif len(matches) > 1:
                ambiguous_count += 1
                if len(ambiguous_examples) < 20:
                    ambiguous_examples.append({"record_id": record["record_id"], "entity_id": entity_id, "matched_node_types": matches})
            else:
                unresolved_count += 1
                if len(unresolved_examples) < 20:
                    unresolved_examples.append({"record_id": record["record_id"], "entity_id": entity_id})
            if entity_id in journal_domain:
                journal_group_degrees.append(len(journal_domain[entity_id]))

        expected_target = ENTITY_TYPE_EXPECTATIONS.get(entity_type)
        deterministic = (
            expected_target is not None
            and resolved_types == Counter({expected_target: len(populated)})
            and ambiguous_count == 0
        )
        proposed_status = "READY_FOR_FREEZE" if deterministic else "UNRESOLVED"
        type_audits.append({
            "entity_type": entity_type,
            "count": len(type_rows),
            "non_null_entity_id_count": len(populated),
            "exact_match_counts_by_operational_node_type": {
                node_type: exact_counts[node_type] for node_type in sorted(canonical_domains)
            },
            "resolved_type_distribution": dict(sorted(resolved_types.items())),
            "resolved_exactly_one_count": sum(resolved_types.values()),
            "unresolved_count": unresolved_count,
            "ambiguous_count": ambiguous_count,
            "representative_unresolved_examples": unresolved_examples,
            "representative_ambiguous_examples": ambiguous_examples,
            "expected_type_consistent_target": expected_target,
            "deterministic_type_mapping_supported": deterministic,
            "proposed_status": proposed_status,
            "journal_id_grouping_attribute_match": {
                "matching_audit_event_count": len(journal_group_degrees),
                "gl_entry_group_degree_statistics": degree_stats(journal_group_degrees),
                "policy": "context/grouping evidence only; no GL_JOURNAL node exists",
            },
        })
        if deterministic and expected_target:
            mapping_by_target[expected_target].append(entity_type)
            target_pk = PRIMARY_KEYS[records_by_type[expected_target][0]["source_table"]]
            relation_key = f"AUDIT_EVENT_{entity_type.upper()}_TO_{expected_target}"
            relation_audits[relation_key] = exact_relation(
                relation_key,
                records_by_type,
                field_domains,
                "AUDIT_EVENT",
                "entity_id",
                expected_target,
                target_pk[0],
                condition=lambda record, wanted=entity_type: record["fields"].get("entity_type") == wanted,
            )

    audit = {
        "audit_version": "audit_event_entity_type_audit_v1",
        "audit_event_count": len(rows),
        "distinct_entity_type_count": len(type_audits),
        "entity_types": type_audits,
        "mapping_policy": "Create an edge only for an exact canonical-ID match where entity_type agrees with the approved target node type. gl_journal remains unresolved because no journal-header node exists.",
        "synthetic_gl_journal_node_created": False,
    }
    return audit, relation_audits, {key: sorted(value) for key, value in mapping_by_target.items()}


def decimal_value(value: Any) -> Decimal | None:
    if not nonempty(value):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def payment_bank_collision_stats(
    payments: list[dict[str, Any]],
    bank_transactions: list[dict[str, Any]],
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
) -> dict[str, Any]:
    payment_degree: dict[str, set[str]] = defaultdict(set)
    bank_degree: dict[str, set[str]] = defaultdict(set)
    ref_payments: dict[str, set[str]] = defaultdict(set)
    ref_banks: dict[str, set[str]] = defaultdict(set)
    for payment, bank in pairs:
        payment_degree[payment["record_id"]].add(bank["record_id"])
        bank_degree[bank["record_id"]].add(payment["record_id"])
        ref = str(payment["fields"].get("reference_number"))
        ref_payments[ref].add(payment["record_id"])
        ref_banks[ref].add(bank["record_id"])
    categories = Counter()
    for ref in sorted(set(ref_payments) | set(ref_banks)):
        p_count = len(ref_payments[ref])
        b_count = len(ref_banks[ref])
        if p_count == 1 and b_count == 1:
            categories["1:1"] += 1
        elif p_count == 1 and b_count > 1:
            categories["1:N"] += 1
        elif p_count > 1 and b_count == 1:
            categories["N:1"] += 1
        elif p_count > 1 and b_count > 1:
            categories["N:M"] += 1
    payment_degrees = [len(payment_degree[record["record_id"]]) for record in payments]
    bank_degrees = [len(bank_degree[record["record_id"]]) for record in bank_transactions]
    return {
        "candidate_pair_count": len(pairs),
        "matched_payment_count": sum(bool(payment_degree[record["record_id"]]) for record in payments),
        "matched_bank_transaction_count": sum(bool(bank_degree[record["record_id"]]) for record in bank_transactions),
        "unmatched_payment_count": sum(not payment_degree[record["record_id"]] for record in payments),
        "unmatched_bank_transaction_count": sum(not bank_degree[record["record_id"]] for record in bank_transactions),
        "reference_group_cardinality_counts": {key: categories[key] for key in ("1:1", "1:N", "N:1", "N:M")},
        "ambiguous_payment_count": sum(len(value) > 1 for value in payment_degree.values()),
        "ambiguous_bank_transaction_count": sum(len(value) > 1 for value in bank_degree.values()),
        "payment_candidate_degree": degree_stats(payment_degrees),
        "bank_transaction_candidate_degree": degree_stats(bank_degrees),
    }


def temporal_delta_stats(pairs: list[tuple[dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    deltas: list[int] = []
    missing = 0
    for payment, bank in pairs:
        payment_date = parse_datetime(payment["fields"].get("payment_date"))
        posted_date = parse_datetime(bank["fields"].get("posted_date"))
        if payment_date is None or posted_date is None:
            missing += 1
            continue
        deltas.append((posted_date.date() - payment_date.date()).days)
    return {
        "pair_count": len(pairs),
        "parsed_delta_count": len(deltas),
        "missing_or_unparseable_count": missing,
        "negative_delta_count": sum(value < 0 for value in deltas),
        "same_day_count": sum(value == 0 for value in deltas),
        "positive_delta_count": sum(value > 0 for value in deltas),
        "minimum_days": min(deltas) if deltas else None,
        "maximum_days": max(deltas) if deltas else None,
        "mean_days": round(mean(deltas), 6) if deltas else None,
        "median_days": round(float(median(deltas)), 6) if deltas else None,
        "p95_days_nearest_rank": nearest_rank_percentile(deltas, 0.95) if deltas else None,
    }


def build_payment_bank_audit(records_by_type: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any], dict[str, list[tuple[dict[str, Any], dict[str, Any]]]]]:
    payments = records_by_type["PAYMENT"]
    banks = records_by_type["BANK_TRANSACTION"]
    payments_by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    banks_by_ref: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in payments:
        value = record["fields"].get("reference_number")
        if nonempty(value):
            payments_by_ref[str(value)].append(record)
    for record in banks:
        value = record["fields"].get("payment_reference")
        if nonempty(value):
            banks_by_ref[str(value)].append(record)

    reference_pairs = [
        (payment, bank)
        for ref in sorted(set(payments_by_ref) & set(banks_by_ref))
        for payment in payments_by_ref[ref]
        for bank in banks_by_ref[ref]
    ]

    def currency(pair: tuple[dict[str, Any], dict[str, Any]]) -> bool:
        payment, bank = pair
        return payment["fields"].get("payment_currency") == bank["fields"].get("currency")

    def account(pair: tuple[dict[str, Any], dict[str, Any]]) -> bool:
        payment, bank = pair
        return payment["fields"].get("bank_account_id") == bank["fields"].get("bank_account_id")

    def amount(pair: tuple[dict[str, Any], dict[str, Any]]) -> bool:
        payment, bank = pair
        left = decimal_value(payment["fields"].get("payment_amount"))
        right = decimal_value(bank["fields"].get("amount"))
        return left is not None and right is not None and left == abs(right)

    def direction(pair: tuple[dict[str, Any], dict[str, Any]]) -> bool:
        _, bank = pair
        return str(bank["fields"].get("direction", "")).lower() == "debit"

    def posted_on_or_after(pair: tuple[dict[str, Any], dict[str, Any]]) -> bool:
        payment, bank = pair
        payment_date = parse_datetime(payment["fields"].get("payment_date"))
        posted_date = parse_datetime(bank["fields"].get("posted_date"))
        return payment_date is not None and posted_date is not None and posted_date.date() >= payment_date.date()

    predicates: list[tuple[str, list[Callable[[tuple[dict[str, Any], dict[str, Any]]], bool]], str]] = [
        ("REFERENCE_ONLY", [], "exact reference"),
        ("REFERENCE_PLUS_CURRENCY", [currency], "exact reference and currency"),
        ("REFERENCE_PLUS_BANK_ACCOUNT", [account], "exact reference and bank_account_id"),
        ("REFERENCE_PLUS_ABS_AMOUNT", [amount], "exact reference and payment_amount == abs(bank amount)"),
        ("REFERENCE_PLUS_DEBIT_DIRECTION", [direction], "exact reference and debit direction"),
        ("REFERENCE_PLUS_CURRENCY_ABS_AMOUNT", [currency, amount], "exact reference, currency, and absolute amount"),
        ("REFERENCE_PLUS_CURRENCY_ABS_AMOUNT_DEBIT", [currency, amount, direction], "exact reference, currency, absolute amount, and debit direction"),
        ("REFERENCE_PLUS_CURRENCY_ACCOUNT_ABS_AMOUNT_DEBIT", [currency, account, amount, direction], "all exact non-temporal operational constraints"),
        ("REFERENCE_PLUS_CURRENCY_ABS_AMOUNT_DEBIT_POSTED_ON_OR_AFTER", [currency, amount, direction, posted_on_or_after], "corroborated candidate plus nonnegative posting lag; audit-only, not a frozen window"),
        ("REFERENCE_PLUS_ALL_AND_POSTED_ON_OR_AFTER", [currency, account, amount, direction, posted_on_or_after], "all exact constraints plus nonnegative posting lag; audit-only, not a frozen window"),
    ]
    candidate_sets: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    predicate_audits = []
    for name, tests, description in predicates:
        pairs = [pair for pair in reference_pairs if all(test(pair) for test in tests)]
        candidate_sets[name] = pairs
        predicate_audits.append({
            "predicate_name": name,
            "description": description,
            **payment_bank_collision_stats(payments, banks, pairs),
        })

    payment_accounts = Counter(str(record["fields"].get("bank_account_id")) for record in payments if nonempty(record["fields"].get("bank_account_id")))
    bank_accounts = Counter(str(record["fields"].get("bank_account_id")) for record in banks if nonempty(record["fields"].get("bank_account_id")))
    reference_stats = payment_bank_collision_stats(payments, banks, reference_pairs)
    matched_refs = set(payments_by_ref) & set(banks_by_ref)
    audit = {
        "audit_version": "payment_bank_relation_audit_v1",
        "payment_count": len(payments),
        "bank_transaction_count": len(banks),
        "exact_reference_behavior": {
            "non_null_payment_reference_count": sum(len(value) for value in payments_by_ref.values()),
            "non_null_bank_payment_reference_count": sum(len(value) for value in banks_by_ref.values()),
            "distinct_payment_reference_count": len(payments_by_ref),
            "distinct_bank_payment_reference_count": len(banks_by_ref),
            "distinct_exact_reference_match_count": len(matched_refs),
            "exact_reference_candidate_pair_count": len(reference_pairs),
            **reference_stats,
            "unmatched_payment_reference_examples": sorted(set(payments_by_ref) - set(banks_by_ref))[:20],
            "unmatched_bank_payment_reference_examples": sorted(set(banks_by_ref) - set(payments_by_ref))[:20],
        },
        "bank_account_identifier_domain_audit": {
            "distinct_payment_bank_account_id_count": len(payment_accounts),
            "distinct_bank_transaction_bank_account_id_count": len(bank_accounts),
            "exact_identifier_intersection_count": len(set(payment_accounts) & set(bank_accounts)),
            "payment_prefix_distribution": dict(sorted(Counter(identifier_prefix(value) for value in payment_accounts).items())),
            "bank_transaction_prefix_distribution": dict(sorted(Counter(identifier_prefix(value) for value in bank_accounts).items())),
            "policy": "No crosswalk or normalization inferred. Exact account comparison only.",
        },
        "candidate_predicates": predicate_audits,
        "temporal_relationship_analysis": {
            "reference_only_delta": temporal_delta_stats(reference_pairs),
            "corroborated_without_bank_account_delta": temporal_delta_stats(candidate_sets["REFERENCE_PLUS_CURRENCY_ABS_AMOUNT_DEBIT"]),
            "maximum_temporal_window_policy": "UNRESOLVED — REQUIRES POLICY FREEZE",
            "statement": "Observed lag distributions are descriptive only and were not optimized against labels. No maximum window is selected.",
        },
        "embeddings_used": False,
        "collision_resolution_policy": "Never select one candidate when multiple remain; preserve every collision group.",
        "proposed_relation_status": "UNRESOLVED",
        "freeze_recommendation": "Exclude PAYMENT↔BANK_TRANSACTION traversal from the READY_FOR_FREEZE core until identifier-domain and temporal policy are independently frozen.",
    }
    return audit, candidate_sets


def establish_temporal_eligibility(
    records_by_type: dict[str, list[dict[str, Any]]],
    field_domains: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
) -> dict[str, Any]:
    po_domain = field_domains["PURCHASE_ORDER"]["po_id"]
    invoice_domain = field_domains["INVOICE"]["invoice_id"]
    node_audits = []
    for table, record_type in RECORD_TYPES.items():
        records = records_by_type[record_type]
        parsed_count = 0
        missing_count = 0
        inherited_unresolved = 0
        after_cutoff = 0
        metadata_mismatch = 0
        timestamps: list[datetime] = []
        for record in records:
            if record_type == "PO_LINE":
                parents = po_domain.get(str(record["fields"].get("po_id")), [])
                if len(parents) != 1:
                    inherited_unresolved += 1
                    availability = None
                else:
                    availability = parse_datetime(parents[0]["fields"].get("po_date"))
                if record["available_at"] != "INHERITED_FROM_PURCHASE_ORDER":
                    metadata_mismatch += 1
            elif record_type == "INVOICE_LINE":
                parents = invoice_domain.get(str(record["fields"].get("invoice_id")), [])
                if len(parents) != 1:
                    inherited_unresolved += 1
                    availability = None
                else:
                    availability = parse_datetime(parents[0]["fields"].get("created_at"))
                if record["available_at"] != "INHERITED_FROM_INVOICE":
                    metadata_mismatch += 1
            elif record_type == "EMPLOYEE":
                availability = CUTOFF
                if record["available_at"] != "DELIVERED_CUTOFF_SNAPSHOT":
                    metadata_mismatch += 1
            else:
                field = AVAILABILITY_FIELDS[table]
                availability = parse_datetime(record["fields"].get(field)) if field else None
                if field and str(record["fields"].get(field)) != str(record["available_at"]):
                    metadata_mismatch += 1
            record["_availability"] = availability
            record["_eligible"] = availability is not None and availability.date() <= CUTOFF.date()
            if availability is None:
                missing_count += 1
            else:
                parsed_count += 1
                timestamps.append(availability)
                if availability.date() > CUTOFF.date():
                    after_cutoff += 1
        if record_type == "PO_LINE":
            rule = "parent PURCHASE_ORDER.po_date <= 2026-06-30"
        elif record_type == "INVOICE_LINE":
            rule = "parent INVOICE.created_at <= 2026-06-30"
        elif record_type == "EMPLOYEE":
            rule = "delivered cutoff snapshot; no row timestamp"
        else:
            rule = f"{AVAILABILITY_FIELDS[table]} <= 2026-06-30"
        node_audits.append({
            "node_type": record_type,
            "record_count": len(records),
            "eligibility_rule": rule,
            "parsed_or_snapshot_availability_count": parsed_count,
            "missing_or_unparseable_availability_count": missing_count,
            "inherited_parent_unresolved_count": inherited_unresolved,
            "after_cutoff_count": after_cutoff,
            "metadata_available_at_mismatch_count": metadata_mismatch,
            "eligible_count": sum(record["_eligible"] for record in records),
            "minimum_availability": min(timestamps).isoformat() if timestamps else None,
            "maximum_availability": max(timestamps).isoformat() if timestamps else None,
        })
    return {
        "audit_version": "graph_temporal_integrity_audit_v1",
        "decision_cutoff": DECISION_CUTOFF,
        "node_eligibility": node_audits,
        "prohibited_availability_substitutions": [
            "INVOICE.due_date",
            "PURCHASE_ORDER.expected_delivery_date",
            "BANK_TRANSACTION.transaction_date when posted_date controls availability",
        ],
        "edge_rule": "eligible(source_node, cutoff) AND eligible(target_node, cutoff) AND eligible(provenance_record, cutoff)",
        "derived_edge_effective_availability_rule": "maximum availability timestamp of all participating evidence records",
        "edge_eligibility": [],
    }


def edge_temporal_audit(relation: dict[str, Any]) -> dict[str, Any]:
    pairs = relation.get("_pairs", [])
    effective: list[datetime] = []
    source_ineligible = 0
    target_ineligible = 0
    provenance_ineligible = 0
    all_eligible = 0
    for source, target, provenance in pairs:
        source_ok = bool(source.get("_eligible"))
        target_ok = bool(target.get("_eligible"))
        provenance_ok = bool(provenance.get("_eligible"))
        source_ineligible += not source_ok
        target_ineligible += not target_ok
        provenance_ineligible += not provenance_ok
        if source_ok and target_ok and provenance_ok:
            all_eligible += 1
            timestamps = [record.get("_availability") for record in (source, target, provenance)]
            if all(timestamp is not None for timestamp in timestamps):
                effective.append(max(timestamps))
    return {
        "relation_key": relation["relation_key"],
        "source_node_type": relation["source_node_type"],
        "target_node_type": relation["target_node_type"],
        "edge_instance_or_provenance_count": len(pairs),
        "all_participants_eligible_count": all_eligible,
        "source_ineligible_count": source_ineligible,
        "target_ineligible_count": target_ineligible,
        "provenance_ineligible_count": provenance_ineligible,
        "minimum_effective_availability": min(effective).isoformat() if effective else None,
        "maximum_effective_availability": max(effective).isoformat() if effective else None,
        "effective_availability_after_cutoff_count": sum(value.date() > CUTOFF.date() for value in effective),
        "rule": "effective availability is max(source, target, provenance); all must be cutoff-eligible",
    }


def attribute_hub_stats(
    records_by_type: dict[str, list[dict[str, Any]]],
    field_names: set[str],
    normalize: Callable[[Any], str] | None = None,
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    populated = 0
    for record_type, records in records_by_type.items():
        for record in records:
            for field in field_names:
                if field not in record["fields"]:
                    continue
                value = record["fields"].get(field)
                if not nonempty(value):
                    continue
                populated += 1
                key = normalize(value) if normalize else str(value)
                counts[key] += 1
                sources[f"{record_type}.{field}"] += 1
    return {
        "fields": sorted(field_names),
        "populated_record_field_count": populated,
        "distinct_value_count": len(counts),
        "degree_statistics_nonzero_values": degree_stats(list(counts.values())),
        "top_values": [{"value": value, "degree": count} for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:20]],
        "source_distribution": dict(sorted(sources.items())),
    }


def build_hub_audit(
    records_by_type: dict[str, list[dict[str, Any]]],
    relation_audits: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    relation_risks = []
    for key in sorted(relation_audits):
        relation = relation_audits[key]
        target = relation["target_node_type"]
        if target == "VENDOR":
            recommendation = "restricted traversal"
            risk = "high-degree hub-sensitive node type"
        elif target == "EMPLOYEE":
            recommendation = "restricted traversal"
            risk = "organizational hub; reverse expansion can fan out"
        else:
            recommendation = "traversable"
            risk = "transactional exact-ID relation; apply motif and 40-record budget caps"
        relation_risks.append({
            "relation_key": key,
            "target_node_type": target,
            "target_in_degree_all_domain": relation["target_in_degree_all_domain"],
            "target_in_degree_nonzero": relation["target_in_degree_nonzero"],
            "recommendation": recommendation,
            "risk_rationale": risk,
        })

    node_neighbor_sets: dict[str, dict[str, set[str]]] = {
        "VENDOR": defaultdict(set),
        "EMPLOYEE": defaultdict(set),
    }
    for relation in relation_audits.values():
        target_type = relation["target_node_type"]
        if target_type not in node_neighbor_sets:
            continue
        for source, target, _ in relation.get("_pairs", []):
            node_neighbor_sets[target_type][target["record_id"]].add(source["record_id"])
    node_hubs = []
    for node_type in ("VENDOR", "EMPLOYEE"):
        values = [len(node_neighbor_sets[node_type][record["record_id"]]) for record in records_by_type[node_type]]
        node_hubs.append({
            "node_type": node_type,
            "record_count": len(records_by_type[node_type]),
            "combined_exact_relation_neighbor_degree": degree_stats(values),
            "recommendation": "restricted traversal",
            "restriction": "allow exact anchoring and direct evidence attachment; prohibit automatic unconstrained reverse-neighborhood expansion",
        })

    status_fields = {
        field for fields in TABLE_SCHEMAS.values() for field in fields
        if field == "status" or field.endswith("_status")
    }
    date_fields = {
        field for fields in TABLE_SCHEMAS.values() for field in fields
        if field.endswith("_date") or field.endswith("_at") or field in {"timestamp", "event_timestamp", "changed_at"}
    }
    attribute_specs = [
        ("bank_account_id", {"bank_account_id"}, None),
        ("gl_account", {"gl_account"}, None),
        ("department", {"department"}, None),
        ("cost_center", {"cost_center"}, None),
        ("currency", {"currency", "payment_currency"}, None),
        ("source_system", {"source_system"}, None),
        ("status_fields", status_fields, None),
        ("calendar_dates", date_fields, lambda value: str(value)[:10]),
        ("journal_id", {"journal_id"}, None),
    ]
    attributes = []
    for name, fields, normalizer in attribute_specs:
        item = attribute_hub_stats(records_by_type, fields, normalizer)
        item.update({
            "attribute_group": name,
            "recommendation": "context only",
            "graph_bridge_policy": "prohibited traversal",
            "rationale": "operational attribute/filtering context, not an approved graph node or cross-record bridge",
        })
        if name == "journal_id":
            item["rationale"] = "GL_ENTRY grouping attribute only; no journal-header source record and no GL_JOURNAL node"
        attributes.append(item)
    return {
        "audit_version": "graph_hub_risk_audit_v1",
        "degree_definition": "Relation target degree counts resolved incoming source records; combined node degree counts distinct neighboring source records. Attribute degree counts records sharing an exact value.",
        "node_hub_risk": node_hubs,
        "relation_hub_risk": relation_risks,
        "attribute_bridge_risk": attributes,
        "policy": "Vendor and Employee remain nodes but require restricted expansion. Attribute bridge nodes are not introduced.",
    }


def relation_status(audit: dict[str, Any]) -> str:
    if audit.get("unresolved_target_count", 0) or audit.get("ambiguous_target_count", 0):
        return "UNRESOLVED"
    if audit.get("non_null_relationship_count", 0) == 0:
        return "REJECTED"
    return "READY_FOR_FREEZE"


def registry_entry(
    relation_type: str,
    audit: dict[str, Any],
    source_fields: list[str],
    target_fields: list[str],
    provenance_record_type: str,
    confidence_tier: str,
    cardinality_expected: str,
    traversable: bool,
    reverse_traversal: bool,
    hub_risk: str,
    status: str | None = None,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "relation_type": relation_type,
        "source_node_type": audit["source_node_type"],
        "target_node_type": audit["target_node_type"],
        "source_fields": source_fields,
        "target_fields": target_fields,
        "provenance_record_type": provenance_record_type,
        "confidence_tier": confidence_tier,
        "cardinality_expected": cardinality_expected,
        "cardinality_observed": audit["cardinality_observed"],
        "temporal_rule": "eligible(source, cutoff) AND eligible(target, cutoff) AND eligible(provenance, cutoff); effective availability = max(participant availability)",
        "ambiguity_policy": "Exact, type-consistent, unique canonical-ID match only; null, unresolved, or ambiguous values create no edge.",
        "traversable": traversable,
        "reverse_traversal": reverse_traversal,
        "hub_risk": hub_risk,
        "label_independent": True,
        "provenance_required": True,
        "status": status or relation_status(audit),
        "audit_statistics": {
            "source_row_count": audit["source_row_count"],
            "non_null_relationship_count": audit["non_null_relationship_count"],
            "resolved_target_count": audit["resolved_target_count"],
            "unresolved_target_count": audit["unresolved_target_count"],
            "unique_target_count": audit["unique_target_count"],
            "resolution_rate_percent_of_populated": audit["resolution_rate_percent_of_populated"],
            "target_in_degree_all_domain": audit["target_in_degree_all_domain"],
        },
    }
    if constraints:
        entry["constraints"] = constraints
    return entry


def build_relation_registry(
    records_by_type: dict[str, list[dict[str, Any]]],
    base_internal: dict[str, dict[str, Any]],
    employee_internal: dict[str, dict[str, Any]],
    employee_audit: dict[str, Any],
    gl_internal: dict[str, dict[str, Any]],
    gl_mapping_by_target: dict[str, list[str]],
    audit_event_internal: dict[str, dict[str, Any]],
    audit_mapping_by_target: dict[str, list[str]],
    payment_bank_audit: dict[str, Any],
) -> dict[str, Any]:
    entries = []
    basic_specs = [
        ("LINE_OF_PO", "PO_LINE_TO_PURCHASE_ORDER", ["po_id"], ["po_id"], "PO_LINE", "TIER_A_EXACT", "many PO lines to one purchase order", True, True, "low transactional-key risk"),
        ("INVOICE_REFERENCES_PO", "INVOICE_TO_PURCHASE_ORDER", ["po_id"], ["po_id"], "INVOICE", "TIER_A_EXACT", "many invoices may reference one purchase order", True, True, "moderate reverse fan-out; motif constrained"),
        ("INVOICE_LINE_REFERENCES_PO_LINE", "INVOICE_LINE_TO_PO_LINE", ["po_line_id"], ["po_line_id"], "INVOICE_LINE", "TIER_A_EXACT", "many invoice lines may reference one PO line", True, True, "low transactional-key risk"),
        ("LINE_OF_INVOICE", "INVOICE_LINE_TO_INVOICE", ["invoice_id"], ["invoice_id"], "INVOICE_LINE", "TIER_A_EXACT", "many invoice lines to one invoice", True, True, "low transactional-key risk"),
        ("APPROVAL_FOR_INVOICE", "APPROVAL_EVENT_TO_INVOICE", ["invoice_id"], ["invoice_id"], "APPROVAL_EVENT", "TIER_A_EXACT", "many approval events to one invoice", True, True, "event fan-out; motif constrained"),
        ("ALLOCATION_OF_PAYMENT", "PAYMENT_ALLOCATION_TO_PAYMENT", ["payment_id"], ["payment_id"], "PAYMENT_ALLOCATION", "TIER_A_EXACT", "many allocations to one payment", True, True, "low transactional-key risk"),
        ("ALLOCATION_TO_INVOICE", "PAYMENT_ALLOCATION_TO_INVOICE", ["invoice_id"], ["invoice_id"], "PAYMENT_ALLOCATION", "TIER_A_EXACT", "many allocations may reference one invoice", True, True, "low transactional-key risk"),
        ("PAYMENT_ALLOCATED_TO_INVOICE", "PAYMENT_TO_INVOICE_VIA_ALLOCATION", ["payment_id"], ["invoice_id"], "PAYMENT_ALLOCATION", "TIER_A_EXPLICIT_PROVENANCE", "potentially many-to-many via explicit allocations", True, True, "transactional relation; allocation provenance mandatory"),
        ("VENDOR_CHANGE_FOR_VENDOR", "VENDOR_CHANGE_TO_VENDOR", ["vendor_id"], ["vendor_id"], "VENDOR_CHANGE", "TIER_A_EXACT", "many changes to one vendor", False, False, "high-degree vendor hub; attach only as exact context"),
        ("PO_FOR_VENDOR", "PURCHASE_ORDER_TO_VENDOR", ["vendor_id"], ["vendor_id"], "PURCHASE_ORDER", "TIER_A_EXACT", "many purchase orders to one vendor", False, False, "high-degree vendor hub; no neighborhood expansion"),
        ("INVOICE_FOR_VENDOR", "INVOICE_TO_VENDOR", ["vendor_id"], ["vendor_id"], "INVOICE", "TIER_A_EXACT", "many invoices to one vendor", False, False, "high-degree vendor hub; no neighborhood expansion"),
        ("PAYMENT_FOR_VENDOR", "PAYMENT_TO_VENDOR", ["vendor_id"], ["vendor_id"], "PAYMENT", "TIER_A_EXACT", "many payments to one vendor", False, False, "high-degree vendor hub; no neighborhood expansion"),
    ]
    for spec in basic_specs:
        entries.append(registry_entry(spec[0], base_internal[spec[1]], *spec[2:]))

    employee_class_by_key = {
        item["relation_key"]: item["proposed_relation_classification"] for item in employee_audit["source_fields"]
    }
    for key, audit in sorted(employee_internal.items()):
        classification = employee_class_by_key[key]
        status = "READY_FOR_FREEZE" if classification == "APPROVED_TIER_A" else "CONDITIONAL"
        entries.append(registry_entry(
            key,
            audit,
            [audit["source_field"]],
            ["employee_id"],
            audit["source_node_type"],
            "TIER_A_EXACT_MATCHED_SUBSET",
            "many operational records may reference one employee",
            False,
            False,
            "employee organizational hub; unmatched system actors retained as context",
            status=status,
            constraints={"employee_audit_classification": classification, "unmatched_values_create_edge": False},
        ))

    grouped_gl: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for audit in gl_internal.values():
        grouped_gl[audit["target_node_type"]].append(audit)
    for target_type, audits in sorted(grouped_gl.items()):
        combined_pairs = [pair for audit in audits for pair in audit["_pairs"]]
        combined = relation_from_provenance_pairs(
            f"GL_ENTRY_TO_{target_type}",
            "GL_ENTRY",
            target_type,
            list({pair[0]["record_id"]: pair[0] for pair in combined_pairs}.values()),
            records_by_type[target_type],
            combined_pairs,
        )
        entries.append(registry_entry(
            f"GL_SOURCE_{target_type}",
            combined,
            ["transaction_type", "source_transaction_id"],
            list(PRIMARY_KEYS[combined_pairs[0][1]["source_table"]]),
            "GL_ENTRY",
            "TIER_A_TYPED_EXACT",
            "many GL lines may reference one source transaction",
            True,
            True,
            "bounded accounting-line fan-out; motif and 40-record budget constrained",
            constraints={"permitted_transaction_types": gl_mapping_by_target[target_type]},
        ))

    grouped_audit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for audit in audit_event_internal.values():
        grouped_audit[audit["target_node_type"]].append(audit)
    for target_type, audits in sorted(grouped_audit.items()):
        combined_pairs = [pair for audit in audits for pair in audit["_pairs"]]
        combined = relation_from_provenance_pairs(
            f"AUDIT_EVENT_TO_{target_type}",
            "AUDIT_EVENT",
            target_type,
            list({pair[0]["record_id"]: pair[0] for pair in combined_pairs}.values()),
            records_by_type[target_type],
            combined_pairs,
        )
        traversable = target_type != "VENDOR"
        entries.append(registry_entry(
            f"AUDIT_EVENT_FOR_{target_type}",
            combined,
            ["entity_type", "entity_id"],
            list(PRIMARY_KEYS[combined_pairs[0][1]["source_table"]]),
            "AUDIT_EVENT",
            "TIER_A_TYPED_EXACT",
            "many audit events may reference one operational node",
            traversable,
            traversable,
            "vendor hub restricted" if target_type == "VENDOR" else "bounded event fan-out; motif constrained",
            constraints={"permitted_entity_types": audit_mapping_by_target[target_type]},
        ))

    exact_ref = next(item for item in payment_bank_audit["candidate_predicates"] if item["predicate_name"] == "REFERENCE_ONLY")
    bank_candidate_audit = {
        "source_node_type": "PAYMENT",
        "target_node_type": "BANK_TRANSACTION",
        "source_row_count": payment_bank_audit["payment_count"],
        "non_null_relationship_count": payment_bank_audit["exact_reference_behavior"]["non_null_payment_reference_count"],
        "resolved_target_count": exact_ref["matched_payment_count"] - exact_ref["ambiguous_payment_count"],
        "unresolved_target_count": exact_ref["unmatched_payment_count"],
        "unique_target_count": exact_ref["matched_bank_transaction_count"],
        "resolution_rate_percent_of_populated": pct(exact_ref["matched_payment_count"], payment_bank_audit["exact_reference_behavior"]["non_null_payment_reference_count"]),
        "cardinality_observed": "candidate collisions retained; see payment_bank_relation_audit.json",
        "target_in_degree_all_domain": exact_ref["bank_transaction_candidate_degree"],
    }
    entries.append(registry_entry(
        "PAYMENT_CANDIDATE_BANK_TRANSACTION",
        bank_candidate_audit,
        ["reference_number", "payment_currency", "bank_account_id", "payment_amount", "payment_date"],
        ["payment_reference", "currency", "bank_account_id", "amount", "direction", "posted_date"],
        "PAYMENT+BANK_TRANSACTION",
        "TIER_B_CANDIDATE",
        "candidate relationship; cardinality not frozen",
        False,
        False,
        "collision and shared-reference risk; account identifier domains may differ",
        status="UNRESOLVED",
        constraints={
            "temporal_window": "UNRESOLVED — REQUIRES POLICY FREEZE",
            "multiple_candidates": "preserve ambiguity; create no edge",
            "embeddings_permitted": False,
        },
    ))

    return {
        "registry_version": "graph_relation_registry_v1_draft",
        "decision_cutoff": DECISION_CUTOFF,
        "source_corpus_text_manifest_sha256": EXPECTED_TEXT_MANIFEST_SHA256,
        "relationships": entries,
        "gl_transaction_type_mapping": {
            target: types for target, types in sorted(gl_mapping_by_target.items())
        },
        "audit_event_entity_type_mapping": {
            target: types for target, types in sorted(audit_mapping_by_target.items())
        },
        "excluded_or_unresolved_designs": [
            {
                "design": "GL_JOURNAL node or AUDIT_EVENT→GL_JOURNAL edge",
                "status": "REJECTED",
                "reason": "No journal-header source record exists. journal_id remains a GL_ENTRY grouping/context attribute.",
            },
            {
                "design": "AUDIT_EVENT gl_journal entity to GL_ENTRY traversal",
                "status": "UNRESOLVED",
                "reason": "entity_id matches a noncanonical journal_id grouping attribute and fans out to multiple GL_ENTRY records; no type-consistent canonical node match.",
            },
            {
                "design": "attribute bridge nodes for bank_account_id, gl_account, department, cost_center, currency, source_system, dates, or statuses",
                "status": "REJECTED",
                "reason": "Context/filtering attributes are not source-backed node types and create hub risk.",
            },
        ],
        "ready_for_freeze_definition": "Only deterministic exact/type-consistent relations with zero unresolved or ambiguous populated references; conditional/unresolved relations remain excluded from traversal.",
    }


def build_path_motifs(registry: dict[str, Any]) -> dict[str, Any]:
    ready_types = {item["relation_type"] for item in registry["relationships"] if item["status"] == "READY_FOR_FREEZE"}
    motifs = [
        ("PO_WITH_INVOICES", ["PURCHASE_ORDER", "INVOICE"], ["INVOICE_REFERENCES_PO:reverse"], False, 1),
        ("PO_WITH_LINES", ["PURCHASE_ORDER", "PO_LINE"], ["LINE_OF_PO:reverse"], False, 1),
        ("PO_INVOICE_LINES", ["PURCHASE_ORDER", "INVOICE", "INVOICE_LINE"], ["INVOICE_REFERENCES_PO:reverse", "LINE_OF_INVOICE:reverse"], False, 2),
        ("INVOICE_PAYMENTS", ["INVOICE", "PAYMENT"], ["PAYMENT_ALLOCATED_TO_INVOICE:reverse"], False, 1),
        ("INVOICE_APPROVALS", ["INVOICE", "APPROVAL_EVENT"], ["APPROVAL_FOR_INVOICE:reverse"], False, 1),
        ("INVOICE_AUDIT_EVENTS", ["INVOICE", "AUDIT_EVENT"], ["AUDIT_EVENT_FOR_INVOICE:reverse"], False, 1),
        ("PAYMENT_GL_ENTRIES", ["PAYMENT", "GL_ENTRY"], ["GL_SOURCE_PAYMENT:reverse"], False, 1),
        ("GL_ENTRY_SOURCE_TRANSACTION", ["GL_ENTRY"], ["GL_SOURCE_{INVOICE|PAYMENT|BANK_TRANSACTION}:forward"], False, 1),
        ("INVOICE_PAYMENT_BANK", ["INVOICE", "PAYMENT", "BANK_TRANSACTION"], ["PAYMENT_ALLOCATED_TO_INVOICE:reverse", "PAYMENT_CANDIDATE_BANK_TRANSACTION:forward"], True, 2),
        ("GL_PAYMENT_BANK", ["GL_ENTRY", "PAYMENT", "BANK_TRANSACTION"], ["GL_SOURCE_PAYMENT:forward", "PAYMENT_CANDIDATE_BANK_TRANSACTION:forward"], True, 2),
    ]
    output = []
    for name, anchors, edges, tier_b, priority in motifs:
        unresolved = any("PAYMENT_CANDIDATE_BANK_TRANSACTION" in edge for edge in edges)
        output.append({
            "motif_name": name,
            "permitted_anchor_types": anchors,
            "edge_sequence": edges,
            "maximum_multiplicity": {
                "maximum_raw_source_records": 40,
                "per_step_rule": "include exact neighbors in ascending canonical record_id order until the remaining global 40-record budget is exhausted",
                "status": "DRAFT_POLICY_REQUIRES_HUMAN_FREEZE",
            },
            "candidate_tier_b_edges_allowed": tier_b,
            "traversal_priority": priority,
            "hub_restrictions": [
                "no Vendor reverse-neighborhood expansion",
                "no Employee reverse-neighborhood expansion",
                "no traversal through attribute values",
            ],
            "temporal_requirements": "Every node and provenance record must be cutoff-eligible; derived edge availability is the latest participant availability.",
            "failure_class_specific": False,
            "status": "UNRESOLVED" if unresolved else "READY_FOR_FREEZE",
            "unresolved_reason": "PAYMENT↔BANK_TRANSACTION Tier B predicate/window is not frozen" if unresolved else None,
        })
    return {
        "motif_registry_version": "graph_path_motifs_v1_draft",
        "unrestricted_bfs_permitted": False,
        "global_raw_source_record_cap": 40,
        "motifs": output,
        "relation_types_ready_at_generation": sorted(ready_types),
    }


def build_ranking_policy() -> dict[str, Any]:
    return {
        "policy_version": "graph_ranking_policy_v1_draft",
        "label_independent": True,
        "trained_reranker": False,
        "held_out_optimization": False,
        "priority_order": [
            {"priority": 1, "class": "exact anchor"},
            {"priority": 2, "class": "direct Tier A relationships"},
            {"priority": 3, "class": "complete Tier A multi-hop paths"},
            {"priority": 4, "class": "deterministic relational joins"},
            {"priority": 5, "class": "Tier B corroborated candidates", "condition": "only after the candidate predicate is separately frozen"},
            {"priority": 6, "class": "audit/event context"},
            {"priority": 7, "class": "targeted semantic fallback", "condition": "unresolved gaps only; never creates graph edges"},
        ],
        "deterministic_tie_breaking": [
            "lower priority number",
            "fewer graph hops",
            "relation registry order",
            "ascending canonical record_id",
            "for semantic fallback only: descending exact float32 score then ascending record_id",
        ],
        "context_budget": {
            "maximum_raw_source_records": 40,
            "token_budget_cap": "UNRESOLVED — REQUIRES POLICY FREEZE",
            "constraint": "must remain comparable with Standard RAG and must not be selected using held-out accuracy",
            "truncation_policy": "no silent record truncation or record-content rewriting",
        },
        "hub_policy": "Vendor/Employee reverse expansion is restricted; attribute bridges are prohibited.",
    }


def report_markdown(
    verification: dict[str, Any],
    node_registry: dict[str, Any],
    tier_a: dict[str, Any],
    gl_audit: dict[str, Any],
    audit_entity: dict[str, Any],
    employee: dict[str, Any],
    payment_bank: dict[str, Any],
    temporal: dict[str, Any],
    leakage: dict[str, Any],
    hub: dict[str, Any],
    relation_registry: dict[str, Any],
    motifs: dict[str, Any],
    ranking: dict[str, Any],
    blockers: list[str],
) -> str:
    node_rows = [
        [item["node_type"], ", ".join(item["canonical_primary_key"]), item["temporal_eligibility_field"], item["record_count"]]
        for item in node_registry["node_types"]
    ]
    relation_rows = []
    for item in tier_a["relationships"]:
        deg = item["target_in_degree_all_domain"]
        risk = "restricted" if item["target_node_type"] in {"VENDOR", "EMPLOYEE"} else "transactional"
        recommendation = "restricted traversal" if risk == "restricted" else "READY_FOR_FREEZE" if not item["unresolved_target_count"] else "UNRESOLVED"
        source_field = item.get("source_field", "explicit PAYMENT_ALLOCATION provenance")
        relation_rows.append([
            item["relation_key"], source_field, f"{item['resolution_rate_percent_of_populated']:.4f}%",
            item["cardinality_observed"], item["unresolved_target_count"],
            f"max={deg['maximum_degree']}; p95={deg['p95_degree_nearest_rank']}", recommendation,
        ])
    gl_rows = [
        [item["transaction_type"], item["count"], item["non_null_source_transaction_id_count"], item["proposed_target_node_type"], item["unresolved_value_count"], item["proposed_status"]]
        for item in gl_audit["transaction_types"]
    ]
    audit_rows = [
        [item["entity_type"], item["count"], item["non_null_entity_id_count"], item["expected_type_consistent_target"], item["unresolved_count"], item["ambiguous_count"], item["proposed_status"]]
        for item in audit_entity["entity_types"]
    ]
    employee_rows = [
        [item["source_node_type"] + "." + item["source_field"], item["total_populated_values"], item["exact_employee_matches"], item["unmatched_values"], f"{item['percentage_resolved']:.4f}%", item["proposed_relation_classification"]]
        for item in employee["source_fields"]
    ]
    payment_predicate_rows = [
        [item["predicate_name"], item["candidate_pair_count"], item["matched_payment_count"], item["matched_bank_transaction_count"], item["ambiguous_payment_count"], item["ambiguous_bank_transaction_count"]]
        for item in payment_bank["candidate_predicates"]
    ]
    temporal_rows = [
        [item["node_type"], item["record_count"], item["eligible_count"], item["after_cutoff_count"], item["missing_or_unparseable_availability_count"], item["metadata_available_at_mismatch_count"]]
        for item in temporal["node_eligibility"]
    ]
    registry_rows = [
        [item["relation_type"], item["source_node_type"], item["target_node_type"], item["confidence_tier"], item["traversable"], item["status"]]
        for item in relation_registry["relationships"]
    ]
    motif_rows = [
        [item["motif_name"], " → ".join(item["edge_sequence"]), item["candidate_tier_b_edges_allowed"], item["traversal_priority"], item["status"]]
        for item in motifs["motifs"]
    ]
    exact = payment_bank["exact_reference_behavior"]
    unresolved = [
        "PAYMENT↔BANK_TRANSACTION: exact bank-account namespaces do not receive any inferred crosswalk; a maximum temporal window is UNRESOLVED — REQUIRES POLICY FREEZE. The edge remains excluded from traversal.",
        "AUDIT_EVENT entity_type=gl_journal: entity_id addresses journal_id grouping values, not canonical GL_ENTRY IDs. No GL_JOURNAL node is allowed; traversal remains unresolved/excluded.",
        "APPROVAL_EVENT.approver_id and AUDIT_EVENT.actor_id include non-Employee system/shared-role actors. Exact Employee matches can be conditional edges; unmatched actor strings remain context.",
        "The exact GraphRAG token cap comparable with Standard RAG and per-motif multiplicity behavior require human policy freeze; the raw-source cap remains 40.",
        "Vendor and Employee reverse-expansion restrictions require explicit reviewer acceptance before implementation.",
    ]
    decision = "RECOMMEND BLOCK GRAPH RAG REGISTRY FREEZE" if blockers else "RECOMMEND 7/7 GO FOR GRAPH RAG REGISTRY FREEZE"
    blocker_text = "\n".join(f"- {item}" for item in blockers) if blockers else "No blocking condition was found for freezing the deterministic READY_FOR_FREEZE core. CONDITIONAL and UNRESOLVED relations must remain excluded from traversal."
    return f"""# GraphRAG Pre-Freeze Review

This is a label-independent schema/relation audit only. No graph, graph index, traversal engine, inference, new embedding, query builder, prompt, prediction, or production behavior was created.

## A. Artifact verification

- Authoritative index SHA-256: `{verification['index_manifest_sha256']['actual']}` (`PASS`)
- Vector matrix: `{verification['vector_count']['matrix']}` × `{verification['dimensions']['matrix']}`, dtype `{verification['matrix_dtype']}` (`PASS`)
- Logical text-manifest SHA-256: `{verification['logical_text_manifest_sha256']['actual']}` (`PASS`)
- Corpus count: `{verification['corpus_count']['actual']}` (`PASS`)
- Corpus hashes: documents `{verification['corpus_file_sha256']['documents.jsonl']['actual']}`, metadata `{verification['corpus_file_sha256']['metadata.jsonl']['actual']}`, record IDs `{verification['corpus_file_sha256']['record_ids.txt']['actual']}`
- Per-document text-hash, ordinal, three-file alignment, metadata parity, and operational-schema mismatch counts are all zero.

{md_table(['Record type', 'Canonical key', 'Temporal eligibility', 'Count'], node_rows)}

## B. Node registry

All 14 expected operational record types are present; their counts total `{node_registry['total_record_count']}`. No synthetic node type was introduced. `GL_JOURNAL` is explicitly excluded because no journal-header source record exists; `journal_id` remains a `GL_ENTRY` grouping/context attribute.

Canonical integrity: `{node_registry['integrity']['duplicate_record_id_count']}` duplicate record IDs, `{node_registry['integrity']['duplicate_canonical_id_count']}` duplicate canonical IDs, `{node_registry['integrity']['malformed_record_id_count']}` malformed IDs, `{node_registry['integrity']['missing_primary_key_count']}` missing primary keys, and `{node_registry['integrity']['orphaned_composite_key_component_count']}` orphaned composite-key components.

The complete field-use registry is in `graph_node_registry_v1_draft.json`.

## C. Tier A relations

Degree values below are target in-degrees over the complete target domain; p95 uses deterministic nearest-rank calculation.

{md_table(['Relationship', 'Evidence field', 'Resolution', 'Observed cardinality', 'Orphans', 'Degree / hub risk', 'Recommendation'], relation_rows)}

`PAYMENT → INVOICE` is exposed only through explicit, cutoff-eligible `PAYMENT_ALLOCATION` provenance. Vendor relations are exact but not automatically traversable.

## D. GL transaction-type audit

{md_table(['transaction_type', 'Rows', 'Non-null source ID', 'Deterministic target', 'Unresolved', 'Status'], gl_rows)}

All mapping decisions use exact canonical IDs and type agreement. No nearest-ID or semantic matching was used. Full prefix distributions and all-node-type match matrices are in `gl_transaction_type_audit.json`.

## E. Audit-event entity-type audit

{md_table(['entity_type', 'Rows', 'Non-null ID', 'Canonical target', 'Unresolved', 'Ambiguous', 'Status'], audit_rows)}

`gl_journal` is intentionally unresolved at the canonical-node layer. Exact `journal_id` grouping matches are reported only as context; they do not authorize a `GL_JOURNAL` node or traversal edge.

## F. Employee reference audit

{md_table(['Source field', 'Populated', 'Employee matches', 'Unmatched', 'Resolved', 'Classification'], employee_rows)}

Unmatched system/service/shared-role actors are preserved as operational context. No synthetic Employee was created and no unmatched actor was discarded.

## G. Payment-bank candidate audit

Exact-reference behavior: `{exact['non_null_payment_reference_count']}` populated payment references, `{exact['non_null_bank_payment_reference_count']}` populated bank payment references, `{exact['distinct_exact_reference_match_count']}` distinct matching references, and `{exact['exact_reference_candidate_pair_count']}` candidate pairs. There are `{exact['unmatched_payment_count']}` unmatched payments and `{exact['unmatched_bank_transaction_count']}` unmatched bank transactions at the reference-only stage.

{md_table(['Candidate predicate', 'Pairs', 'Payments matched', 'Bank rows matched', 'Ambiguous payments', 'Ambiguous bank rows'], payment_predicate_rows)}

No embedding resolution or collision winner selection was performed. The maximum temporal window is **UNRESOLVED — REQUIRES POLICY FREEZE**; observed date lags are descriptive only.

## H. Temporal integrity audit

{md_table(['Node type', 'Rows', 'Eligible', 'After cutoff', 'Missing availability', 'Metadata mismatch'], temporal_rows)}

Every proposed edge is separately checked under `eligible(source) AND eligible(target) AND eligible(provenance)`. A derived edge becomes available no earlier than the latest participating evidence. `due_date`, `expected_delivery_date`, and bank `transaction_date` were not substituted for the frozen availability fields.

## I. Leakage audit

Status: **{leakage['status']}**. The audit scanned `{leakage['scan']['json_lines_scanned']}` JSONL records, structured key paths, all serialized field headers, source artifact names, and practical semantic variants. It found `{leakage['prohibited_key_or_header_hit_count']}` prohibited key/header hits and `{leakage['prohibited_content_hit_count']}` prohibited content hits. No prohibited ground-truth file was opened to construct or run the scan.

## J. Hub-risk audit

Vendor and Employee nodes are retained but classified for restricted traversal: exact anchoring/direct attachment is allowed, while unconstrained reverse-neighborhood expansion is prohibited. `bank_account_id`, `gl_account`, `department`, `cost_center`, `currency`, `source_system`, dates, statuses, and `journal_id` remain context/filtering attributes and cannot become bridge nodes. Exact observed fan-out statistics are in `graph_hub_risk_audit.json`.

## K. Draft relation registry

{md_table(['Relation', 'Source', 'Target', 'Tier', 'Traversable', 'Status'], registry_rows)}

Only `READY_FOR_FREEZE` relations are recommended for the frozen core. `CONDITIONAL`, `UNRESOLVED`, and `REJECTED` designs remain non-traversable until a separately approved policy change.

## L. Proposed path motifs

{md_table(['Motif', 'Edge sequence', 'Tier B allowed', 'Priority', 'Status'], motif_rows)}

Unrestricted BFS is prohibited. Every motif is label-independent, cutoff-gated, provenance-preserving, hub-restricted, and subject to the existing maximum of 40 raw source records.

### Deterministic ranking policy draft

The proposed order is: exact anchor; direct Tier A; complete Tier A multi-hop paths; deterministic joins; frozen Tier B corroborated candidates; audit/event context; then targeted semantic fallback only for unresolved gaps. Ties resolve by tier, hop count, registry order, and ascending canonical `record_id`. No reranker is trained and no weight is optimized on held-out labels. The exact token cap remains a human freeze item.

## M. Unresolved questions

{chr(10).join(f'- {item}' for item in unresolved)}

## N. Recommended freeze decision

Recommended scope: freeze only the deterministic `READY_FOR_FREEZE` node/relation/motif core. Keep every conditional or unresolved item explicitly excluded from traversal, especially payment-bank candidates and `gl_journal` grouping references. This recommendation does not authorize GraphRAG implementation.

{blocker_text}

{decision}
"""


def main() -> int:
    verification, records_by_type, leakage = load_and_verify()
    if verification["status"] != "PASS":
        # Fail closed. A minimal blocked record is the only generated audit output.
        blocked = {
            "status": "BLOCKED",
            "verification": verification,
            "leakage": leakage,
            "statement": "No relation/schema review artifacts were generated because the mandatory gate failed.",
        }
        write_json(OUT_DIR / "BLOCKED_PRE_FREEZE_GATE.json", blocked)
        return 2

    canonical_domains, field_domains = build_domains(records_by_type)
    node_registry, node_integrity = build_node_registry(records_by_type, canonical_domains, field_domains)
    temporal = establish_temporal_eligibility(records_by_type, field_domains)
    tier_a_list, base_internal = build_base_relation_audits(records_by_type, field_domains)
    employee, employee_internal = build_employee_audit(records_by_type, field_domains)
    gl_audit, gl_internal, gl_mapping = build_gl_audit(records_by_type, canonical_domains, field_domains)
    audit_entity, audit_event_internal, audit_mapping = build_audit_event_entity_audit(records_by_type, canonical_domains, field_domains)
    payment_bank, payment_candidate_sets = build_payment_bank_audit(records_by_type)

    all_internal = {**base_internal, **employee_internal, **gl_internal, **audit_event_internal}
    temporal["edge_eligibility"] = [edge_temporal_audit(all_internal[key]) for key in sorted(all_internal)]
    for predicate_name, pairs in payment_candidate_sets.items():
        provenance_pairs = [(payment, bank, bank) for payment, bank in pairs]
        candidate_relation = relation_from_provenance_pairs(
            f"PAYMENT_BANK_{predicate_name}",
            "PAYMENT",
            "BANK_TRANSACTION",
            records_by_type["PAYMENT"],
            records_by_type["BANK_TRANSACTION"],
            provenance_pairs,
        )
        temporal["edge_eligibility"].append(edge_temporal_audit(candidate_relation))

    hub = build_hub_audit(records_by_type, all_internal)
    relation_registry = build_relation_registry(
        records_by_type,
        base_internal,
        employee_internal,
        employee,
        gl_internal,
        gl_mapping,
        audit_event_internal,
        audit_mapping,
        payment_bank,
    )
    motifs = build_path_motifs(relation_registry)
    ranking = build_ranking_policy()

    tier_a = {
        "audit_version": "tier_a_relation_audit_v1",
        "degree_definition": "Target in-degree is calculated over the complete target-node domain, including zero-degree nodes; p95 is nearest-rank. Nonzero degree statistics are also retained.",
        "relationships": tier_a_list,
    }
    blockers: list[str] = []
    if any(node_integrity[key] for key in (
        "duplicate_record_id_count", "duplicate_canonical_id_count", "malformed_record_id_count",
        "missing_primary_key_count", "orphaned_composite_key_component_count",
    )):
        blockers.append("canonical node-ID integrity defects exist")
    expected_types = set(RECORD_TYPES.values())
    if set(records_by_type) != expected_types or sum(map(len, records_by_type.values())) != EXPECTED_DOCUMENT_COUNT:
        blockers.append("record-type set or total count differs from the frozen expectation")
    if any(item["after_cutoff_count"] or item["missing_or_unparseable_availability_count"] or item["metadata_available_at_mismatch_count"] for item in temporal["node_eligibility"]):
        blockers.append("node temporal eligibility defects exist")
    if any(item["effective_availability_after_cutoff_count"] or item["source_ineligible_count"] or item["target_ineligible_count"] or item["provenance_ineligible_count"] for item in temporal["edge_eligibility"]):
        blockers.append("edge temporal eligibility defects exist")
    if leakage["status"] != "PASS":
        blockers.append("prohibited benchmark information is present")

    verification["record_type_distribution"] = {
        record_type: len(records_by_type[record_type]) for record_type in sorted(records_by_type)
    }
    verification["recommended_freeze_blockers"] = blockers

    artifacts = {
        "artifact_verification.json": verification,
        "graph_node_registry_v1_draft.json": node_registry,
        "tier_a_relation_audit.json": tier_a,
        "gl_transaction_type_audit.json": gl_audit,
        "audit_event_entity_type_audit.json": audit_entity,
        "employee_reference_audit.json": employee,
        "payment_bank_relation_audit.json": payment_bank,
        "graph_temporal_integrity_audit.json": temporal,
        "graph_leakage_audit.json": leakage,
        "graph_hub_risk_audit.json": hub,
        "graph_relation_registry_v1_draft.json": relation_registry,
        "graph_path_motifs_v1_draft.json": motifs,
        "graph_ranking_policy_v1_draft.json": ranking,
    }
    for name, value in artifacts.items():
        write_json(OUT_DIR / name, value)
    report = report_markdown(
        verification, node_registry, tier_a, gl_audit, audit_entity, employee,
        payment_bank, temporal, leakage, hub, relation_registry, motifs, ranking, blockers,
    )
    (OUT_DIR / "GRAPH_RAG_PRE_FREEZE_REVIEW.md").write_text(report, encoding="utf-8")

    generated_paths = sorted(
        [path for path in OUT_DIR.iterdir() if path.is_file() and path.name != "generated_artifact_hashes.json"],
        key=lambda path: path.name,
    )
    hash_inventory = {
        "inventory_version": "generated_artifact_hashes_v1",
        "algorithm": "SHA-256",
        "self_hash_excluded_to_avoid_circularity": True,
        "artifacts": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in generated_paths
        ],
    }
    write_json(OUT_DIR / "generated_artifact_hashes.json", hash_inventory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
