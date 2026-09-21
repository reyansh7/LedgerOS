"""Test deterministic reconciliation engine on imported financial dataset."""

import pytest
from core.reconciliation.engine import reconciliation_engine


def test_reconciliation_engine():
    res = reconciliation_engine.run(dataset_scale="small")
    assert res["status"] == "completed"
    assert res["matched_records"] > 0
    assert res["total_exceptions"] > 0
    assert res["match_rate"] > 50.0
    assert "F01_DUPLICATE_INVOICE" in res["breakdown_by_failure"]
    assert "F02_PO_INVOICE_AMOUNT_MISMATCH" in res["breakdown_by_failure"]
    assert "F03_QUANTITY_MISMATCH" in res["breakdown_by_failure"]
