"""Tests for Enterprise Schema Mapping and Field Transforms."""

from decimal import Decimal
from core.adapters.mapping import (
    SchemaMappingEngine,
    EntityMapping,
    FieldMapping,
    enterprise_schema_mapper,
)


def test_schema_mapping_transforms_and_status():
    raw_external_invoice = {
        "inv_num": "ERP_INV_9921",
        "supp_id": "VEND_ACME_01",
        "gross_amt": "14500.50",
        "state": "approved",
    }

    canonical = enterprise_schema_mapper.map_record("invoice", raw_external_invoice)

    assert canonical["invoice_id"] == "ERP_INV_9921"
    assert canonical["vendor_id"] == "VEND_ACME_01"
    assert canonical["total_amount"] == Decimal("14500.50")
    assert isinstance(canonical["total_amount"], Decimal)
    assert canonical["status"] == "POSTED"


def test_custom_gateway_schema_mapping():
    mapper = SchemaMappingEngine()
    mapper.add_mapping(
        EntityMapping(
            external_table="custom_gateway_charge",
            canonical_entity="payment",
            fields={
                "payment_id": FieldMapping("ch_id", "payment_id"),
                "amount": FieldMapping("amount_cents", "amount", transform="divide_100"),
                "status": FieldMapping("charge_state", "status", transform="to_upper"),
            },
            status_mapping={"SUCCEEDED": "CLEARED"},
        )
    )

    raw_charge = {
        "ch_id": "ch_982182",
        "amount_cents": 50000,
        "charge_state": "succeeded",
    }

    mapped = mapper.map_record("payment", raw_charge)
    assert mapped["payment_id"] == "ch_982182"
    assert mapped["amount"] == Decimal("500.0")
    assert mapped["status"] == "CLEARED"
