"""Canonical Enterprise Financial Domain Models for LedgerOS.

These dataclasses define the stable, schema-independent financial concepts
that AI agents, reconciliation engines, and policy gates operate over.
Adapters translate source-specific systems (FinRCA SQLite, Razorpay API,
PostgreSQL, Snowflake, BigQuery) into these canonical domain structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, List, Optional


@dataclass
class CanonicalEntity:
    """Base financial entity preserving identity, provenance, and source metadata."""
    entity_id: str
    entity_type: str
    source_system: str
    source_connector: str
    amount: Decimal = Decimal("0.0")
    currency: str = "INR"
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalInvoiceLine:
    line_id: str
    invoice_id: str
    item_description: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal


@dataclass
class CanonicalInvoice:
    invoice_id: str
    vendor_id: str
    po_id: Optional[str]
    invoice_number: str
    invoice_date: str
    due_date: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str  # POSTED, PAID, VOIDED, PENDING
    source_system: str
    source_connector: str
    lines: list[CanonicalInvoiceLine] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalPurchaseOrderLine:
    line_id: str
    po_id: str
    item_description: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal


@dataclass
class CanonicalPurchaseOrder:
    po_id: str
    vendor_id: str
    po_number: str
    order_date: str
    total_amount: Decimal
    currency: str
    status: str  # APPROVED, FULFILLED, CLOSED, DRAFT
    source_system: str
    source_connector: str
    lines: list[CanonicalPurchaseOrderLine] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalPaymentAllocation:
    allocation_id: str
    payment_id: str
    invoice_id: str
    allocated_amount: Decimal


@dataclass
class CanonicalPayment:
    payment_id: str
    counterparty_id: Optional[str]
    amount: Decimal
    currency: str
    payment_method: str  # ACH, WIRE, UPI, CARD, CHECK
    payment_date: str
    status: str  # CLEARED, PENDING, FAILED, REVERSED
    reference_number: str
    source_system: str
    source_connector: str
    allocations: list[CanonicalPaymentAllocation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalBankTransaction:
    bank_tx_id: str
    account_number: str
    tx_date: str
    value_date: str
    amount: Decimal
    currency: str
    description: str
    reference_number: str
    balance_after: Decimal
    source_system: str
    source_connector: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalGLEntry:
    entry_id: str
    journal_id: str
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal
    currency: str
    effective_date: str
    description: str
    source_system: str
    source_connector: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalRefund:
    refund_id: str
    payment_id: str
    amount: Decimal
    currency: str
    status: str  # PROCESSED, PENDING, FAILED
    reason: str
    created_at: str
    source_system: str
    source_connector: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalSettlement:
    settlement_id: str
    gross_amount: Decimal
    fee_amount: Decimal
    tax_amount: Decimal
    net_amount: Decimal
    currency: str
    status: str  # SETTLED, PENDING, FAILED
    settled_at: str
    source_system: str
    source_connector: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalDispute:
    dispute_id: str
    entity_id: str
    amount: Decimal
    currency: str
    reason: str
    status: str  # OPEN, WON, LOST, UNDER_REVIEW
    created_at: str
    source_system: str
    source_connector: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalEvidence:
    evidence_id: str
    entity_type: str
    entity_id: str
    source_system: str
    source_connector: str
    data: dict[str, Any]
    relevance_score: float = 1.0
    retrieved_at: str = ""


@dataclass
class DecisionReceipt:
    """Immutable, explainable Decision Receipt representing a finalized financial or policy decision."""
    receipt_id: str
    case_id: str
    action_type: str
    amount: Decimal
    currency: str
    root_cause: str
    candidate_causes: list[str]
    evidence_count: int
    evidence_summary: list[dict[str, Any]]
    policy_version: str
    policy_code: str
    policy_decision: str
    autonomy_level: str  # L0_DETECT, L1_INVESTIGATE, L2_RECOMMEND, L3_EXECUTE_WITH_APPROVAL, L4_AUTONOMOUS_EXECUTION
    verification_status: str
    audit_id: str
    hash_digest: str
    agent_name: str
    reviewer: Optional[str]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "case_id": self.case_id,
            "action_type": self.action_type,
            "amount": float(self.amount),
            "currency": self.currency,
            "root_cause": self.root_cause,
            "candidate_causes": self.candidate_causes,
            "evidence_count": self.evidence_count,
            "evidence_summary": self.evidence_summary,
            "policy_version": self.policy_version,
            "policy_code": self.policy_code,
            "policy_decision": self.policy_decision,
            "autonomy_level": self.autonomy_level,
            "verification_status": self.verification_status,
            "audit_id": self.audit_id,
            "hash_digest": self.hash_digest,
            "agent_name": self.agent_name,
            "reviewer": self.reviewer,
            "timestamp": self.timestamp,
        }
