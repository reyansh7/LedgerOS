"""Deterministic Disbursements and Approval reconciliation: Payments, Allocations, Approvals, and Vendor Changes."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models.operational import (
    Payment,
    PaymentAllocation,
    Invoice,
    ApprovalEvent,
    Employee,
    VendorChangeLog,
)
from core.models.reconciliation import ReconciliationMatch, ExceptionCase


def reconcile_disbursements(
    session: Session,
    run_id: str,
    timestamp: str,
) -> Tuple[List[ReconciliationMatch], List[ExceptionCase]]:
    """Deterministic validation of payment allocations, approvals, and double payments."""
    matches: list[ReconciliationMatch] = []
    exceptions: list[ExceptionCase] = []

    payments = session.execute(select(Payment)).scalars().all()
    invoices = session.execute(select(Invoice)).scalars().all()
    invoices_by_id = {inv.invoice_id: inv for inv in invoices}

    # 1. Payment without valid invoice allocation (F05)
    allocations = session.execute(select(PaymentAllocation)).scalars().all()
    alloc_by_pay: dict[str, list[PaymentAllocation]] = {}
    alloc_by_inv: dict[str, list[PaymentAllocation]] = {}
    for a in allocations:
        alloc_by_pay.setdefault(a.payment_id, []).append(a)
        alloc_by_inv.setdefault(a.invoice_id, []).append(a)

    for pay in payments:
        pay_allocs = alloc_by_pay.get(pay.payment_id, [])
        if not pay_allocs:
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F05_{pay.payment_id}",
                    run_id=run_id,
                    failure_type="F05_PAYMENT_WITHOUT_VALID_INVOICE",
                    primary_entity_type="payment",
                    primary_entity_id=pay.payment_id,
                    counterparty_id=pay.vendor_id,
                    amount_at_risk=pay.payment_amount,
                    currency=pay.payment_currency,
                    observed_symptom=f"Unallocated payment: Payment {pay.payment_id} of {pay.payment_amount} has no matching invoice allocation.",
                    status="OPEN",
                    severity="high",
                    created_at=timestamp,
                )
            )
        else:
            total_allocated = sum(a.allocated_amount for a in pay_allocs)
            diff = abs(pay.payment_amount - total_allocated)
            if diff < Decimal("0.0001"):
                matches.append(
                    ReconciliationMatch(
                        match_id=f"MAT_PAY_ALLOC_{pay.payment_id}",
                        run_id=run_id,
                        match_type="EXACT_PAY_ALLOC",
                        entity1_type="payment",
                        entity1_id=pay.payment_id,
                        entity2_type="invoice",
                        entity2_id=pay_allocs[0].invoice_id,
                        amount1=pay.payment_amount,
                        amount2=total_allocated,
                        variance=Decimal("0.0"),
                        confidence=Decimal("1.0000"),
                        matched_at=timestamp,
                    )
                )

    # 2. Invoice Paid Twice (F06) & Partial Payments (F07)
    for inv_id, inv in invoices_by_id.items():
        inv_allocs = alloc_by_inv.get(inv_id, [])
        if not inv_allocs:
            continue

        total_paid = sum(a.allocated_amount for a in inv_allocs)
        # Double payment check (paid significantly more than invoice total or allocated by 2+ separate payments)
        if len(inv_allocs) > 1 and total_paid > inv.invoice_total:
            overpaid = total_paid - inv.invoice_total
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F06_{inv_id}",
                    run_id=run_id,
                    failure_type="F06_DOUBLE_PAYMENT",
                    primary_entity_type="invoice",
                    primary_entity_id=inv_id,
                    counterparty_id=inv.vendor_id,
                    amount_at_risk=overpaid,
                    currency=inv.currency,
                    observed_symptom=f"Invoice paid twice / overpaid: Invoice {inv_id} for {inv.invoice_total} received multiple payments totaling {total_paid} (excess: {overpaid}).",
                    status="OPEN",
                    severity="critical",
                    created_at=timestamp,
                )
            )
        elif total_paid < inv.invoice_total and inv.status == "paid":
            # Partial payment marked as paid or residual balance
            unpaid = inv.invoice_total - total_paid
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F07_{inv_id}",
                    run_id=run_id,
                    failure_type="F07_PARTIAL_PAYMENT",
                    primary_entity_type="invoice",
                    primary_entity_id=inv_id,
                    counterparty_id=inv.vendor_id,
                    amount_at_risk=unpaid,
                    currency=inv.currency,
                    observed_symptom=f"Partial payment discrepancy: Invoice {inv_id} total {inv.invoice_total} only received {total_paid}, leaving unresolved balance of {unpaid}.",
                    status="OPEN",
                    severity="medium",
                    created_at=timestamp,
                )
            )

    # 3. Approval Workflow Check (F08)
    employees = {e.employee_id: e for e in session.execute(select(Employee)).scalars().all()}
    approvals = session.execute(select(ApprovalEvent)).scalars().all()
    for app in approvals:
        inv = invoices_by_id.get(app.invoice_id)
        if not inv:
            continue

        emp = employees.get(app.approver_id or "")
        if emp and inv.invoice_total > emp.approval_limit and app.action == "approve":
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F08_{app.approval_event_id}",
                    run_id=run_id,
                    failure_type="F08_APPROVAL_FAILURE",
                    primary_entity_type="approval_event",
                    primary_entity_id=app.approval_event_id,
                    counterparty_id=inv.vendor_id,
                    amount_at_risk=inv.invoice_total,
                    currency=inv.currency,
                    observed_symptom=f"Approval policy violation: Approver {emp.employee_id} limit {emp.approval_limit} was exceeded by invoice {inv.invoice_id} ({inv.invoice_total}).",
                    status="OPEN",
                    severity="high",
                    created_at=timestamp,
                )
            )

    # 4. Vendor Master Change Conflict (F11)
    changes = session.execute(select(VendorChangeLog)).scalars().all()
    for chg in changes:
        if "bank" in chg.field_changed.lower() or "routing" in chg.field_changed.lower():
            # Check payments to this vendor around the change timestamp
            vnd_payments = [p for p in payments if p.vendor_id == chg.vendor_id]
            for p in vnd_payments:
                if p.payment_date and chg.changed_at and p.payment_date >= chg.changed_at[:10]:
                    exceptions.append(
                        ExceptionCase(
                            case_id=f"EXC_F11_{p.payment_id}",
                            run_id=run_id,
                            failure_type="F11_VENDOR_CHANGE",
                            primary_entity_type="payment",
                            primary_entity_id=p.payment_id,
                            counterparty_id=chg.vendor_id,
                            amount_at_risk=p.payment_amount,
                            currency=p.payment_currency,
                            observed_symptom=f"Suspicious bank routing change: Payment {p.payment_id} ({p.payment_amount}) issued right after vendor {chg.vendor_id} modified {chg.field_changed}.",
                            status="OPEN",
                            severity="high",
                            created_at=timestamp,
                        )
                    )

    return matches, exceptions
