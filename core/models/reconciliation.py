"""SQLAlchemy models for reconciliation runs, matched records, and exception cases."""

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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    started_at: Mapped[str] = mapped_column(String(64), nullable=False)
    completed_at: Mapped[Optional[str]] = mapped_column(String(64))
    dataset_scale: Mapped[str] = mapped_column(String(32), default="small")
    total_records: Mapped[int] = mapped_column(default=0)
    matched_records: Mapped[int] = mapped_column(default=0)
    match_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0.0)  # e.g., 96.4000%
    total_exceptions: Mapped[int] = mapped_column(default=0)
    amount_at_risk: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="running")  # running, completed, failed


class ReconciliationMatch(Base):
    __tablename__ = "reconciliation_matches"

    match_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("reconciliation_runs.run_id"), nullable=False, index=True)
    match_type: Mapped[str] = mapped_column(String(64), nullable=False)  # EXACT, NORMALIZED_REF, TEMPORAL, PARTIAL
    entity1_type: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., purchase_order, payment
    entity1_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity2_type: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., invoice, bank_transaction
    entity2_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount1: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    amount2: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    variance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=1.0)
    matched_at: Mapped[str] = mapped_column(String(64), nullable=False)


class ExceptionCase(Base):
    __tablename__ = "exception_cases"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # RCA_... or EXC_...
    run_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("reconciliation_runs.run_id"), nullable=True, index=True)
    failure_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # F01_DUPLICATE_INVOICE, etc.
    primary_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)  # invoice, payment, etc.
    primary_entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    counterparty_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # vendor_id or bank_account
    amount_at_risk: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    observed_symptom: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)  # OPEN, INVESTIGATING, AWAITING_APPROVAL, RESOLVED, DISMISSED
    severity: Mapped[str] = mapped_column(String(16), default="medium", index=True)  # low, medium, high, critical
    evidence_collected: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON serialized list of IDs
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[Optional[str]] = mapped_column(String(64))
