"""FinRCA Financial Benchmark Adapter.

Connects LedgerOS to the benchmark SQLite operational database, exposing
canonical domain models across Accounts Payable, Disbursements, Bank Reconciliation,
and the General Ledger. Declares capability boundaries and strictly isolates
hidden evaluator ground truth.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from core.database import SyncSessionLocal
from core.models.operational import (
    Invoice,
    InvoiceLine,
    PurchaseOrder,
    POLine,
    Payment,
    PaymentAllocation,
    BankTransaction,
    GLEntry,
)
from core.domain.models import (
    CanonicalInvoice,
    CanonicalInvoiceLine,
    CanonicalPurchaseOrder,
    CanonicalPurchaseOrderLine,
    CanonicalPayment,
    CanonicalPaymentAllocation,
    CanonicalBankTransaction,
    CanonicalGLEntry,
)
from core.adapters.base import (
    BaseFinancialAdapter,
    ConnectorConfig,
    ConnectorHealth,
    FinancialCapability,
    CapabilityNotSupportedError,
)
from core.retrieval.provenance_graph import ProvenanceGraphRetriever


class FinRCAAdapter(BaseFinancialAdapter):
    """Adapter for FinRCA benchmark operational accounting systems."""

    def __init__(self, connector_id: str = "FINRCA-BENCH-01", connector_name: str = "FinRCA Enterprise ERP & Ledger"):
        config = ConnectorConfig(
            connector_id=connector_id,
            connector_name=connector_name,
            connector_type="finrca",
            environment="benchmark",
            enabled=True,
            capabilities={
                FinancialCapability.ACCOUNTS_PAYABLE,
                FinancialCapability.DISBURSEMENTS,
                FinancialCapability.BANK_RECONCILIATION,
                FinancialCapability.GENERAL_LEDGER,
            },
            permissions=["read", "write_bounded"],
        )
        super().__init__(config)

    def check_health(self) -> ConnectorHealth:
        start = time.perf_counter()
        try:
            with SyncSessionLocal() as session:
                count = session.execute(select(func.count(Invoice.invoice_id))).scalar() or 0
                latency = (time.perf_counter() - start) * 1000.0
                return ConnectorHealth(
                    status="HEALTHY",
                    last_sync=datetime.now(timezone.utc).isoformat(),
                    records_count=count,
                    latency_ms=round(latency, 2),
                    message=f"Connected to operational database ({count} invoices present)",
                )
        except Exception as e:
            return ConnectorHealth(
                status="OFFLINE",
                last_sync=datetime.now(timezone.utc).isoformat(),
                message=f"Database connectivity failure: {str(e)}",
            )

    def get_invoices(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalInvoice]:
        self.require_capability(FinancialCapability.ACCOUNTS_PAYABLE)
        with SyncSessionLocal() as session:
            stmt = select(Invoice).limit(limit)
            if filters and "vendor_id" in filters:
                stmt = stmt.where(Invoice.vendor_id == filters["vendor_id"])
            if filters and "status" in filters:
                stmt = stmt.where(Invoice.status == filters["status"])

            rows = session.execute(stmt).scalars().all()
            return [
                CanonicalInvoice(
                    invoice_id=inv.invoice_id,
                    vendor_id=inv.vendor_id,
                    po_id=inv.po_id,
                    invoice_number=inv.invoice_number,
                    invoice_date=str(inv.invoice_date),
                    due_date=str(inv.due_date),
                    subtotal=inv.subtotal,
                    tax_amount=inv.tax,
                    total_amount=inv.invoice_total,
                    currency=inv.currency,
                    status=inv.status.upper(),
                    source_system="FinRCA_ERP",
                    source_connector=self.connector_id,
                )
                for inv in rows
            ]

    def get_purchase_orders(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalPurchaseOrder]:
        self.require_capability(FinancialCapability.ACCOUNTS_PAYABLE)
        with SyncSessionLocal() as session:
            stmt = select(PurchaseOrder).limit(limit)
            if filters and "vendor_id" in filters:
                stmt = stmt.where(PurchaseOrder.vendor_id == filters["vendor_id"])

            rows = session.execute(stmt).scalars().all()
            return [
                CanonicalPurchaseOrder(
                    po_id=po.po_id,
                    vendor_id=po.vendor_id,
                    po_number=po.po_number,
                    order_date=str(po.order_date),
                    total_amount=po.po_total,
                    currency=po.currency,
                    status=po.status.upper(),
                    source_system="FinRCA_Procurement",
                    source_connector=self.connector_id,
                )
                for po in rows
            ]

    def get_payments(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalPayment]:
        self.require_capability(FinancialCapability.DISBURSEMENTS)
        with SyncSessionLocal() as session:
            stmt = select(Payment).limit(limit)
            rows = session.execute(stmt).scalars().all()
            return [
                CanonicalPayment(
                    payment_id=pmt.payment_id,
                    counterparty_id=pmt.vendor_id,
                    amount=pmt.payment_amount,
                    currency=pmt.payment_currency,
                    payment_method=pmt.payment_method or "DISBURSEMENT",
                    payment_date=str(pmt.payment_date),
                    status=pmt.payment_status.upper(),
                    reference_number=pmt.reference_number or pmt.payment_id,
                    source_system="FinRCA_AP_Disbursement",
                    source_connector=self.connector_id,
                )
                for pmt in rows
            ]

    def get_bank_transactions(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalBankTransaction]:
        self.require_capability(FinancialCapability.BANK_RECONCILIATION)
        with SyncSessionLocal() as session:
            stmt = select(BankTransaction).limit(limit)
            rows = session.execute(stmt).scalars().all()
            return [
                CanonicalBankTransaction(
                    bank_tx_id=bt.bank_transaction_id,
                    account_number=bt.bank_account_id,
                    tx_date=str(bt.transaction_date),
                    value_date=str(bt.posted_date or bt.transaction_date),
                    amount=bt.amount,
                    currency=bt.currency,
                    description=bt.transaction_type or "",
                    reference_number=bt.bank_reference or bt.payment_reference or "",
                    balance_after=Decimal("0.0"),
                    source_system="FinRCA_Bank_Feed",
                    source_connector=self.connector_id,
                )
                for bt in rows
            ]

    def get_gl_entries(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalGLEntry]:
        self.require_capability(FinancialCapability.GENERAL_LEDGER)
        with SyncSessionLocal() as session:
            stmt = select(GLEntry).limit(limit)
            if filters and "journal_id" in filters:
                stmt = stmt.where(GLEntry.journal_id == filters["journal_id"])

            rows = session.execute(stmt).scalars().all()
            return [
                CanonicalGLEntry(
                    entry_id=gl.journal_line_id,
                    journal_id=gl.journal_id,
                    account_code=gl.gl_account,
                    account_name=gl.gl_account,
                    debit=gl.debit,
                    credit=gl.credit,
                    currency=gl.currency,
                    effective_date=str(gl.posting_date),
                    description=gl.memo or "",
                    source_system="FinRCA_General_Ledger",
                    source_connector=self.connector_id,
                )
                for gl in rows
            ]

    def get_provenance_subgraph(self, primary_entity_type: str, primary_entity_id: str, max_hops: int = 3) -> dict[str, Any]:
        with SyncSessionLocal() as session:
            retriever = ProvenanceGraphRetriever(session)
            subgraph = retriever.get_provenance_subgraph(
                primary_entity_type=primary_entity_type,
                primary_entity_id=primary_entity_id,
                max_hops=max_hops,
            )
            # Add connector provenance tag to nodes
            for node in subgraph.get("nodes", []):
                node["source_connector"] = self.connector_id
            return subgraph
