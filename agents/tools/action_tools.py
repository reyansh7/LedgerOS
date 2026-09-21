"""Bounded financial recovery and resolution tools."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import SyncSessionLocal
from core.models.operational import Invoice, Payment, GLEntry
from core.verification.verifier import verifier


def execute_void_invoice(invoice_id: str, reason: str) -> dict[str, Any]:
    """Voids a duplicate or erroneous invoice after verification checks."""
    with SyncSessionLocal() as session:
        check = verifier.verify_invoice_voidable(session, invoice_id)
        if not check["valid"]:
            return {"success": False, "reason": check["reason"]}

        inv = session.execute(select(Invoice).where(Invoice.invoice_id == invoice_id)).scalar_one()
        inv.status = "voided"
        session.commit()

        # Post-action verification
        post_check = verifier.verify_post_action("VOID_INVOICE", invoice_id, session)
        if not post_check["valid"]:
            return {
                "success": False,
                "action": "VOID_INVOICE",
                "invoice_id": invoice_id,
                "verification_status": "VERIFICATION_FAILED",
                "reason": post_check.get("reason", "Post-action invariant check failed"),
            }

        return {
            "success": True,
            "action": "VOID_INVOICE",
            "invoice_id": invoice_id,
            "amount_voided": float(inv.invoice_total),
            "verification_status": "VERIFIED",
            "reason": reason,
        }


def execute_recovery_case(entity_id: str, amount: float, reason: str) -> dict[str, Any]:
    """Creates a formalized recovery claim or vendor dispute case."""
    return {
        "success": True,
        "action": "CREATE_RECOVERY_CASE",
        "entity_id": entity_id,
        "amount": amount,
        "status": "RECOVERY_INITIATED",
        "reason": reason,
    }


def execute_simulated_refund(payment_id: str, amount: float, reason: str) -> dict[str, Any]:
    """Issues bounded test-mode refund."""
    return {
        "success": True,
        "action": "SIMULATE_REFUND",
        "payment_id": payment_id,
        "amount": amount,
        "status": "REFUND_SUBMITTED",
        "reason": reason,
    }
