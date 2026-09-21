"""Razorpay endpoints: webhook ingestion, live status, and test simulation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models.razorpay import RazorpayPaymentEvent, RazorpayWebhookLog
from integrations.razorpay.webhook_handler import process_webhook_event
from integrations.razorpay.simulator import seed_razorpay_simulation

router = APIRouter(prefix="/razorpay", tags=["Razorpay Integration"])


@router.post("/webhook")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header("", alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str = Header("", alias="X-Razorpay-Event-Id"),
):
    body = await request.body()
    if not x_razorpay_event_id:
        # Fallback to body-derived or generated ID if header not provided in simulation
        x_razorpay_event_id = f"evt_{hash(body)}"

    res = process_webhook_event(
        event_id=x_razorpay_event_id,
        raw_body=body,
        signature=x_razorpay_signature,
    )
    if res.get("status") == "rejected":
        raise HTTPException(status_code=400, detail=res.get("reason"))
    return res


@router.post("/seed-simulation")
async def seed_simulation(count: int = 50):
    """Seed synthetic Razorpay payments and settlements to simulate live gateway traffic."""
    events = seed_razorpay_simulation(count=count)
    return {"status": "success", "seeded_count": len(events), "events": events[:5]}


@router.get("/payments")
async def list_payments(db: AsyncSession = Depends(get_db)):
    payments = (
        await db.execute(select(RazorpayPaymentEvent).order_by(desc(RazorpayPaymentEvent.created_at)).limit(50))
    ).scalars().all()
    return [
        {
            "payment_id": p.payment_id,
            "order_id": p.order_id,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "method": p.method,
            "fee": float(p.fee),
            "tax": float(p.tax),
            "created_at": p.created_at,
        }
        for p in payments
    ]
