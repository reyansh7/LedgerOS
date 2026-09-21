"""SQLAlchemy models for canonical operational financial entities (FinRCA-compatible)."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_type: Mapped[Optional[str]] = mapped_column(String(64))
    tax_id_hash: Mapped[Optional[str]] = mapped_column(String(128))
    country: Mapped[Optional[str]] = mapped_column(String(16))
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    payment_terms: Mapped[Optional[str]] = mapped_column(String(32))
    default_payment_method: Mapped[Optional[str]] = mapped_column(String(32))
    bank_account_token: Mapped[Optional[str]] = mapped_column(String(128))
    bank_routing_token: Mapped[Optional[str]] = mapped_column(String(128))
    vendor_status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[Optional[str]] = mapped_column(String(64))
    source_system: Mapped[str] = mapped_column(String(64), default="VendorManagement")


class VendorChangeLog(Base):
    __tablename__ = "vendor_change_log"

    change_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String(64), ForeignKey("vendors.vendor_id"), nullable=False, index=True)
    field_changed: Mapped[str] = mapped_column(String(64), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    changed_at: Mapped[Optional[str]] = mapped_column(String(64))
    changed_by: Mapped[Optional[str]] = mapped_column(String(64))
    change_reason: Mapped[Optional[str]] = mapped_column(Text)
    source_system: Mapped[str] = mapped_column(String(64), default="VendorManagement")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    po_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String(64), ForeignKey("vendors.vendor_id"), nullable=False, index=True)
    po_date: Mapped[Optional[str]] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    shipping: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    po_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(64))
    cost_center: Mapped[Optional[str]] = mapped_column(String(64))
    gl_account: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="issued")
    expected_delivery_date: Mapped[Optional[str]] = mapped_column(String(32))
    created_by: Mapped[Optional[str]] = mapped_column(String(64))
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-Procurement")


class POLine(Base):
    __tablename__ = "po_lines"

    po_line_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    po_id: Mapped[str] = mapped_column(String(64), ForeignKey("purchase_orders.po_id"), nullable=False, index=True)
    item_id: Mapped[Optional[str]] = mapped_column(String(64))
    description: Mapped[Optional[str]] = mapped_column(Text)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=1.0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    gl_account: Mapped[Optional[str]] = mapped_column(String(64))
    department: Mapped[Optional[str]] = mapped_column(String(64))
    cost_center: Mapped[Optional[str]] = mapped_column(String(64))
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-Procurement")


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String(64), ForeignKey("vendors.vendor_id"), nullable=False, index=True)
    po_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    invoice_date: Mapped[Optional[str]] = mapped_column(String(32))
    received_date: Mapped[Optional[str]] = mapped_column(String(32))
    due_date: Mapped[Optional[str]] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    shipping: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    invoice_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, index=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    duplicate_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String(64))
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-AP")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    invoice_line_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(64), ForeignKey("invoices.invoice_id"), nullable=False, index=True)
    po_line_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    item_id: Mapped[Optional[str]] = mapped_column(String(64))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=1.0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    gl_account: Mapped[Optional[str]] = mapped_column(String(64))
    department: Mapped[Optional[str]] = mapped_column(String(64))
    cost_center: Mapped[Optional[str]] = mapped_column(String(64))
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-AP")


class ApprovalEvent(Base):
    __tablename__ = "approval_events"

    approval_event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(64), ForeignKey("invoices.invoice_id"), nullable=False, index=True)
    approval_level: Mapped[Optional[str]] = mapped_column(String(32))
    approver_id: Mapped[Optional[str]] = mapped_column(String(64))
    approver_role: Mapped[Optional[str]] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    event_timestamp: Mapped[Optional[str]] = mapped_column(String(64))
    previous_status: Mapped[Optional[str]] = mapped_column(String(32))
    new_status: Mapped[Optional[str]] = mapped_column(String(32))
    comments: Mapped[Optional[str]] = mapped_column(Text)
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-AP")


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(String(64), ForeignKey("vendors.vendor_id"), nullable=False, index=True)
    payment_date: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(32))
    payment_currency: Mapped[str] = mapped_column(String(8), default="USD")
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, index=True)
    bank_account_id: Mapped[Optional[str]] = mapped_column(String(64))
    payment_status: Mapped[str] = mapped_column(String(32), default="cleared", index=True)
    settlement_status: Mapped[Optional[str]] = mapped_column(String(32))
    reference_number: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    created_at: Mapped[Optional[str]] = mapped_column(String(64))
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-AP")


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    payment_id: Mapped[str] = mapped_column(String(64), ForeignKey("payments.payment_id"), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(64), ForeignKey("invoices.invoice_id"), primary_key=True)
    allocation_date: Mapped[str] = mapped_column(String(32), primary_key=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-AP")


class GLEntry(Base):
    __tablename__ = "gl_entries"

    journal_line_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    journal_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    transaction_type: Mapped[Optional[str]] = mapped_column(String(64))
    source_transaction_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    posting_date: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    accounting_period: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    gl_account: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    department: Mapped[Optional[str]] = mapped_column(String(64))
    cost_center: Mapped[Optional[str]] = mapped_column(String(64))
    memo: Mapped[Optional[str]] = mapped_column(Text)
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-GL")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    bank_transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    bank_account_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    transaction_date: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    posted_date: Mapped[Optional[str]] = mapped_column(String(32))
    transaction_type: Mapped[Optional[str]] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    direction: Mapped[str] = mapped_column(String(16), default="debit")
    bank_reference: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    counterparty_token: Mapped[Optional[str]] = mapped_column(String(128))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="posted")
    source_system: Mapped[str] = mapped_column(String(64), default="Bank")


class BankStatement(Base):
    __tablename__ = "bank_statements"

    bank_statement_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    bank_account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    statement_date: Mapped[Optional[str]] = mapped_column(String(32))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    total_debits: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    total_credits: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    source_system: Mapped[str] = mapped_column(String(64), default="Bank")


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role: Mapped[Optional[str]] = mapped_column(String(64))
    department: Mapped[Optional[str]] = mapped_column(String(64))
    approval_limit: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    active_status: Mapped[bool] = mapped_column(default=True)
    source_system: Mapped[str] = mapped_column(String(64), default="HRIS")


class FinRCAAuditLog(Base):
    __tablename__ = "audit_log"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[Optional[str]] = mapped_column(String(64))
    actor_id: Mapped[Optional[str]] = mapped_column(String(64))
    field: Mapped[Optional[str]] = mapped_column(String(64))
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    source_system: Mapped[str] = mapped_column(String(64), default="ERP-Audit")
