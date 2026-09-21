"""Razorpay Webhook verification, deduplication, and event ingestion."""

from __future__ import annotations

import hmac
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SyncSessionLocal
from core.models.razorpay import (
    RazorpayWebhookLog,
    RazorpayPaymentEvent,
    RazorpayRefundEvent,
    RazorpaySettlementEvent,
)


def verify_webhook_signature(body_bytes: bytes, signature: str, secret: str | None = None) -> bool:
    """Verify HMAC SHA-256 signature against webhook secret."""
    sec = secret or settings.razorpay_webhook_secret
    if not sec:
        return True  # Bypass in dev without secret configured
    expected = hmac.new(sec.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def process_webhook_event(
    event_id: str,
    raw_body: bytes,
    signature: str,
) -> dict[str, Any]:
    """Process incoming Razorpay webhook with strict idempotency and schema mapping."""
    # 1. Signature Verification
    valid_sig = verify_webhook_signature(raw_body, signature)
    if not valid_sig:
        return {"status": "rejected", "reason": "Invalid HMAC signature"}

    payload: dict[str, Any] = json.loads(raw_body.decode("utf-8"))
    event_type = payload.get("event", "unknown")
    timestamp = datetime.now(timezone.utc).isoformat()

    with SyncSessionLocal() as session:
        # 2. Idempotency Check using x-razorpay-event-id
        existing = session.execute(
            select(RazorpayWebhookLog).where(RazorpayWebhookLog.webhook_id == event_id)
        ).scalar_one_or_none()

        if existing:
            return {
                "status": "ignored",
                "message": f"Event {event_id} has already been processed (idempotent skip).",
            }

        # Record webhook receipt
        log_entry = RazorpayWebhookLog(
            webhook_id=event_id,
            event_type=event_type,
            entity_id=payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "none"),
            signature_verified=valid_sig,
            payload_json=json.dumps(payload),
            received_at=timestamp,
            processed_status="PROCESSED",
        )
        session.add(log_entry)

        # 3. Entity State Ingestion
        p_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        if "payment" in event_type and p_entity:
            amt_inr = Decimal(str(p_entity.get("amount", 0))) / Decimal("100.0")
            fee_inr = Decimal(str(p_entity.get("fee", 0))) / Decimal("100.0")
            tax_inr = Decimal(str(p_entity.get("tax", 0))) / Decimal("100.0")

            payment_record = session.execute(
                select(RazorpayPaymentEvent).where(RazorpayPaymentEvent.payment_id == p_entity["id"])
            ).scalar_one_or_none()

            if not payment_record:
                payment_record = RazorpayPaymentEvent(
                    payment_id=p_entity["id"],
                    order_id=p_entity.get("order_id"),
                    amount=amt_inr,
                    currency=p_entity.get("currency", "INR"),
                    status=p_entity.get("status", "captured"),
                    method=p_entity.get("method"),
                    fee=fee_inr,
                    tax=tax_inr,
                    created_at=timestamp,
                )
                session.add(payment_record)
            else:
                # Handle out-of-order state transitions (e.g. captured arriving after failed)
                payment_record.status = p_entity.get("status", payment_record.status)

        session.commit()

    return {
        "status": "success",
        "event_id": event_id,
        "event_type": event_type,
        "processed_at": timestamp,
    }
