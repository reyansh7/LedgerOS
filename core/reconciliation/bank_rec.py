"""Deterministic Bank Reconciliation: Matching ERP Payments to Bank Statement Transactions."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models.operational import Payment, BankTransaction
from core.models.reconciliation import ReconciliationMatch, ExceptionCase


def reconcile_bank_transactions(
    session: Session,
    run_id: str,
    timestamp: str,
) -> Tuple[List[ReconciliationMatch], List[ExceptionCase]]:
    """Deterministic validation of ERP payments vs Bank Transactions (F12, F13, F14, F15)."""
    matches: list[ReconciliationMatch] = []
    exceptions: list[ExceptionCase] = []

    payments = session.execute(select(Payment)).scalars().all()
    bank_txs = session.execute(select(BankTransaction)).scalars().all()

    # Index bank transactions by payment_reference and bank_reference
    bt_by_ref: dict[str, list[BankTransaction]] = {}
    bt_matched_ids: set[str] = set()

    for bt in bank_txs:
        if bt.payment_reference:
            bt_by_ref.setdefault(bt.payment_reference, []).append(bt)
        if bt.bank_reference:
            bt_by_ref.setdefault(bt.bank_reference, []).append(bt)

    # 1. Match ERP Payments to Bank Transactions
    for pay in payments:
        matching_bts: list[BankTransaction] = []
        if pay.reference_number and pay.reference_number in bt_by_ref:
            matching_bts = bt_by_ref[pay.reference_number]
        elif pay.payment_id in bt_by_ref:
            matching_bts = bt_by_ref[pay.payment_id]

        if not matching_bts:
            # F12: ERP payment missing from bank
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F12_{pay.payment_id}",
                    run_id=run_id,
                    failure_type="F12_ERP_PAYMENT_MISSING_BANK",
                    primary_entity_type="payment",
                    primary_entity_id=pay.payment_id,
                    counterparty_id=pay.vendor_id,
                    amount_at_risk=pay.payment_amount,
                    currency=pay.payment_currency,
                    observed_symptom=f"ERP payment missing from bank: Payment {pay.payment_id} ({pay.payment_amount}) has no corresponding clearing transaction on bank statement.",
                    status="OPEN",
                    severity="high",
                    created_at=timestamp,
                )
            )
        else:
            bt = matching_bts[0]
            bt_matched_ids.add(bt.bank_transaction_id)

            # Check amount variance (F14)
            amount_diff = abs(pay.payment_amount - bt.amount)
            if amount_diff > Decimal("0.0001"):
                exceptions.append(
                    ExceptionCase(
                        case_id=f"EXC_F14_{pay.payment_id}",
                        run_id=run_id,
                        failure_type="F14_BANK_ERP_AMOUNT_MISMATCH",
                        primary_entity_type="payment",
                        primary_entity_id=pay.payment_id,
                        counterparty_id=pay.vendor_id,
                        amount_at_risk=amount_diff,
                        currency=pay.payment_currency,
                        observed_symptom=f"Bank/ERP amount mismatch: ERP Payment {pay.payment_id} recorded {pay.payment_amount}, but bank transaction {bt.bank_transaction_id} cleared for {bt.amount} (variance: {amount_diff}).",
                        status="OPEN",
                        severity="medium",
                        created_at=timestamp,
                    )
                )
            # Check bank account token / direction / reference integrity (F15)
            elif pay.bank_account_id and bt.bank_account_id and pay.bank_account_id != bt.bank_account_id:
                exceptions.append(
                    ExceptionCase(
                        case_id=f"EXC_F15_{pay.payment_id}",
                        run_id=run_id,
                        failure_type="F15_INCORRECT_BANK_MATCH",
                        primary_entity_type="payment",
                        primary_entity_id=pay.payment_id,
                        counterparty_id=pay.vendor_id,
                        amount_at_risk=pay.payment_amount,
                        currency=pay.payment_currency,
                        observed_symptom=f"Incorrect payment-to-bank match: ERP account {pay.bank_account_id} does not match bank account {bt.bank_account_id}.",
                        status="OPEN",
                        severity="high",
                        created_at=timestamp,
                    )
                )
            else:
                # Clean bank match
                matches.append(
                    ReconciliationMatch(
                        match_id=f"MAT_BANK_{pay.payment_id}",
                        run_id=run_id,
                        match_type="EXACT_BANK_PAY",
                        entity1_type="payment",
                        entity1_id=pay.payment_id,
                        entity2_type="bank_transaction",
                        entity2_id=bt.bank_transaction_id,
                        amount1=pay.payment_amount,
                        amount2=bt.amount,
                        variance=Decimal("0.0"),
                        confidence=Decimal("1.0000"),
                        matched_at=timestamp,
                    )
                )

    # 2. Check Bank Transactions missing from ERP (F13)
    for bt in bank_txs:
        if bt.bank_transaction_id not in bt_matched_ids and bt.direction == "debit":
            # Check if this debit had no matching payment in ERP
            exceptions.append(
                ExceptionCase(
                    case_id=f"EXC_F13_{bt.bank_transaction_id}",
                    run_id=run_id,
                    failure_type="F13_BANK_MISSING_ERP",
                    primary_entity_type="bank_transaction",
                    primary_entity_id=bt.bank_transaction_id,
                    counterparty_id=bt.bank_account_id,
                    amount_at_risk=bt.amount,
                    currency=bt.currency,
                    observed_symptom=f"Bank transaction missing from ERP: Bank debit {bt.bank_transaction_id} of {bt.amount} appeared on bank statement without prior ERP authorization.",
                    status="OPEN",
                    severity="high",
                    created_at=timestamp,
                )
            )

    return matches, exceptions
