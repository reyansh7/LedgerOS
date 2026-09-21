"""Simulator for generating Razorpay payment events and settlement variances."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List
from core.database import SyncSessionLocal
from core.models.razorpay import RazorpayPaymentEvent, RazorpaySettlementEvent


def seed_razorpay_simulation(count: int = 50) -> list[dict[str, Any]]:
    """Generates synthetic Razorpay payment and settlement records with deliberate variances."""
    timestamp = datetime.now(timezone.utc).isoformat()
    generated = []

    with SyncSessionLocal() as session:
        for i in range(count):
            pay_id = f"pay_{uuid.uuid4().hex[:14]}"
            amount = Decimal(str(random.choice([1499.00, 2499.00, 4999.00, 9999.00, 14000.00])))
            fee = (amount * Decimal("0.02")).quantize(Decimal("0.01"))
            tax = (fee * Decimal("0.18")).quantize(Decimal("0.01"))

            # 10% chance of refund variance or failed settlement
            status = "captured" if i % 10 != 0 else "failed"

            record = RazorpayPaymentEvent(
                payment_id=pay_id,
                order_id=f"order_{uuid.uuid4().hex[:10]}",
                amount=amount,
                currency="INR",
                status=status,
                method=random.choice(["upi", "card", "netbanking"]),
                fee=fee,
                tax=tax,
                settlement_id=f"set_{uuid.uuid4().hex[:10]}" if status == "captured" else None,
                created_at=timestamp,
            )
            session.add(record)
            generated.append({"payment_id": pay_id, "amount": float(amount), "status": status})

        session.commit()

    return generated
