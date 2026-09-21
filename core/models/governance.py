"""SQLAlchemy models for governance: agent runs, actions, human approvals, and immutable audit log."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)  # investigation_agent, reconciliation_agent
    case_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("exception_cases.case_id"), nullable=True, index=True)
    trigger_source: Mapped[str] = mapped_column(String(64), default="automated")  # automated, manual, webhook
    status: Mapped[str] = mapped_column(String(32), default="RUNNING", index=True)  # RUNNING, COMPLETED, INTERRUPTED, FAILED
    steps_count: Mapped[int] = mapped_column(default=0)
    start_time: Mapped[str] = mapped_column(String(64), nullable=False)
    end_time: Mapped[Optional[str]] = mapped_column(String(64))
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class AgentAction(Base):
    __tablename__ = "agent_actions"

    action_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_runs.run_id"), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)  # VOID_DUPLICATE_INVOICE, HOLD_PAYMENT, ADJUST_GL, INITIATE_RECOVERY
    input_payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON payload
    evidence_ids: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of entity IDs
    policy_verdict: Mapped[str] = mapped_column(String(32), nullable=False)  # ALLOW, DENY, REQUIRE_APPROVAL
    policy_rule_matched: Mapped[Optional[str]] = mapped_column(String(128))
    execution_status: Mapped[str] = mapped_column(String(32), default="PROPOSED")  # PROPOSED, APPROVED, EXECUTED, REJECTED
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    approval_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    action_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_actions.action_id"), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    policy_citation: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(64))
    review_comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String(64))


class AuditTrailEvent(Base):
    __tablename__ = "audit_trail_events"

    audit_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    input_payload: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    decision: Mapped[str] = mapped_column(String(32), nullable=False)  # APPROVED, REJECTED, AUTO_EXECUTED
    policy_code: Mapped[Optional[str]] = mapped_column(String(64))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=1.0)
    human_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    human_reviewer: Mapped[Optional[str]] = mapped_column(String(64))
    execution_result: Mapped[str] = mapped_column(String(32), default="SUCCESS")  # SUCCESS, FAILED
    previous_hash: Mapped[str] = mapped_column(String(64), default="")
    hash_digest: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
