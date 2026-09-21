"""Immutable, cryptographically chained Audit Trail logger."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from core.database import SyncSessionLocal
from core.models.governance import AuditTrailEvent


class AuditLogger:
    """Records audit events with SHA-256 hash chaining to ensure tamper-evident provenance."""

    def log_event(
        self,
        agent_name: str,
        action_type: str,
        case_id: Optional[str],
        input_payload: dict[str, Any],
        evidence_ids: list[str],
        decision: str,
        policy_code: Optional[str],
        confidence_score: float = 1.0,
        human_approval: bool = False,
        human_reviewer: Optional[str] = None,
        execution_result: str = "SUCCESS",
    ) -> AuditTrailEvent:
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_id = f"AUD_{uuid.uuid4().hex[:12].upper()}"

        with SyncSessionLocal() as session:
            # Fetch previous hash
            last_event = session.execute(
                select(AuditTrailEvent).order_by(desc(AuditTrailEvent.timestamp)).limit(1)
            ).scalar_one_or_none()
            prev_hash = last_event.hash_digest if last_event else "GENESIS_LEDGEROS_00000000000000"

            # Compute hash digest of current event
            payload_str = json.dumps(input_payload, sort_keys=True, default=str)
            evidence_str = json.dumps(sorted(evidence_ids))
            raw_data = f"{prev_hash}|{audit_id}|{agent_name}|{action_type}|{case_id}|{payload_str}|{evidence_str}|{decision}|{policy_code}|{timestamp}"
            hash_digest = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

            event = AuditTrailEvent(
                audit_id=audit_id,
                agent_name=agent_name,
                action_type=action_type,
                case_id=case_id,
                input_payload=payload_str,
                evidence_ids=evidence_str,
                decision=decision,
                policy_code=policy_code,
                confidence_score=Decimal(str(confidence_score)),
                human_approval=human_approval,
                human_reviewer=human_reviewer,
                execution_result=execution_result,
                previous_hash=prev_hash,
                hash_digest=hash_digest,
                timestamp=timestamp,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            session.expunge(event)
            return event

    def verify_chain(self, session: Session | None = None) -> dict[str, Any]:
        """Independently verifies the complete SHA-256 hash chain across all audit events."""
        close_session = False
        if session is None:
            session = SyncSessionLocal()
            close_session = True

        try:
            # Query all events in chronological order
            events = session.execute(
                select(AuditTrailEvent).order_by(AuditTrailEvent.timestamp.asc())
            ).scalars().all()

            if not events:
                return {
                    "valid": True,
                    "total_events": 0,
                    "verified_blocks": 0,
                    "genesis_hash": "NONE",
                    "head_hash": "NONE",
                    "message": "Empty ledger; chain is trivially valid.",
                }

            expected_prev_hash = "GENESIS_LEDGEROS_00000000000000"
            for idx, event in enumerate(events):
                # 1. Verify previous hash chaining
                if event.previous_hash != expected_prev_hash:
                    return {
                        "valid": False,
                        "failed_at_audit_id": event.audit_id,
                        "failed_at_index": idx,
                        "expected_prev_hash": expected_prev_hash,
                        "actual_prev_hash": event.previous_hash,
                        "reason": f"Hash chain linkage broken at event index {idx} ({event.audit_id}).",
                    }

                # 2. Recompute SHA-256 digest
                raw_data = (
                    f"{event.previous_hash}|{event.audit_id}|{event.agent_name}|"
                    f"{event.action_type}|{event.case_id}|{event.input_payload}|"
                    f"{event.evidence_ids}|{event.decision}|{event.policy_code}|{event.timestamp}"
                )
                computed_digest = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
                if computed_digest != event.hash_digest:
                    return {
                        "valid": False,
                        "failed_at_audit_id": event.audit_id,
                        "failed_at_index": idx,
                        "expected_hash": computed_digest,
                        "actual_hash": event.hash_digest,
                        "reason": f"Cryptographic digest mismatch at event index {idx} ({event.audit_id}). Data was tampered with.",
                    }

                expected_prev_hash = event.hash_digest

            return {
                "valid": True,
                "total_events": len(events),
                "verified_blocks": len(events),
                "genesis_hash": events[0].hash_digest,
                "head_hash": events[-1].hash_digest,
                "message": f"Successfully verified SHA-256 hash integrity across {len(events)} blocks.",
            }
        finally:
            if close_session:
                session.close()


audit_logger = AuditLogger()
