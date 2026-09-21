"""Base Data Abstraction Layer & Financial Capability Discovery.

Defines the contract for external financial data sources. Connectors must explicitly
declare supported financial capabilities (Accounts Payable, General Ledger, Bank,
Gateway Settlements, etc.). Unsupported requests raise structured capability errors
rather than returning misleading empty sets or hallucinated records.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from core.domain.models import (
    CanonicalInvoice,
    CanonicalPurchaseOrder,
    CanonicalPayment,
    CanonicalBankTransaction,
    CanonicalGLEntry,
    CanonicalRefund,
    CanonicalSettlement,
    CanonicalDispute,
)


class FinancialCapability(str, Enum):
    ACCOUNTS_PAYABLE = "accounts_payable"        # POs, Invoices, Lines, Vendors
    DISBURSEMENTS = "disbursements"              # ERP payments, payment allocations
    BANK_RECONCILIATION = "bank_reconciliation"  # Bank statements, account transactions
    GENERAL_LEDGER = "general_ledger"            # Journal entries, debit/credit balancing
    GATEWAY_PAYMENTS = "gateway_payments"        # Payment gateway charges, orders, methods
    GATEWAY_SETTLEMENTS = "gateway_settlements"  # Batch settlements, gateway fees, taxes
    REFUNDS = "refunds"                          # Refunds, returns, partial credits
    DISPUTES = "disputes"                        # Chargebacks, vendor disputes, recoveries


class CapabilityNotSupportedError(Exception):
    """Raised when an agent or caller requests an operation unsupported by the connector."""
    def __init__(self, connector_id: str, capability: FinancialCapability, message: str | None = None):
        self.connector_id = connector_id
        self.capability = capability
        default_msg = (
            f"Financial capability '{capability.value}' is NOT supported by connector '{connector_id}'. "
            f"Enterprise schema does not expose this financial entity."
        )
        self.message = message or default_msg
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": "CAPABILITY_NOT_SUPPORTED",
            "connector_id": self.connector_id,
            "capability": self.capability.value,
            "message": self.message,
        }


@dataclass
class ConnectorHealth:
    status: str  # HEALTHY, DEGRADED, OFFLINE, UNKNOWN
    last_sync: str
    records_count: int = 0
    latency_ms: float = 0.0
    message: str = "Connector operational"


@dataclass
class ConnectorConfig:
    connector_id: str
    connector_name: str
    connector_type: str  # finrca, razorpay, postgresql, snowflake, bigquery
    environment: str     # benchmark, sandbox, test, production
    enabled: bool = True
    capabilities: set[FinancialCapability] = field(default_factory=set)
    permissions: list[str] = field(default_factory=lambda: ["read"])  # read, write_bounded
    health: ConnectorHealth = field(
        default_factory=lambda: ConnectorHealth(status="HEALTHY", last_sync="2026-09-21T10:00:00Z")
    )


class BaseFinancialAdapter(ABC):
    """Abstract Base Class for all LedgerOS enterprise financial connectors."""

    def __init__(self, config: ConnectorConfig):
        self.config = config

    @property
    def connector_id(self) -> str:
        return self.config.connector_id

    @property
    def connector_name(self) -> str:
        return self.config.connector_name

    @property
    def capabilities(self) -> set[FinancialCapability]:
        return self.config.capabilities

    def supports(self, capability: FinancialCapability) -> bool:
        """Determines whether this connector supports the requested financial domain concept."""
        return capability in self.config.capabilities

    def require_capability(self, capability: FinancialCapability) -> None:
        """Raises CapabilityNotSupportedError if this connector lacks the capability."""
        if not self.supports(capability):
            raise CapabilityNotSupportedError(self.connector_id, capability)

    @abstractmethod
    def check_health(self) -> ConnectorHealth:
        """Performs a live ping/query to verify connectivity."""
        pass

    # --- Accounts Payable ---
    def get_invoices(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalInvoice]:
        self.require_capability(FinancialCapability.ACCOUNTS_PAYABLE)
        raise NotImplementedError

    def get_purchase_orders(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalPurchaseOrder]:
        self.require_capability(FinancialCapability.ACCOUNTS_PAYABLE)
        raise NotImplementedError

    # --- Disbursements & Payments ---
    def get_payments(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalPayment]:
        if not (self.supports(FinancialCapability.DISBURSEMENTS) or self.supports(FinancialCapability.GATEWAY_PAYMENTS)):
            raise CapabilityNotSupportedError(self.connector_id, FinancialCapability.DISBURSEMENTS)
        raise NotImplementedError

    # --- Bank Reconciliation ---
    def get_bank_transactions(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalBankTransaction]:
        self.require_capability(FinancialCapability.BANK_RECONCILIATION)
        raise NotImplementedError

    # --- General Ledger ---
    def get_gl_entries(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalGLEntry]:
        self.require_capability(FinancialCapability.GENERAL_LEDGER)
        raise NotImplementedError

    # --- Gateway Settlements ---
    def get_settlements(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalSettlement]:
        self.require_capability(FinancialCapability.GATEWAY_SETTLEMENTS)
        raise NotImplementedError

    # --- Refunds ---
    def get_refunds(self, limit: int = 50, filters: Optional[dict[str, Any]] = None) -> list[CanonicalRefund]:
        self.require_capability(FinancialCapability.REFUNDS)
        raise NotImplementedError

    # --- Provenance Traversal ---
    @abstractmethod
    def get_provenance_subgraph(self, primary_entity_type: str, primary_entity_id: str, max_hops: int = 3) -> dict[str, Any]:
        """Traverse schema-directed relational links from the underlying data source."""
        pass
