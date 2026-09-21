"""Tests for Decision Receipt Generation, Policy Versioning, and Autonomy Levels."""

from decimal import Decimal
from sqlalchemy import select
from core.database import SyncSessionLocal
from core.models.reconciliation import ExceptionCase
from core.governance.receipts import decision_receipt_service
from core.policies.engine import policy_engine


def test_decision_receipt_for_persisted_case():
    # 1. Fetch an existing case
    with SyncSessionLocal() as session:
        case = session.execute(select(ExceptionCase)).scalars().first()
        assert case is not None, "Test requires at least one exception case in DB."
        case_id = case.case_id

    # 2. Generate structured decision receipt
    receipt = decision_receipt_service.generate_receipt_for_case(case_id)
    assert receipt is not None
    assert receipt.case_id == case_id
    assert receipt.receipt_id == f"RCP-{case_id.replace('EXC_', '')}"
    assert "FIN-POL-" in receipt.policy_version
    assert receipt.autonomy_level in [
        "L0_DETECT",
        "L1_INVESTIGATE",
        "L2_RECOMMEND",
        "L3_EXECUTE_WITH_APPROVAL",
        "L4_AUTONOMOUS_EXECUTION",
    ]
    assert receipt.verification_status in ["PASSED", "PENDING", "FAILED"]

    receipt_dict = receipt.to_dict()
    assert "audit_id" in receipt_dict
    assert "hash_digest" in receipt_dict
    assert "evidence_summary" in receipt_dict


def test_autonomy_level_and_policy_versioning():
    # 1. Auto-allow check (Refund <= 5000) -> L4_AUTONOMOUS_EXECUTION
    res1 = policy_engine.evaluate("SIMULATE_REFUND", Decimal("4500.0"))
    assert res1.verdict == "ALLOW"
    assert res1.autonomy_level == "L4_AUTONOMOUS_EXECUTION"
    assert res1.policy_version.startswith("FIN-POL-")

    # 2. Require approval check (Refund > 5000) -> L3_EXECUTE_WITH_APPROVAL
    res2 = policy_engine.evaluate("SIMULATE_REFUND", Decimal("7500.0"))
    assert res2.verdict == "REQUIRE_APPROVAL"
    assert res2.autonomy_level == "L3_EXECUTE_WITH_APPROVAL"

    # 3. High risk check (WRITE_OFF) -> L3_EXECUTE_WITH_APPROVAL
    res3 = policy_engine.evaluate("WRITE_OFF", Decimal("1000.0"))
    assert res3.verdict == "REQUIRE_APPROVAL"
    assert res3.autonomy_level == "L3_EXECUTE_WITH_APPROVAL"
