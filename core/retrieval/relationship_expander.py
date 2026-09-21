"""Expands evidence candidates using normalized references, amounts, and temporal windows."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, List
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models.operational import Invoice, Payment, BankTransaction, PurchaseOrder


def normalize_ref(ref: str | None) -> str:
    """Strip punctuation and whitespace for robust reference comparison."""
    if not ref:
        return ""
    return re.sub(r"[^a-zA-Z0-9]", "", ref).upper()


class RelationshipExpander:
    """Identifies candidate matches across systems when direct foreign keys are obscured or corrupted."""

    def __init__(self, session: Session):
        self.session = session

    def find_duplicate_invoices(self, target_invoice: Invoice, similarity_threshold: float = 85.0) -> list[Invoice]:
        """Find other invoices from the same vendor with matching amounts or similar references."""
        candidates = self.session.execute(
            select(Invoice).where(
                (Invoice.vendor_id == target_invoice.vendor_id) &
                (Invoice.invoice_id != target_invoice.invoice_id)
            )
        ).scalars().all()

        duplicates = []
        norm_target_ref = normalize_ref(target_invoice.invoice_number)

        for cand in candidates:
            # Exact amount match + normalized reference match
            if abs(cand.invoice_total - target_invoice.invoice_total) < Decimal("0.01"):
                norm_cand_ref = normalize_ref(cand.invoice_number)
                if norm_target_ref == norm_cand_ref:
                    duplicates.append(cand)
                    continue

                sim = fuzz.ratio(norm_target_ref, norm_cand_ref)
                if sim >= similarity_threshold:
                    duplicates.append(cand)

        return duplicates

    def find_unmatched_bank_transactions(self, payment: Payment, days_tolerance: int = 5) -> list[BankTransaction]:
        """Find bank transactions matching amount within temporal window."""
        candidates = self.session.execute(
            select(BankTransaction).where(
                (BankTransaction.amount == payment.payment_amount) &
                (BankTransaction.direction == "debit")
            )
        ).scalars().all()
        return candidates
