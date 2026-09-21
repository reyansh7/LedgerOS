"""Tests for Data Abstraction Layer, FinRCA Adapter, Razorpay Adapter, and Capability Discovery."""

import pytest
from decimal import Decimal
from core.adapters.base import FinancialCapability, CapabilityNotSupportedError
from core.adapters.finrca_adapter import FinRCAAdapter
from core.adapters.razorpay_adapter import RazorpayAdapter
from core.adapters.registry import adapter_registry
from core.domain.models import CanonicalInvoice, CanonicalPayment, CanonicalGLEntry


def test_finrca_adapter_capabilities_and_data():
    adapter = FinRCAAdapter()

    # 1. Verify capability declarations
    assert adapter.supports(FinancialCapability.ACCOUNTS_PAYABLE) is True
    assert adapter.supports(FinancialCapability.DISBURSEMENTS) is True
    assert adapter.supports(FinancialCapability.BANK_RECONCILIATION) is True
    assert adapter.supports(FinancialCapability.GENERAL_LEDGER) is True
    assert adapter.supports(FinancialCapability.GATEWAY_SETTLEMENTS) is False
    assert adapter.supports(FinancialCapability.DISPUTES) is False

    # 2. Fetch canonical domain models
    invoices = adapter.get_invoices(limit=5)
    assert len(invoices) > 0
    assert isinstance(invoices[0], CanonicalInvoice)
    assert invoices[0].source_connector == adapter.connector_id
    assert isinstance(invoices[0].total_amount, Decimal)

    gl_entries = adapter.get_gl_entries(limit=5)
    assert len(gl_entries) > 0
    assert isinstance(gl_entries[0], CanonicalGLEntry)

    # 3. Reject unsupported operations with structured error
    with pytest.raises(CapabilityNotSupportedError) as exc_info:
        adapter.get_settlements()
    err = exc_info.value.to_dict()
    assert err["error"] == "CAPABILITY_NOT_SUPPORTED"
    assert err["capability"] == "gateway_settlements"


def test_razorpay_adapter_capabilities_and_rejections():
    adapter = RazorpayAdapter()

    # 1. Verify capability declarations
    assert adapter.supports(FinancialCapability.GATEWAY_PAYMENTS) is True
    assert adapter.supports(FinancialCapability.GATEWAY_SETTLEMENTS) is True
    assert adapter.supports(FinancialCapability.REFUNDS) is True
    assert adapter.supports(FinancialCapability.ACCOUNTS_PAYABLE) is False
    assert adapter.supports(FinancialCapability.GENERAL_LEDGER) is False

    # 2. Reject AP operations with structured error
    with pytest.raises(CapabilityNotSupportedError) as exc_info:
        adapter.get_invoices()
    assert exc_info.value.capability == FinancialCapability.ACCOUNTS_PAYABLE

    # 3. Reject GL operations with structured error
    with pytest.raises(CapabilityNotSupportedError) as exc_info:
        adapter.get_gl_entries()
    assert exc_info.value.capability == FinancialCapability.GENERAL_LEDGER


def test_adapter_registry_discovery():
    # 1. Discover capabilities across all connectors
    caps = adapter_registry.discover_capabilities()
    assert "FINRCA-BENCH-01" in caps
    assert "RAZORPAY-GATEWAY-01" in caps

    # 2. Query connectors supporting Accounts Payable
    ap_adapters = adapter_registry.find_adapters_with_capability(FinancialCapability.ACCOUNTS_PAYABLE)
    assert len(ap_adapters) == 1
    assert ap_adapters[0].connector_id == "FINRCA-BENCH-01"

    # 3. Operational health status summary
    status_list = adapter_registry.get_connectors_status()
    assert len(status_list) >= 2
    for s in status_list:
        assert s["health_status"] in ["HEALTHY", "DEGRADED", "OFFLINE"]
        assert len(s["capabilities"]) > 0
