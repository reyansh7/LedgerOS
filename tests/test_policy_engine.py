"""Test deterministic policy engine boundaries and stopping rules."""

from decimal import Decimal
import pytest
from core.policies.engine import policy_engine


def test_policy_allow():
    res = policy_engine.evaluate(action_type="VOID_INVOICE", amount=2500.0)
    assert res.verdict == "ALLOW"
    assert "FIN-POL" in res.policy_code


def test_policy_require_approval_on_excess_amount():
    # Refund over 5000 requires human approval
    res = policy_engine.evaluate(action_type="SIMULATE_REFUND", amount=12000.0)
    assert res.verdict == "REQUIRE_APPROVAL"


def test_policy_deny_excess_exposure():
    # Refund over 100000 is rejected
    res = policy_engine.evaluate(action_type="SIMULATE_REFUND", amount=150000.0)
    assert res.verdict == "DENY"


def test_policy_high_risk_actions():
    res = policy_engine.evaluate(action_type="WRITE_OFF", amount=50.0)
    assert res.verdict == "REQUIRE_APPROVAL"
    assert "FIN-POL-RISK-01" in res.policy_code
