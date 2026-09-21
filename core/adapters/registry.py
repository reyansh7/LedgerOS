"""Financial Adapter Registry & Connector Discovery Manager.

Orchestrates multi-source connectors, routing financial capability requests
to the authorized and compatible adapters (FinRCA, Razorpay, Enterprise).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from core.adapters.base import (
    BaseFinancialAdapter,
    FinancialCapability,
    CapabilityNotSupportedError,
)
from core.adapters.finrca_adapter import FinRCAAdapter
from core.adapters.razorpay_adapter import RazorpayAdapter


class AdapterRegistry:
    """Central registry of configured financial connectors."""

    def __init__(self):
        self._adapters: dict[str, BaseFinancialAdapter] = {}
        # Pre-register default production adapters
        self.register(FinRCAAdapter())
        self.register(RazorpayAdapter())

    def register(self, adapter: BaseFinancialAdapter) -> None:
        self._adapters[adapter.connector_id] = adapter

    def get_adapter(self, connector_id: str) -> BaseFinancialAdapter:
        if connector_id not in self._adapters:
            raise KeyError(f"Connector '{connector_id}' is not registered in LedgerOS.")
        return self._adapters[connector_id]

    def get_all_adapters(self) -> list[BaseFinancialAdapter]:
        return list(self._adapters.values())

    def find_adapters_with_capability(self, capability: FinancialCapability) -> list[BaseFinancialAdapter]:
        """Discovers all active connectors that support a specific financial capability."""
        return [ad for ad in self._adapters.values() if ad.supports(capability)]

    def discover_capabilities(self) -> dict[str, list[str]]:
        """Maps each registered connector to its verified supported capabilities."""
        return {
            ad.connector_id: [cap.value for cap in ad.capabilities]
            for ad in self._adapters.values()
        }

    def get_connectors_status(self) -> list[dict[str, Any]]:
        """Provides operational health, capabilities, and permissions for all connectors."""
        statuses = []
        for ad in self._adapters.values():
            health = ad.check_health()
            statuses.append({
                "connector_id": ad.connector_id,
                "connector_name": ad.connector_name,
                "connector_type": ad.config.connector_type,
                "environment": ad.config.environment,
                "enabled": ad.config.enabled,
                "capabilities": [c.value for c in ad.capabilities],
                "permissions": ad.config.permissions,
                "health_status": health.status,
                "records_count": health.records_count,
                "latency_ms": health.latency_ms,
                "message": health.message,
                "last_sync": health.last_sync,
            })
        return statuses


# Global Singleton Registry
adapter_registry = AdapterRegistry()
