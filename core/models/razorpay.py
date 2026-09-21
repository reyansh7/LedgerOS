"""SQLAlchemy models for Razorpay events, webhooks, and payment operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column,
    Numeric,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class RazorpayPaymentEvent(Base):
    __tablename__ = "razorpay_payments"

    payment_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # pay_...
    order_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), default="captured")
    method: Mapped[Optional[str]] = mapped_column(String(32))  # upi, card, netbanking
    fee: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    settlement_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), default="RAZORPAY_TEST")


class RazorpayRefundEvent(Base):
    __tablename__ = "razorpay_refunds"

    refund_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # rfn_...
    payment_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), default="processed")
    speed_processed: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), default="RAZORPAY_TEST")


class RazorpaySettlementEvent(Base):
    __tablename__ = "razorpay_settlements"

    settlement_id: Mapped[str] = mapped_column(String(64), primary_key=True)  # set_...
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), default="processed")
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    utr: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), default="RAZORPAY_TEST")


class RazorpayWebhookLog(Base):
    __tablename__ = "razorpay_webhooks"

    webhook_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[str] = mapped_column(String(64), nullable=False)
    processed_status: Mapped[str] = mapped_column(String(32), default="PROCESSED")
