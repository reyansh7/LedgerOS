"""Tests for Razorpay Webhook Ingestion, Idempotency, and Signature Verification."""

import hmac
import hashlib
import json
import uuid
import pytest
from sqlalchemy import select
from core.config import settings
from core.database import SyncSessionLocal
from core.models.razorpay import RazorpayWebhookLog, RazorpayPaymentEvent
from integrations.razorpay.webhook_handler import process_webhook_event, verify_webhook_signature


def test_webhook_signature_verification():
    secret = "test_webhook_secret_123"
    body = b'{"event":"payment.captured","payload":{}}'
    correct_sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    wrong_sig = "fake_invalid_signature_hex_0000"

    assert verify_webhook_signature(body, correct_sig, secret=secret) is True
    assert verify_webhook_signature(body, wrong_sig, secret=secret) is False


def test_webhook_idempotent_processing():
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": "order_test_1",
                    "amount": 750000,  # ₹7,500.00
                    "currency": "INR",
                    "status": "captured",
                    "method": "upi",
                    "fee": 1500,
                    "tax": 270,
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")

    # Generate valid signature if secret configured
    secret = settings.razorpay_webhook_secret
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest() if secret else ""

    # 1. First arrival: should process successfully
    res1 = process_webhook_event(event_id=event_id, raw_body=raw_body, signature=sig)
    assert res1["status"] == "success"
    assert res1["event_id"] == event_id

    # Verify payment stored in DB
    with SyncSessionLocal() as session:
        pmt = session.execute(
            select(RazorpayPaymentEvent).where(RazorpayPaymentEvent.payment_id == payment_id)
        ).scalar_one_or_none()
        assert pmt is not None
        assert float(pmt.amount) == 7500.0

    # 2. Replay of same event_id: must be ignored idempotently without creating duplicate DB rows
    res2 = process_webhook_event(event_id=event_id, raw_body=raw_body, signature=sig)
    assert res2["status"] == "ignored"
    assert "already been processed" in res2["message"]

