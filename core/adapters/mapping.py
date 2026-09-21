"""Enterprise Schema Mapping Engine.

Normalizes heterogeneous external table schemas, field names, currency codes,
and status strings into canonical LedgerOS domain representations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class FieldMapping:
    external_name: str
    canonical_name: str
    transform: Optional[str] = None  # to_decimal, to_upper, date_iso, divide_100


@dataclass
class EntityMapping:
    external_table: str
    canonical_entity: str
    fields: dict[str, FieldMapping] = field(default_factory=dict)
    status_mapping: dict[str, str] = field(default_factory=dict)


class SchemaMappingEngine:
    """Applies schema mapping configuration to raw external records."""

    def __init__(self, mappings: Optional[dict[str, EntityMapping]] = None):
        self.mappings: dict[str, EntityMapping] = mappings or {}

    def add_mapping(self, entity_mapping: EntityMapping) -> None:
        self.mappings[entity_mapping.canonical_entity] = entity_mapping

    def map_record(self, canonical_entity: str, raw_record: dict[str, Any]) -> dict[str, Any]:
        """Translates a raw external record into canonical field definitions."""
        mapping = self.mappings.get(canonical_entity)
        if not mapping:
            # Identity fallback if no specific mapping defined
            return dict(raw_record)

        result: dict[str, Any] = {}
        for canonical_field, f_map in mapping.fields.items():
            val = raw_record.get(f_map.external_name)
            if val is not None:
                if f_map.transform == "to_decimal":
                    val = Decimal(str(val))
                elif f_map.transform == "divide_100":
                    val = Decimal(str(val)) / Decimal("100.0")
                elif f_map.transform == "to_upper":
                    val = str(val).upper()
                result[canonical_field] = val

        # Handle status normalization
        if "status" in result and result["status"] in mapping.status_mapping:
            result["status"] = mapping.status_mapping[result["status"]]

        return result


# Pre-configured enterprise schema mappings
enterprise_schema_mapper = SchemaMappingEngine()

enterprise_schema_mapper.add_mapping(
    EntityMapping(
        external_table="erp_invoices",
        canonical_entity="invoice",
        fields={
            "invoice_id": FieldMapping("inv_num", "invoice_id"),
            "vendor_id": FieldMapping("supp_id", "vendor_id"),
            "total_amount": FieldMapping("gross_amt", "total_amount", transform="to_decimal"),
            "status": FieldMapping("state", "status", transform="to_upper"),
        },
        status_mapping={
            "OPEN": "PENDING",
            "APPROVED": "POSTED",
            "CLEARED": "PAID",
            "CANCELLED": "VOIDED",
        },
    )
)
