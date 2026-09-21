"""Razorpay Test Mode Client & Simulated Environment Adapter."""

from __future__ import annotations

import hmac
import hashlib
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional
import httpx

from core.config import settings


class RazorpayClient:
    """Client for interacting with Razorpay APIs or simulated test transactions."""

    def __init__(
        self,
        key_id: str | None = None,
        key_secret: str | None = None,
        base_url: str = "https://api.razorpay.com/v1",
        use_simulator: bool = True,
    ):
        self.key_id = key_id or settings.razorpay_key_id
        self.key_secret = key_secret or settings.razorpay_key_secret
        self.base_url = base_url
        self.use_simulator = use_simulator or (self.key_id == "rzp_test_dummykey123")

    async def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """Fetch payment details from Razorpay or local test simulator."""
        if self.use_simulator:
            return {
                "id": payment_id,
                "entity": "payment",
                "amount": 240000,  # in paise (₹2,400.00)
                "currency": "INR",
                "status": "captured",
                "method": "upi",
                "fee": 4800,
                "tax": 864,
                "settled": True,
            }

        async with httpx.AsyncClient(auth=(self.key_id, self.key_secret)) as client:
            resp = await client.get(f"{self.base_url}/payments/{payment_id}")
            resp.raise_for_status()
            return resp.json()

    async def create_refund(
        self,
        payment_id: str,
        amount_paise: int,
        speed: str = "normal",
        notes: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Initiate payment refund (gated in simulator or test mode)."""
        if self.use_simulator:
            refund_id = f"rfnd_{uuid.uuid4().hex[:14]}"
            return {
                "id": refund_id,
                "entity": "refund",
                "payment_id": payment_id,
                "amount": amount_paise,
                "currency": "INR",
                "status": "processed",
                "speed_processed": speed,
                "notes": notes or {},
            }

        async with httpx.AsyncClient(auth=(self.key_id, self.key_secret)) as client:
            payload = {
                "amount": amount_paise,
                "speed": speed,
                "notes": notes or {},
            }
            resp = await client.post(f"{self.base_url}/payments/{payment_id}/refund", json=payload)
            resp.raise_for_status()
            return resp.json()


razorpay_client = RazorpayClient()
