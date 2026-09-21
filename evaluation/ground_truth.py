"""Strictly isolated Evaluator-Only Ground Truth repository.

CRITICAL FIREWALL RULE:
This module and its loaded ground truth data (rca_ground_truth.jsonl, causal_edges.csv,
failure_manifest.csv, mutation_log.jsonl) MUST NEVER BE EXPOSED TO AGENTS OR OPERATIONAL MODELS.
It is exclusively utilized by the evaluation framework to grade performance post-investigation.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import settings


@dataclass(frozen=True)
class GroundTruthCase:
    case_id: str
    failure_type: str
    difficulty: str
    reasoning_hops: int
    primary_entity_type: str
    primary_entity_id: str
    affected_entities: list[dict[str, str]]
    evidence_ids: list[str]
    evidence_required: list[str]
    root_cause: str
    root_cause_category: str
    expected_resolution: str
    split: str
    observed_symptom: str


class GroundTruthRepository:
    """Evaluator-only interface to FinRCA hidden ground truth."""

    def __init__(self, benchmark_dir: Path | str | None = None):
        self.benchmark_dir = Path(benchmark_dir or settings.finrca_data_dir)
        self._cases: dict[str, GroundTruthCase] = {}
        self._manifest: dict[str, dict[str, Any]] = {}
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return

        gt_file = self.benchmark_dir / "rca_ground_truth.jsonl"
        if not gt_file.exists():
            raise FileNotFoundError(f"Hidden ground truth file not found at: {gt_file}")

        with gt_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                case = GroundTruthCase(
                    case_id=row["case_id"],
                    failure_type=row["failure_type"],
                    difficulty=row.get("difficulty", "medium"),
                    reasoning_hops=row.get("reasoning_hops", 2),
                    primary_entity_type=row.get("primary_entity", {}).get("type", "unknown"),
                    primary_entity_id=row.get("primary_entity", {}).get("id", "unknown"),
                    affected_entities=row.get("affected_entities", []),
                    evidence_ids=row.get("evidence_ids", []),
                    evidence_required=row.get("evidence_required", []),
                    root_cause=row.get("root_cause", ""),
                    root_cause_category=row.get("root_cause_category", ""),
                    expected_resolution=row.get("expected_resolution", ""),
                    split=row.get("split", "train"),
                    observed_symptom=row.get("observed_symptom", ""),
                )
                self._cases[case.case_id] = case

        manifest_file = self.benchmark_dir / "failure_manifest.csv"
        if manifest_file.exists():
            with manifest_file.open("r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self._manifest[r["case_id"]] = r

        self._loaded = True

    def get_case(self, case_id: str) -> Optional[GroundTruthCase]:
        self.load()
        return self._cases.get(case_id)

    def all_cases(self, split: Optional[str] = None) -> list[GroundTruthCase]:
        self.load()
        if split:
            return [c for c in self._cases.values() if c.split == split]
        return list(self._cases.values())

    def total_cases_count(self) -> int:
        self.load()
        return len(self._cases)


# Singleton evaluator repository
evaluator_ground_truth = GroundTruthRepository()
