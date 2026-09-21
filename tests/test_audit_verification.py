"""Tests for Cryptographic Audit Trail Chaining and Tamper Verification."""

import hashlib
import json
import pytest
from sqlalchemy import select, delete
from core.database import SyncSessionLocal
from core.models.governance import AuditTrailEvent
from core.audit.logger import audit_logger


def test_audit_chain_validity():
    # 1. Existing ledger should be cryptographically sound
    res0 = audit_logger.verify_chain()
    assert res0["valid"] is True

    # 2. Append new chained event
    e1 = audit_logger.log_event(
        agent_name="reconciliation_agent",
        action_type="MATCH_RECORD",
        case_id="EXC_TEST_01",
        input_payload={"stage": "5-stage matcher", "variance": 0.0},
        evidence_ids=["INV_01", "PO_01"],
        decision="ALLOW",
        policy_code="FIN-POL-GEN-01",
    )
    assert e1.audit_id is not None
    assert e1.hash_digest is not None

    # 3. Verify independent ledger integrity holds with newly appended block
    res1 = audit_logger.verify_chain()
    assert res1["valid"] is True
    assert res1["verified_blocks"] >= 1
    assert "Successfully verified SHA-256" in res1["message"]


def test_audit_chain_tamper_detection():
    # 1. Create a controlled event at the head of the ledger
    e = audit_logger.log_event(
        agent_name="tamper_test_agent",
        action_type="TEST_TAMPER_TARGET",
        case_id="EXC_TAMPER_01",
        input_payload={"amount": 5000},
        evidence_ids=["REC_T1"],
        decision="ALLOW",
        policy_code="FIN-POL-GEN-01",
    )

    try:
        # 2. Deliberately tamper with the database record
        with SyncSessionLocal() as session:
            row = session.execute(select(AuditTrailEvent).where(AuditTrailEvent.audit_id == e.audit_id)).scalar_one()
            # Mutate the payload without updating the cryptographic hash
            row.input_payload = json.dumps({"amount": 999999999})
            session.commit()

        # 3. Verify independent verification detects the cryptographic mismatch
        tamper_res = audit_logger.verify_chain()
        assert tamper_res["valid"] is False
        assert tamper_res["failed_at_audit_id"] == e.audit_id
        assert "Cryptographic digest mismatch" in tamper_res["reason"]

    finally:
        # 4. Clean up test event so persistent operational ledger stays unbroken
        with SyncSessionLocal() as session:
            session.execute(delete(AuditTrailEvent).where(AuditTrailEvent.audit_id == e.audit_id))
            session.commit()
