"""Razorpay Payment Gateway Adapter for LedgerOS.

Connects LedgerOS to Razorpay's payment infrastructure, exposing canonical domain
models for gateway charges, payment orders, merchant settlements, and refunds.
Explicitly rejects unsupported enterprise accounting operations (e.g. Purchase Orders, GL).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func

from core.database import SyncSessionLocal
from core.models.razorpay import (
    RazorpayPaymentEvent,
    RazorpayRefundEvent,
    RazorpaySettlementEvent,
    RazorpayWebhookLog,
)
from core.domain.models import (
    CanonicalPayment,
    CanonicalRefund,
    CanonicalSettlement,
    CanonicalDispute,
)
from core.adapters.base import (
    BaseFinancialAdapter,
    ConnectorConfig,
    ConnectorHealth,
    FinancialCapability,
    CapabilityNotSupportedError,
)


class RazorpayAdapter(BaseFinancialAdapter):
    """Adapter for Razorpay payment gateway data sources."""

    def __init__(self, connector_id: str = "RAZORPAY-GATEWAY-01", connector_name: str = "Razorpay Payment Processing Gateway"):
        config = ConnectorConfig(
            connector_id=connector_id,
            connector_name=connector_name,
            connector_type="razorpay",
            environment="test",
            enabled=True,
            capabilities={
                FinancialCapability.GATEWAY_PAYMENTS,
                FinancialCapability.GATEWAY_SETTLEMENTS,
                FinancialCapability.REFUNDS,
                FinancialCapability.DISPUTES,
            },
            permissions=["read", "write_bounded"],
        )
        super().__init__(config)

    def check_health(self) -> ConnectorHealth:
        start = time.perf_counter()
        try:
            with SyncSessionLocal() as session:
                count = session.execute(select(func.count(RazorpayPaymentEvent.payment_id))).scalar() or 0
                webhook_count = session.execute(select(func.count(RazorpayWebhookLog.webhook_id))).scalar() or 0
                latency = (time.perf_counter() - start) * 1000.0
                return ConnectorHealth(
                    status="HEALTHY",
                    last_sync=datetime.now(timezone.utc).isoformat(),
                    records_count=count + webhook_count,
                    latency_ms=round(latency, 2),
                    message=f"Connected to Razorpay Gateway ({count} payments, {webhook_count} webhooks processed)",
                )
        except Exception as e:
            return ConnectorHealth(
                status="OFFLINE",
                last_sync=datetime.now(timezone.utc).isoformat(),
                message=f"Razorpay connector query failure: {str(e)}",
            )

    def get_payments(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalPayment]:
        self.require_capability(FinancialCapability.GATEWAY_PAYMENTS)
        with SyncSessionLocal() as session:
            stmt = select(RazorpayPaymentEvent).limit(limit)
            if filters and "status" in filters:
                stmt = stmt.where(RazorpayPaymentEvent.status == filters["status"])

            rows = session.execute(stmt).scalars().all()
            return [
                CanonicalPayment(
                    payment_id=p.payment_id,
                    counterparty_id=p.order_id,
                    amount=p.amount,
                    currency=p.currency,
                    payment_method=p.method or "GATEWAY",
                    payment_date=str(p.created_at),
                    status=p.status.upper(),
                    reference_number=p.payment_id,
                    source_system="Razorpay_Gateway_API",
                    source_connector=self.connector_id,
                    metadata={"fee": float(p.fee), "tax": float(p.tax), "order_id": p.order_id},
                )
                for p in rows
            ]

    def get_refunds(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalRefund]:
        self.require_capability(FinancialCapability.REFUNDS)
        with SyncSessionLocal() as session:
            stmt = select(RazorpayRefundEvent).limit(limit)
            rows = session.execute(stmt).scalars().all()
            return [
                CanonicalRefund(
                    refund_id=r.refund_id,
                    payment_id=r.payment_id,
                    amount=r.amount,
                    currency=r.currency,
                    status=r.status.upper(),
                    reason="Gateway initiated customer refund",
                    created_at=str(r.created_at),
                    source_system="Razorpay_Gateway_API",
                    source_connector=self.connector_id,
                )
                for r in rows
            ]

    def get_settlements(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalSettlement]:
        self.require_capability(FinancialCapability.GATEWAY_SETTLEMENTS)
        with SyncSessionLocal() as session:
            stmt = select(RazorpaySettlementEvent).limit(limit)
            rows = session.execute(stmt).scalars().all()
            return [
                CanonicalSettlement(
                    settlement_id=s.settlement_id,
                    gross_amount=s.gross_amount,
                    fee_amount=s.fee_amount,
                    tax_amount=s.tax_amount,
                    net_amount=s.net_amount,
                    currency=s.currency,
                    status=s.status.upper(),
                    settled_at=str(s.settled_at),
                    source_system="Razorpay_Merchant_Settlements",
                    source_connector=self.connector_id,
                )
                for s in rows
            ]

    def get_provenance_subgraph(self, primary_entity_type: str, primary_entity_id: str, max_hops: int = 3) -> dict[str, Any]:
        """Resolve relational provenance across Razorpay payment entities."""
        nodes = []
        edges = []
        evidence_ids = [primary_entity_id]

        with SyncSessionLocal() as session:
            pmt = session.execute(
                select(RazorpayPaymentEvent).where(RazorpayPaymentEvent.payment_id == primary_entity_id)
            ).scalar_one_or_none()

            if pmt:
                nodes.append({
                    "entity_type": "payment",
                    "entity_id": pmt.payment_id,
                    "source_connector": self.connector_id,
                    "data": {
                        "amount": float(pmt.amount),
                        "currency": pmt.currency,
                        "status": pmt.status,
                        "order_id": pmt.order_id,
                    }
                })

                # Check for refunds
                refunds = session.execute(
                    select(RazorpayRefundEvent).where(RazorpayRefundEvent.payment_id == pmt.payment_id)
                ).scalars().all()

                for ref in refunds:
                    evidence_ids.append(ref.refund_id)
                    nodes.append({
                        "entity_type": "refund",
                        "entity_id": ref.refund_id,
                        "source_connector": self.connector_id,
                        "data": {"amount": float(ref.amount), "status": ref.status},
                    })
                    edges.append({
                        "source": pmt.payment_id,
                        "target": ref.refund_id,
                        "relation": "has_refund",
                    })

        return {
            "root_entity": primary_entity_id,
            "evidence_count": len(nodes),
            "evidence_ids": evidence_ids,
            "nodes": nodes,
            "edges": edges,
        }
