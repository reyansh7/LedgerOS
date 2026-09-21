"""Structured Decision Receipt Generator.

Generates formal, tamper-evident Decision Receipts for approved, autonomous, or denied
financial operations. Decision Receipts synthesize LangGraph investigation state,
retrieved evidence, deterministic policy evaluation, post-action verification, and
cryptographically chained audit hashes.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import SyncSessionLocal
from core.models.reconciliation import ExceptionCase
from core.models.governance import AuditTrailEvent, ApprovalRequest, AgentAction
from core.domain.models import DecisionReceipt
from core.policies.engine import policy_engine


class DecisionReceiptService:
    """Extracts persisted case, action, policy, and audit data to build immutable receipts."""

    def generate_receipt_for_case(self, case_id: str, session: Optional[Session] = None) -> Optional[DecisionReceipt]:
        close_session = False
        if session is None:
            session = SyncSessionLocal()
            close_session = True

        try:
            case = session.execute(select(ExceptionCase).where(ExceptionCase.case_id == case_id)).scalar_one_or_none()
            if not case:
                return None

            # Fetch corresponding audit event
            audit_event = session.execute(
                select(AuditTrailEvent)
                .where(AuditTrailEvent.case_id == case_id)
                .order_by(AuditTrailEvent.timestamp.desc())
                .limit(1)
            ).scalar_one_or_none()

            # Fetch approval request if any
            approval = session.execute(
                select(ApprovalRequest).where(ApprovalRequest.case_id == case_id).limit(1)
            ).scalar_one_or_none()

            # Parse evidence IDs
            evidence_ids = []
            if audit_event and audit_event.evidence_ids:
                try:
                    evidence_ids = json.loads(audit_event.evidence_ids)
                except Exception:
                    evidence_ids = [audit_event.evidence_ids]

            # Determine action and amount
            action_type = audit_event.action_type if audit_event else (
                approval.action_type if approval else "INVESTIGATE"
            )
            amount = case.amount_at_risk or Decimal("0.0")

            # Determine policy and autonomy level
            policy_eval = policy_engine.evaluate(action_type, amount)
            policy_version = policy_eval.policy_version
            policy_code = audit_event.policy_code if (audit_event and audit_event.policy_code) else policy_eval.policy_code
            policy_decision = audit_event.decision if audit_event else policy_eval.verdict
            autonomy_level = policy_eval.autonomy_level

            # Verification outcome
            verif_status = "PASSED" if (audit_event and audit_event.execution_result == "SUCCESS") else "PENDING"
            if audit_event and audit_event.execution_result == "VERIFICATION_FAILED":
                verif_status = "FAILED"

            receipt_id = f"RCP-{case_id.replace('EXC_', '')}"
            audit_id = audit_event.audit_id if audit_event else "AUD_PENDING"
            hash_digest = audit_event.hash_digest if audit_event else "HASH_UNCOMMITTED"
            agent_name = audit_event.agent_name if audit_event else "investigation_agent"
            reviewer = approval.reviewed_by if approval else None
            timestamp = audit_event.timestamp if audit_event else case.created_at

            return DecisionReceipt(
                receipt_id=receipt_id,
                case_id=case_id,
                action_type=action_type,
                amount=amount,
                currency=case.currency,
                root_cause=case.root_cause or "Pending Root Cause Analysis",
                candidate_causes=[case.failure_type],
                evidence_count=len(evidence_ids),
                evidence_summary=[{"evidence_id": eid} for eid in evidence_ids],
                policy_version=policy_version,
                policy_code=policy_code,
                policy_decision=policy_decision,
                autonomy_level=autonomy_level,
                verification_status=verif_status,
                audit_id=audit_id,
                hash_digest=hash_digest,
                agent_name=agent_name,
                reviewer=reviewer,
                timestamp=timestamp,
            )
        finally:
            if close_session:
                session.close()


decision_receipt_service = DecisionReceiptService()
