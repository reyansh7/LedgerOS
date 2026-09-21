"""Agent Guardrails & Operating Boundaries Specification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Guardrail:
    guardrail_id: str
    name: str
    description: str
    enforcement: str  # DETERMINISTIC_CODE, POLICY_ENGINE, CRYPTOGRAPHIC, SCHEMA_ISOLATION
    status: str       # ACTIVE, ENFORCED


ACTIVE_GUARDRAILS: list[Guardrail] = [
    Guardrail(
        guardrail_id="GR-01-PROVENANCE-EVIDENCE",
        name="Mandatory Relational Evidence",
        description="Agents cannot propose recovery actions without retrieving minimum 3-hop typed relational graph evidence.",
        enforcement="DETERMINISTIC_CODE",
        status="ACTIVE",
    ),
    Guardrail(
        guardrail_id="GR-02-POLICY-BOUNDARIES",
        name="Deterministic Policy Enforcement",
        description="LLMs cannot bypass exposure rules. Policy decisions are governed strictly by rules.yaml (FIN-POL-v2.0).",
        enforcement="POLICY_ENGINE",
        status="ACTIVE",
    ),
    Guardrail(
        guardrail_id="GR-03-HUMAN-APPROVAL-GATE",
        name="Human-in-the-Loop Sign-Off",
        description="Any transaction exceeding exposure limits (e.g. refunds > ₹5,000, voids > ₹25,000) pauses LangGraph for Controller approval.",
        enforcement="POLICY_ENGINE",
        status="ACTIVE",
    ),
    Guardrail(
        guardrail_id="GR-04-POST-ACTION-INVARIANT",
        name="Post-Action Invariant Verification",
        description="Every financial action must be validated against accounting invariants post-execution; failure triggers VERIFICATION_FAILED.",
        enforcement="DETERMINISTIC_CODE",
        status="ACTIVE",
    ),
    Guardrail(
        guardrail_id="GR-05-IMMUTABLE-AUDIT-CHAIN",
        name="Cryptographic SHA-256 Chaining",
        description="Every decision, milestone, and approval is cryptographically chained with independent tamper verification.",
        enforcement="CRYPTOGRAPHIC",
        status="ACTIVE",
    ),
    Guardrail(
        guardrail_id="GR-06-RAW-SQL-PROHIBITION",
        name="Prohibition of Arbitrary SQL",
        description="Agents interact strictly with domain-level tools (FinanceDataInterface). Direct LLM-to-SQL construction is prohibited.",
        enforcement="SCHEMA_ISOLATION",
        status="ACTIVE",
    ),
    Guardrail(
        guardrail_id="GR-07-GROUND-TRUTH-FIREWALL",
        name="Ground-Truth Isolation Firewall",
        description="FinRCA evaluator benchmark ground truth is strictly quarantined from agent context windows and tools.",
        enforcement="SCHEMA_ISOLATION",
        status="ACTIVE",
    ),
    Guardrail(
        guardrail_id="GR-08-IDEMPOTENT-WEBHOOKS",
        name="Webhook Replay & Idempotency Protection",
        description="Payment events are deduplicated by event ID and verified via HMAC SHA-256 signatures before mutation.",
        enforcement="CRYPTOGRAPHIC",
        status="ACTIVE",
    ),
]


def get_active_guardrails() -> list[dict[str, str]]:
    return [
        {
            "guardrail_id": g.guardrail_id,
            "name": g.name,
            "description": g.description,
            "enforcement": g.enforcement,
            "status": g.status,
        }
        for g in ACTIVE_GUARDRAILS
    ]
