"""Master Deterministic Reconciliation Engine for LedgerOS."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import delete
from sqlalchemy.orm import Session

from core.database import SyncSessionLocal
from core.models.reconciliation import (
    ReconciliationRun,
    ReconciliationMatch,
    ExceptionCase,
)
from core.reconciliation.po_invoice import reconcile_po_invoices
from core.reconciliation.disbursements import reconcile_disbursements
from core.reconciliation.bank_rec import reconcile_bank_transactions
from core.reconciliation.gl_rec import reconcile_gl_entries


class ReconciliationEngine:
    """Orchestrates all deterministic reconciliation stages across accounting domains."""

    def run(self, dataset_scale: str = "small") -> dict[str, Any]:
        run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"
        start_time = datetime.now(timezone.utc).isoformat()

        with SyncSessionLocal() as session:
            # Wipe previous exception cases and matches for a fresh run
            session.execute(delete(ReconciliationMatch))
            session.execute(delete(ExceptionCase))
            session.commit()

            all_matches: list[ReconciliationMatch] = []
            all_exceptions: list[ExceptionCase] = []

            # Stage 1: PO vs Invoices & Duplicate Invoices
            m1, e1 = reconcile_po_invoices(session, run_id, start_time)
            all_matches.extend(m1)
            all_exceptions.extend(e1)

            # Stage 2: Disbursements, Allocations, Approvals & Vendor Changes
            m2, e2 = reconcile_disbursements(session, run_id, start_time)
            all_matches.extend(m2)
            all_exceptions.extend(e2)

            # Stage 3: Bank Reconciliation
            m3, e3 = reconcile_bank_transactions(session, run_id, start_time)
            all_matches.extend(m3)
            all_exceptions.extend(e3)

            # Stage 4: General Ledger
            m4, e4 = reconcile_gl_entries(session, run_id, start_time)
            all_matches.extend(m4)
            all_exceptions.extend(e4)

            # Deduplicate exception cases by primary_entity_id + failure_type
            unique_exceptions: dict[tuple[str, str], ExceptionCase] = {}
            for exc in all_exceptions:
                key = (exc.failure_type, exc.primary_entity_id)
                if key not in unique_exceptions:
                    unique_exceptions[key] = exc
            final_exceptions = list(unique_exceptions.values())

            # Save matches and exceptions
            session.bulk_save_objects(all_matches)
            session.bulk_save_objects(final_exceptions)

            total_records = len(all_matches) + len(final_exceptions)
            matched_count = len(all_matches)
            match_rate = Decimal("0.0")
            if total_records > 0:
                match_rate = (Decimal(str(matched_count)) / Decimal(str(total_records))) * Decimal("100.0")

            total_amount_at_risk = sum((e.amount_at_risk for e in final_exceptions), Decimal("0.0"))
            completed_time = datetime.now(timezone.utc).isoformat()

            run_record = ReconciliationRun(
                run_id=run_id,
                started_at=start_time,
                completed_at=completed_time,
                dataset_scale=dataset_scale,
                total_records=total_records,
                matched_records=matched_count,
                match_rate=match_rate.quantize(Decimal("0.01")),
                total_exceptions=len(final_exceptions),
                amount_at_risk=total_amount_at_risk.quantize(Decimal("0.01")),
                status="completed",
            )
            session.add(run_record)
            session.commit()

            return {
                "run_id": run_id,
                "dataset_scale": dataset_scale,
                "total_records": total_records,
                "matched_records": matched_count,
                "match_rate": float(match_rate.quantize(Decimal("0.01"))),
                "total_exceptions": len(final_exceptions),
                "amount_at_risk": float(total_amount_at_risk.quantize(Decimal("0.01"))),
                "breakdown_by_failure": {
                    f: sum(1 for e in final_exceptions if e.failure_type == f)
                    for f in sorted(set(e.failure_type for e in final_exceptions))
                },
                "status": "completed",
            }


reconciliation_engine = ReconciliationEngine()

if __name__ == "__main__":
    result = reconciliation_engine.run()
    print("Reconciliation Engine Run Completed:")
    print(f"  Run ID: {result['run_id']}")
    print(f"  Matched Records: {result['matched_records']}")
    print(f"  Match Rate: {result['match_rate']}%")
    print(f"  Total Exceptions: {result['total_exceptions']}")
    print(f"  Amount at Risk: INR/USD {result['amount_at_risk']:,.2f}")
    print("  Exceptions Breakdown:")
    for k, v in result["breakdown_by_failure"].items():
        print(f"    {k}: {v}")
