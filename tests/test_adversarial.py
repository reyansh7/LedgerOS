"""Adversarial Lab & Security Boundary Regression Suite.

Verifies that malicious, malformed, or unauthorized attempts are deterministically
intercepted and blocked across the entire LedgerOS control plane.
"""

import hmac
import hashlib
import json
import uuid
import pytest
from decimal import Decimal

from core.adapters.base import CapabilityNotSupportedError
from core.adapters.razorpay_adapter import RazorpayAdapter
from core.governance.rbac import RBACManager, UserRole, Permission
from core.policies.engine import policy_engine
from core.audit.logger import audit_logger
from integrations.razorpay.webhook_handler import process_webhook_event, verify_webhook_signature


def test_adversarial_invalid_webhook_signature():
    """Attack 1: Attacker sends fabricated payment notification with invalid HMAC signature."""
    raw_body = b'{"event":"payment.captured","payload":{"payment":{"entity":{"amount":9999900}}}}'
    tampered_sig = "0000000000000000deadbeefcafebabedeadbeef000000000000000000000000"

    is_valid = verify_webhook_signature(raw_body, tampered_sig, secret="production_secret_key_123")
    assert is_valid is False

    res = process_webhook_event(
        event_id=f"evt_fake_{uuid.uuid4().hex[:8]}",
        raw_body=raw_body,
        signature=tampered_sig,
    )
    assert res["status"] == "rejected"
    assert "Invalid HMAC signature" in res["reason"]


def test_adversarial_unsupported_capability_probe():
    """Attack 2: Agent attempts to query General Ledger entries from Razorpay Payment Gateway."""
    razor_adapter = RazorpayAdapter()
    with pytest.raises(CapabilityNotSupportedError) as exc:
        razor_adapter.get_gl_entries()
    assert exc.value.capability.value == "general_ledger"
    assert "NOT supported by connector" in str(exc.value)


def test_adversarial_unauthorized_role_approval():
    """Attack 3: Finance Analyst attempts to bypass separation of duties and approve financial recovery."""
    with pytest.raises(PermissionError) as exc:
        RBACManager.require_permission(UserRole.FINANCE_ANALYST, Permission.APPROVE_ACTION)
    assert "not authorized to perform action" in str(exc.value)


def test_adversarial_policy_exposure_bypass():
    """Attack 4: LLM proposes an unapproved ₹50,000 refund attempting auto-execution."""
    res = policy_engine.evaluate("SIMULATE_REFUND", Decimal("50000.0"))
    # MUST NOT be ALLOW
    assert res.verdict != "ALLOW"
    assert res.verdict == "REQUIRE_APPROVAL"
    assert res.policy_code == "FIN-POL-REF-02"


def test_adversarial_ground_truth_isolation():
    """Attack 5: Verifies that hidden ground truth cannot be loaded through operational database models."""
    from core.models.operational import Invoice, Payment, GLEntry
    # Operational tables must have NO reference to evaluator columns
    assert not hasattr(Invoice, "rca_ground_truth")
    assert not hasattr(Payment, "hidden_causal_edges")
    assert not hasattr(GLEntry, "mutation_metadata")
