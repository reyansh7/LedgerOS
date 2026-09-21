"""State definition for LangGraph financial investigation workflows."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict


class Milestone(TypedDict):
    step: str
    status: str  # completed, in_progress, pending, failed
    detail: str
    timestamp: str


class InvestigationState(TypedDict):
    case_id: str
    failure_type: str
    primary_entity_type: str
    primary_entity_id: str
    amount_at_risk: float
    observed_symptom: str

    # Retrieval & Evidence
    retrieval_hop: int
    evidence_nodes: List[Dict[str, Any]]
    evidence_edges: List[Dict[str, Any]]
    evidence_ids: List[str]
    evidence_sufficient: bool

    # Reasoning & Hypotheses
    candidate_causes: List[str]
    root_cause: Optional[str]
    confidence_score: float
    explanation: Optional[str]

    # Action & Policy Gate
    proposed_action: Optional[Dict[str, Any]]
    policy_verdict: Optional[str]  # ALLOW, DENY, REQUIRE_APPROVAL
    policy_code: Optional[str]
    policy_reason: Optional[str]

    # Human-in-the-loop & Execution
    approval_id: Optional[str]
    is_paused_for_approval: bool
    human_verdict: Optional[str]  # APPROVED, REJECTED
    execution_result: Optional[Dict[str, Any]]
    verification_passed: bool
    audit_id: Optional[str]

    # Clean UI Activity Log (No raw CoT tokens exposed)
    activity_log: List[Milestone]
