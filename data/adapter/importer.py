"""FinRCA-AI-Bench data ingestion adapter into LedgerOS operational database."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy import delete
from sqlalchemy.orm import Session

from core.database import SyncSessionLocal, sync_engine, Base
from core.models.operational import (
    Vendor,
    VendorChangeLog,
    PurchaseOrder,
    POLine,
    Invoice,
    InvoiceLine,
    ApprovalEvent,
    Payment,
    PaymentAllocation,
    GLEntry,
    BankTransaction,
    BankStatement,
    Employee,
    FinRCAAuditLog,
)


def _to_decimal(val: Any, default: str = "0.0000") -> Decimal:
    if val is None or val == "":
        return Decimal(default)
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _to_str(val: Any) -> str | None:
    if val is None or val == "":
        return None
    return str(val).strip()


def _to_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("true", "1", "yes", "t")


def import_finrca_dataset(data_dir: Path | str) -> dict[str, Any]:
    """Ingest FinRCA operational CSV tables into LedgerOS relational storage."""
    base_path = Path(data_dir)
    full_path = base_path / "full" if (base_path / "full").exists() else base_path
    if not full_path.exists():
        raise FileNotFoundError(f"FinRCA benchmark path does not exist: {full_path}")

    # Ensure tables exist
    Base.metadata.create_all(bind=sync_engine)

    report: dict[str, Any] = {
        "status": "success",
        "source_directory": str(full_path.resolve()),
        "imported_counts": {},
        "integrity_checks": {},
    }

    with SyncSessionLocal() as session:
        # Clear previous data in reverse foreign key order
        for model in (
            FinRCAAuditLog,
            PaymentAllocation,
            BankTransaction,
            BankStatement,
            GLEntry,
            Payment,
            ApprovalEvent,
            InvoiceLine,
            Invoice,
            POLine,
            PurchaseOrder,
            VendorChangeLog,
            Vendor,
            Employee,
        ):
            session.execute(delete(model))
        session.commit()

        # 1. Vendors
        vendors_csv = full_path / "vendors.csv"
        if vendors_csv.exists():
            with vendors_csv.open("r", encoding="utf-8") as f:
                records = [
                    Vendor(
                        vendor_id=r["vendor_id"],
                        vendor_name=r["vendor_name"],
                        vendor_type=_to_str(r.get("vendor_type")),
                        tax_id_hash=_to_str(r.get("tax_id_hash")),
                        country=_to_str(r.get("country")),
                        currency=r.get("currency") or "USD",
                        payment_terms=_to_str(r.get("payment_terms")),
                        default_payment_method=_to_str(r.get("default_payment_method")),
                        bank_account_token=_to_str(r.get("bank_account_token")),
                        bank_routing_token=_to_str(r.get("bank_routing_token")),
                        vendor_status=r.get("vendor_status") or "active",
                        created_at=_to_str(r.get("created_at")),
                        updated_at=_to_str(r.get("updated_at")),
                        source_system=r.get("source_system") or "VendorManagement",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["vendors"] = len(records)
            session.commit()

        # 2. Employees
        emp_csv = full_path / "employees.csv"
        if emp_csv.exists():
            with emp_csv.open("r", encoding="utf-8") as f:
                records = [
                    Employee(
                        employee_id=r["employee_id"],
                        role=_to_str(r.get("role")),
                        department=_to_str(r.get("department")),
                        approval_limit=_to_decimal(r.get("approval_limit")),
                        active_status=_to_bool(r.get("active_status", True)),
                        source_system=r.get("source_system") or "HRIS",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["employees"] = len(records)
            session.commit()

        # 3. Vendor Change Log
        vcl_csv = full_path / "vendor_change_log.csv"
        if vcl_csv.exists():
            with vcl_csv.open("r", encoding="utf-8") as f:
                records = [
                    VendorChangeLog(
                        change_id=r["change_id"],
                        vendor_id=r["vendor_id"],
                        field_changed=r["field_changed"],
                        old_value=_to_str(r.get("old_value")),
                        new_value=_to_str(r.get("new_value")),
                        changed_at=_to_str(r.get("changed_at")),
                        changed_by=_to_str(r.get("changed_by")),
                        change_reason=_to_str(r.get("change_reason")),
                        source_system=r.get("source_system") or "VendorManagement",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["vendor_change_log"] = len(records)
            session.commit()

        # 4. Purchase Orders
        po_csv = full_path / "purchase_orders.csv"
        if po_csv.exists():
            with po_csv.open("r", encoding="utf-8") as f:
                records = [
                    PurchaseOrder(
                        po_id=r["po_id"],
                        vendor_id=r["vendor_id"],
                        po_date=_to_str(r.get("po_date")),
                        currency=r.get("currency") or "USD",
                        subtotal=_to_decimal(r.get("subtotal")),
                        tax=_to_decimal(r.get("tax")),
                        shipping=_to_decimal(r.get("shipping")),
                        po_total=_to_decimal(r["po_total"]),
                        department=_to_str(r.get("department")),
                        cost_center=_to_str(r.get("cost_center")),
                        gl_account=_to_str(r.get("gl_account")),
                        status=r.get("status") or "issued",
                        expected_delivery_date=_to_str(r.get("expected_delivery_date")),
                        created_by=_to_str(r.get("created_by")),
                        source_system=r.get("source_system") or "ERP-Procurement",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["purchase_orders"] = len(records)
            session.commit()

        # 5. PO Lines
        pol_csv = full_path / "po_lines.csv"
        if pol_csv.exists():
            with pol_csv.open("r", encoding="utf-8") as f:
                records = [
                    POLine(
                        po_line_id=r["po_line_id"],
                        po_id=r["po_id"],
                        item_id=_to_str(r.get("item_id")),
                        description=_to_str(r.get("description")),
                        quantity=_to_decimal(r.get("quantity", "1")),
                        unit_price=_to_decimal(r.get("unit_price")),
                        line_amount=_to_decimal(r["line_amount"]),
                        gl_account=_to_str(r.get("gl_account")),
                        department=_to_str(r.get("department")),
                        cost_center=_to_str(r.get("cost_center")),
                        source_system=r.get("source_system") or "ERP-Procurement",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["po_lines"] = len(records)
            session.commit()

        # 6. Invoices
        inv_csv = full_path / "invoices.csv"
        if inv_csv.exists():
            with inv_csv.open("r", encoding="utf-8") as f:
                records = [
                    Invoice(
                        invoice_id=r["invoice_id"],
                        vendor_id=r["vendor_id"],
                        po_id=_to_str(r.get("po_id")),
                        invoice_number=r["invoice_number"],
                        invoice_date=_to_str(r.get("invoice_date")),
                        received_date=_to_str(r.get("received_date")),
                        due_date=_to_str(r.get("due_date")),
                        currency=r.get("currency") or "USD",
                        subtotal=_to_decimal(r.get("subtotal")),
                        tax=_to_decimal(r.get("tax")),
                        shipping=_to_decimal(r.get("shipping")),
                        invoice_total=_to_decimal(r["invoice_total"]),
                        payment_terms=_to_str(r.get("payment_terms")),
                        status=r.get("status") or "pending",
                        duplicate_reference=_to_str(r.get("duplicate_reference")),
                        created_at=_to_str(r.get("created_at")),
                        source_system=r.get("source_system") or "ERP-AP",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["invoices"] = len(records)
            session.commit()

        # 7. Invoice Lines
        invl_csv = full_path / "invoice_lines.csv"
        if invl_csv.exists():
            with invl_csv.open("r", encoding="utf-8") as f:
                records = [
                    InvoiceLine(
                        invoice_line_id=r["invoice_line_id"],
                        invoice_id=r["invoice_id"],
                        po_line_id=_to_str(r.get("po_line_id")),
                        item_id=_to_str(r.get("item_id")),
                        quantity=_to_decimal(r.get("quantity", "1")),
                        unit_price=_to_decimal(r.get("unit_price")),
                        line_amount=_to_decimal(r["line_amount"]),
                        gl_account=_to_str(r.get("gl_account")),
                        department=_to_str(r.get("department")),
                        cost_center=_to_str(r.get("cost_center")),
                        source_system=r.get("source_system") or "ERP-AP",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["invoice_lines"] = len(records)
            session.commit()

        # 8. Approval Events
        app_csv = full_path / "approval_events.csv"
        if app_csv.exists():
            with app_csv.open("r", encoding="utf-8") as f:
                records = [
                    ApprovalEvent(
                        approval_event_id=r["approval_event_id"],
                        invoice_id=r["invoice_id"],
                        approval_level=_to_str(r.get("approval_level")),
                        approver_id=_to_str(r.get("approver_id")),
                        approver_role=_to_str(r.get("approver_role")),
                        action=r["action"],
                        event_timestamp=_to_str(r.get("event_timestamp")),
                        previous_status=_to_str(r.get("previous_status")),
                        new_status=_to_str(r.get("new_status")),
                        comments=_to_str(r.get("comments")),
                        source_system=r.get("source_system") or "ERP-AP",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["approval_events"] = len(records)
            session.commit()

        # 9. Payments
        pay_csv = full_path / "payments.csv"
        if pay_csv.exists():
            with pay_csv.open("r", encoding="utf-8") as f:
                records = [
                    Payment(
                        payment_id=r["payment_id"],
                        vendor_id=r["vendor_id"],
                        payment_date=_to_str(r.get("payment_date")),
                        payment_method=_to_str(r.get("payment_method")),
                        payment_currency=r.get("payment_currency") or "USD",
                        payment_amount=_to_decimal(r["payment_amount"]),
                        bank_account_id=_to_str(r.get("bank_account_id")),
                        payment_status=r.get("payment_status") or "cleared",
                        settlement_status=_to_str(r.get("settlement_status")),
                        reference_number=_to_str(r.get("reference_number")),
                        created_at=_to_str(r.get("created_at")),
                        source_system=r.get("source_system") or "ERP-AP",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["payments"] = len(records)
            session.commit()

        # 10. Payment Allocations
        alloc_csv = full_path / "payment_allocations.csv"
        if alloc_csv.exists():
            with alloc_csv.open("r", encoding="utf-8") as f:
                records = [
                    PaymentAllocation(
                        payment_id=r["payment_id"],
                        invoice_id=r["invoice_id"],
                        allocation_date=r["allocation_date"],
                        allocated_amount=_to_decimal(r["allocated_amount"]),
                        source_system=r.get("source_system") or "ERP-AP",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["payment_allocations"] = len(records)
            session.commit()

        # 11. GL Entries
        gl_csv = full_path / "gl_entries.csv"
        if gl_csv.exists():
            with gl_csv.open("r", encoding="utf-8") as f:
                records = [
                    GLEntry(
                        journal_line_id=r["journal_line_id"],
                        journal_id=r["journal_id"],
                        transaction_type=_to_str(r.get("transaction_type")),
                        source_transaction_id=_to_str(r.get("source_transaction_id")),
                        posting_date=_to_str(r.get("posting_date")),
                        accounting_period=_to_str(r.get("accounting_period")),
                        gl_account=r["gl_account"],
                        debit=_to_decimal(r.get("debit")),
                        credit=_to_decimal(r.get("credit")),
                        currency=r.get("currency") or "USD",
                        department=_to_str(r.get("department")),
                        cost_center=_to_str(r.get("cost_center")),
                        memo=_to_str(r.get("memo")),
                        source_system=r.get("source_system") or "ERP-GL",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["gl_entries"] = len(records)
            session.commit()

        # 12. Bank Transactions
        bt_csv = full_path / "bank_transactions.csv"
        if bt_csv.exists():
            with bt_csv.open("r", encoding="utf-8") as f:
                records = [
                    BankTransaction(
                        bank_transaction_id=r["bank_transaction_id"],
                        bank_account_id=r["bank_account_id"],
                        transaction_date=_to_str(r.get("transaction_date")),
                        posted_date=_to_str(r.get("posted_date")),
                        transaction_type=_to_str(r.get("transaction_type")),
                        amount=_to_decimal(r["amount"]),
                        currency=r.get("currency") or "USD",
                        direction=r.get("direction") or "debit",
                        bank_reference=_to_str(r.get("bank_reference")),
                        counterparty_token=_to_str(r.get("counterparty_token")),
                        payment_reference=_to_str(r.get("payment_reference")),
                        status=r.get("status") or "posted",
                        source_system=r.get("source_system") or "Bank",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["bank_transactions"] = len(records)
            session.commit()

        # 13. Bank Statements
        bs_csv = full_path / "bank_statements.csv"
        if bs_csv.exists():
            with bs_csv.open("r", encoding="utf-8") as f:
                records = [
                    BankStatement(
                        bank_statement_id=r["bank_statement_id"],
                        bank_account_id=r["bank_account_id"],
                        statement_date=_to_str(r.get("statement_date")),
                        opening_balance=_to_decimal(r.get("opening_balance")),
                        closing_balance=_to_decimal(r.get("closing_balance")),
                        total_debits=_to_decimal(r.get("total_debits")),
                        total_credits=_to_decimal(r.get("total_credits")),
                        source_system=r.get("source_system") or "Bank",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["bank_statements"] = len(records)
            session.commit()

        # 14. Audit Log
        al_csv = full_path / "audit_log.csv"
        if al_csv.exists():
            with al_csv.open("r", encoding="utf-8") as f:
                records = [
                    FinRCAAuditLog(
                        event_id=r["event_id"],
                        entity_type=r["entity_type"],
                        entity_id=r["entity_id"],
                        event_type=r["event_type"],
                        timestamp=_to_str(r.get("timestamp")),
                        actor_id=_to_str(r.get("actor_id")),
                        field=_to_str(r.get("field")),
                        old_value=_to_str(r.get("old_value")),
                        new_value=_to_str(r.get("new_value")),
                        source_system=r.get("source_system") or "ERP-Audit",
                    )
                    for r in csv.DictReader(f)
                ]
                session.bulk_save_objects(records)
                report["imported_counts"]["audit_log"] = len(records)
            session.commit()

    return report


if __name__ == "__main__":
    from core.config import settings
    res = import_finrca_dataset(settings.finrca_data_dir)
    print("Import completed successfully:")
    for k, v in res["imported_counts"].items():
        print(f"  {k}: {v} records")
