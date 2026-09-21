"""Finance Data Interface & Domain Tooling Layer for LedgerOS Agents.

Provides domain-level capabilities to LangGraph agents without exposing raw SQL
or coupling agent reasoning to company-specific database schemas. Routes all
requests through registered adapters and validates capability support.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from core.adapters.base import FinancialCapability, CapabilityNotSupportedError
from core.adapters.registry import adapter_registry
from core.domain.models import CanonicalInvoice, CanonicalPayment, CanonicalGLEntry


class FinanceDataInterface:
    """Domain-level data access interface used by AI investigation agents."""

    def __init__(self, registry=adapter_registry):
        self.registry = registry

    def get_invoices(self, vendor_id: Optional[str] = None, limit: int = 20) -> list[CanonicalInvoice]:
        """Fetch canonical invoices from authorized Accounts Payable adapters."""
        adapters = self.registry.find_adapters_with_capability(FinancialCapability.ACCOUNTS_PAYABLE)
        if not adapters:
            raise CapabilityNotSupportedError("GLOBAL", FinancialCapability.ACCOUNTS_PAYABLE)

        filters = {}
        if vendor_id:
            filters["vendor_id"] = vendor_id
        return adapters[0].get_invoices(limit=limit, filters=filters)

    def get_payments(self, limit: int = 20) -> list[CanonicalPayment]:
        """Fetch canonical payments from authorized payment/disbursement adapters."""
        adapters = self.registry.find_adapters_with_capability(FinancialCapability.DISBURSEMENTS)
        if not adapters:
            adapters = self.registry.find_adapters_with_capability(FinancialCapability.GATEWAY_PAYMENTS)
        if not adapters:
            raise CapabilityNotSupportedError("GLOBAL", FinancialCapability.DISBURSEMENTS)
        return adapters[0].get_payments(limit=limit)

    def get_provenance_evidence(self, entity_type: str, entity_id: str, max_hops: int = 3) -> dict[str, Any]:
        """Traverse relational accounting graph across available connectors."""
        # Check primary ERP/FinRCA adapter first
        adapters = self.registry.get_all_adapters()
        for ad in adapters:
            # Check if adapter supports relevant entity
            if entity_type in ["invoice", "po", "payment", "bank", "gl"] and ad.supports(FinancialCapability.ACCOUNTS_PAYABLE):
                return ad.get_provenance_subgraph(entity_type, entity_id, max_hops=max_hops)
            elif entity_type in ["charge", "refund", "settlement"] and ad.supports(FinancialCapability.GATEWAY_PAYMENTS):
                return ad.get_provenance_subgraph(entity_type, entity_id, max_hops=max_hops)

        # Fallback to first available adapter
        return adapters[0].get_provenance_subgraph(entity_type, entity_id, max_hops=max_hops)

    def verify_capability(self, capability: str) -> bool:
        """Query whether any connected data source provides this financial capability."""
        try:
            cap_enum = FinancialCapability(capability)
            return len(self.registry.find_adapters_with_capability(cap_enum)) > 0
        except ValueError:
            return False


finance_data_interface = FinanceDataInterface()
