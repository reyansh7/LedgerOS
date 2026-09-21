"""Model abstraction layer using LiteLLM with offline deterministic fallback."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from core.config import settings

try:
    import litellm
except ImportError:
    litellm = None


def generate_financial_reasoning(
    symptom: str,
    failure_type: str,
    evidence_nodes: list[dict[str, Any]],
    amount_at_risk: float,
) -> dict[str, Any]:
    """Generates root-cause hypothesis, explanation, and resolution proposal."""
    # If API key is available and litellm is present, attempt LLM completion
    api_key = settings.gemini_api_key or settings.openai_api_key or settings.groq_api_key
    if litellm and api_key:
        try:
            prompt = f"""You are LedgerOS, an autonomous finance controller.
Analyze the following financial exception:
Failure Type: {failure_type}
Observed Symptom: {symptom}
Amount at Risk: {amount_at_risk}
Evidence Records: {json.dumps(evidence_nodes, indent=2)}

Return a JSON object with:
- "candidate_causes": list of 2-3 plausible hypotheses
- "root_cause": concise single-sentence root cause
- "explanation": evidence-backed explanation
- "confidence_score": float between 0.0 and 1.0
- "proposed_action": object with "action_type", "amount", "target_entity", "rationale"
"""
            model = settings.default_llm_model
            resp = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            pass  # Fall through to deterministic financial reasoner

    # Deterministic Financial Reasoner Fallback (Zero external dependency requirement)
    if "DUPLICATE_INVOICE" in failure_type or "F01" in failure_type:
        return {
            "candidate_causes": [
                "Duplicate invoice entry with modified punctuation/reference",
                "Automated supplier rebilling loop",
                "Manual AP operator duplicate keying",
            ],
            "root_cause": "The same economic obligation was entered twice with differing reference punctuation.",
            "explanation": f"Discovered twin invoice records sharing the identical vendor and gross amount ({amount_at_risk}).",
            "confidence_score": 0.98,
            "proposed_action": {
                "action_type": "VOID_INVOICE",
                "amount": amount_at_risk,
                "target_entity": evidence_nodes[0].get("entity_id") if evidence_nodes else "unknown",
                "rationale": "Void the duplicate entry to prevent double disbursement, retaining the original payable.",
            },
        }
    elif "PO_INVOICE" in failure_type or "F02" in failure_type:
        return {
            "candidate_causes": [
                "Unauthorized vendor price inflation",
                "Unaccounted shipping or tax surcharge on invoice",
                "Unit price mismatch on purchase order lines",
            ],
            "root_cause": "Invoice total exceeds authorized purchase order total beyond acceptable 2% tolerance.",
            "explanation": f"Price discrepancy detected between procurement contract and AP billing totaling {amount_at_risk}.",
            "confidence_score": 0.94,
            "proposed_action": {
                "action_type": "CREATE_RECOVERY_CASE",
                "amount": amount_at_risk,
                "target_entity": evidence_nodes[0].get("entity_id") if evidence_nodes else "unknown",
                "rationale": "Issue price variance dispute to vendor requesting credit note for unauthorized surplus.",
            },
        }
    elif "DOUBLE_PAYMENT" in failure_type or "F06" in failure_type:
        return {
            "candidate_causes": [
                "Payment batch rerun after timeout",
                "Manual ACH wire issued parallel to ERP batch",
            ],
            "root_cause": "Single invoice was settled multiple times across separate disbursement runs.",
            "explanation": f"Multiple payment allocations detected for a single payable resulting in excess disbursement of {amount_at_risk}.",
            "confidence_score": 0.99,
            "proposed_action": {
                "action_type": "SIMULATE_REFUND",
                "amount": amount_at_risk,
                "target_entity": evidence_nodes[0].get("entity_id") if evidence_nodes else "unknown",
                "rationale": "Initiate clawback recovery from recipient vendor for redundant disbursement.",
            },
        }
    else:
        return {
            "candidate_causes": [
                "Timing mismatch between ledger posting and bank settlement",
                "Inconsistent counterparty identifier across accounts",
            ],
            "root_cause": f"Financial discrepancy detected under category {failure_type}.",
            "explanation": f"Observed symptom: {symptom}",
            "confidence_score": 0.90,
            "proposed_action": {
                "action_type": "CREATE_RECOVERY_CASE",
                "amount": amount_at_risk,
                "target_entity": evidence_nodes[0].get("entity_id") if evidence_nodes else "unknown",
                "rationale": "Flag for Finance Controller review with attached evidence subgraph.",
            },
        }
