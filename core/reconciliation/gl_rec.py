"""Deterministic General Ledger reconciliation: Balancing Debits & Credits, and Period Verification."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models.operational import GLEntry, Invoice, Payment
from core.models.reconciliation import ReconciliationMatch, ExceptionCase


def reconcile_gl_entries(
    session: Session,
    run_id: str,
    timestamp: str,
) -> Tuple[List[ReconciliationMatch], List[ExceptionCase]]:
    """Deterministic validation of General Ledger entries (F09, F10)."""
    matches: list[ReconciliationMatch] = []
    exceptions: list[ExceptionCase] = []

    gl_entries = session.execute(select(GLEntry)).scalars().all()

    # 1. Group by journal_id to check double-entry balance (Debits == Credits)
    by_journal: dict[str, list[GLEntry]] = {}
    for g in gl_entries:
        by_journal.setdefault(g.journal_id, []).append(g)

    for j_id, entries in by_journal.items():
        total_debit = sum(e.debit for e in entries)
        total_credit = sum(e.credit for e in entries)
        diff = abs(total_debit - total_credit)

        if diff > Decimal("0.0001"):
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F09_{j_id}",
                    run_id=run_id,
                    failure_type="F09_GL_MISMATCH",
                    primary_entity_type="gl_journal",
                    primary_entity_id=j_id,
                    counterparty_id=entries[0].gl_account,
                    amount_at_risk=diff,
                    currency=entries[0].currency,
                    observed_symptom=f"GL journal out of balance: Journal {j_id} has total debits {total_debit} != credits {total_credit} (imbalance: {diff}).",
                    status="OPEN",
                    severity="high",
                    created_at=timestamp,
                )
            )
        else:
            matches.append(
                ReconciliationMatch(
                    match_id=f"MAT_GL_{j_id}",
                    run_id=run_id,
                    match_type="GL_BALANCED",
                    entity1_type="gl_journal",
                    entity1_id=j_id,
                    entity2_type="gl_journal",
                    entity2_id=j_id,
                    amount1=total_debit,
                    amount2=total_credit,
                    variance=Decimal("0.0"),
                    confidence=Decimal("1.0000"),
                    matched_at=timestamp,
                )
            )

        # 2. Accounting Period Verification (F10)
        for e in entries:
            if e.posting_date and e.accounting_period:
                posting_period = e.posting_date[:7]  # YYYY-MM
                if posting_period != e.accounting_period:
                    exceptions.append(
                        ExceptionCase(
                            case_id=f"EXC_F10_{e.journal_line_id}",
                            run_id=run_id,
                            failure_type="F10_WRONG_PERIOD",
                            primary_entity_type="gl_entry",
                            primary_entity_id=e.journal_line_id,
                            counterparty_id=e.gl_account,
                            amount_at_risk=max(e.debit, e.credit),
                            currency=e.currency,
                            observed_symptom=f"Wrong accounting period: Entry {e.journal_line_id} posted on {e.posting_date} ({posting_period}) but assigned to accounting period {e.accounting_period}.",
                            status="OPEN",
                            severity="medium",
                            created_at=timestamp,
                        )
                    )

    return matches, exceptions
