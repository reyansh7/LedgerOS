"""Deterministic Accounts Payable reconciliation: POs, Invoices, Lines, and Duplicate Detection."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models.operational import PurchaseOrder, POLine, Invoice, InvoiceLine, Vendor
from core.models.reconciliation import ReconciliationMatch, ExceptionCase


def normalize_ref(ref: str | None) -> str:
    if not ref:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", ref).upper()


def reconcile_po_invoices(
    session: Session,
    run_id: str,
    timestamp: str,
) -> Tuple[List[ReconciliationMatch], List[ExceptionCase]]:
    """Deterministic validation of purchase orders vs invoices and duplicate invoice detection."""
    matches: list[ReconciliationMatch] = []
    exceptions: list[ExceptionCase] = []

    invoices = session.execute(select(Invoice)).scalars().all()
    invoices_by_id = {inv.invoice_id: inv for inv in invoices}

    # 1. Duplicate Invoice Detection (F01)
    # Group invoices by vendor
    by_vendor: dict[str, list[Invoice]] = {}
    for inv in invoices:
        by_vendor.setdefault(inv.vendor_id, []).append(inv)

    reported_duplicates: set[str] = set()
    for vendor_id, vendor_invs in by_vendor.items():
        if len(vendor_invs) < 2:
            continue
        for i in range(len(vendor_invs)):
            for j in range(i + 1, len(vendor_invs)):
                inv1, inv2 = vendor_invs[i], vendor_invs[j]
                if abs(inv1.invoice_total - inv2.invoice_total) < Decimal("0.0001"):
                    norm1 = normalize_ref(inv1.invoice_number)
                    norm2 = normalize_ref(inv2.invoice_number)
                    # Check exact normalized match or explicit duplicate_reference
                    is_dup = (norm1 == norm2) or (inv1.duplicate_reference and inv1.duplicate_reference == inv2.invoice_id) or (inv2.duplicate_reference and inv2.duplicate_reference == inv1.invoice_id)
                    if is_dup:
                        dup_id = inv2.invoice_id if inv2.created_at and inv1.created_at and inv2.created_at >= inv1.created_at else inv1.invoice_id
                        orig_id = inv1.invoice_id if dup_id == inv2.invoice_id else inv2.invoice_id
                        pair_key = tuple(sorted([inv1.invoice_id, inv2.invoice_id]))
                        if str(pair_key) not in reported_duplicates:
                            reported_duplicates.add(str(pair_key))
                            exceptions.append(
                                ExceptionCase(
                                    case_id=f"EXC_F01_{dup_id}",
                                    run_id=run_id,
                                    failure_type="F01_DUPLICATE_INVOICE",
                                    primary_entity_type="invoice",
                                    primary_entity_id=dup_id,
                                    counterparty_id=vendor_id,
                                    amount_at_risk=inv2.invoice_total,
                                    currency=inv2.currency,
                                    observed_symptom=f"Duplicate invoice detected for vendor {vendor_id}: {inv2.invoice_id} matches {orig_id} with identical total {inv2.invoice_total}.",
                                    status="OPEN",
                                    severity="high",
                                    created_at=timestamp,
                                )
                            )

    # 2. PO vs Invoice 2-Way Matching (F02, F03, F04)
    for inv in invoices:
        if not inv.po_id:
            continue

        po = session.execute(select(PurchaseOrder).where(PurchaseOrder.po_id == inv.po_id)).scalar_one_or_none()
        if not po:
            continue

        # Vendor mismatch check (F04)
        if po.vendor_id != inv.vendor_id:
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F04_{inv.invoice_id}",
                    run_id=run_id,
                    failure_type="F04_INCORRECT_VENDOR_ASSOCIATION",
                    primary_entity_type="invoice",
                    primary_entity_id=inv.invoice_id,
                    counterparty_id=inv.vendor_id,
                    amount_at_risk=inv.invoice_total,
                    currency=inv.currency,
                    observed_symptom=f"Vendor mismatch: Invoice {inv.invoice_id} vendor {inv.vendor_id} does not match PO {po.po_id} vendor {po.vendor_id}.",
                    status="OPEN",
                    severity="high",
                    created_at=timestamp,
                )
            )
            continue

        # Total amount match check (F02)
        variance = abs(inv.invoice_total - po.po_total)
        tolerance = Decimal("0.02") * po.po_total  # 2% standard tolerance
        if variance > tolerance:
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F02_{inv.invoice_id}",
                    run_id=run_id,
                    failure_type="F02_PO_INVOICE_AMOUNT_MISMATCH",
                    primary_entity_type="invoice",
                    primary_entity_id=inv.invoice_id,
                    counterparty_id=inv.vendor_id,
                    amount_at_risk=variance,
                    currency=inv.currency,
                    observed_symptom=f"PO/Invoice amount mismatch: Invoice {inv.invoice_id} ({inv.invoice_total}) exceeds PO {po.po_id} ({po.po_total}) by {variance}.",
                    status="OPEN",
                    severity="medium",
                    created_at=timestamp,
                )
            )
        else:
            # Clean Match
            matches.append(
                ReconciliationMatch(
                    match_id=f"MAT_PO_{inv.invoice_id}",
                    run_id=run_id,
                    match_type="EXACT_PO_INV",
                    entity1_type="purchase_order",
                    entity1_id=po.po_id,
                    entity2_type="invoice",
                    entity2_id=inv.invoice_id,
                    amount1=po.po_total,
                    amount2=inv.invoice_total,
                    variance=variance,
                    confidence=Decimal("1.0000") if variance == Decimal("0") else Decimal("0.9800"),
                    matched_at=timestamp,
                )
            )

        # Line item quantity check (F03)
        inv_lines = session.execute(select(InvoiceLine).where(InvoiceLine.invoice_id == inv.invoice_id)).scalars().all()
        for il in inv_lines:
            if il.po_line_id:
                pl = session.execute(select(POLine).where(POLine.po_line_id == il.po_line_id)).scalar_one_or_none()
                if pl and il.quantity != pl.quantity:
                    qty_diff = abs(il.quantity - pl.quantity)
                    exceptions.append(
                        ExceptionCase(
                            case_id=f"EXC_F03_{il.invoice_line_id}",
                            run_id=run_id,
                            failure_type="F03_QUANTITY_MISMATCH",
                            primary_entity_type="invoice",
                            primary_entity_id=inv.invoice_id,
                            counterparty_id=inv.vendor_id,
                            amount_at_risk=il.line_amount,
                            currency=inv.currency,
                            observed_symptom=f"Line quantity mismatch: Line {il.invoice_line_id} qty {il.quantity} does not match PO line {pl.po_line_id} qty {pl.quantity}.",
                            status="OPEN",
                            severity="medium",
                            created_at=timestamp,
                        )
                    )

    return matches, exceptions
