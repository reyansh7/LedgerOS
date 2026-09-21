"""Test FinRCA data importer and referential integrity."""

import pytest
from sqlalchemy import select
from core.database import SyncSessionLocal
from core.models.operational import Vendor, PurchaseOrder, Invoice, Payment, BankTransaction
from data.adapter.importer import import_finrca_dataset
from core.config import settings


def test_finrca_import():
    report = import_finrca_dataset(settings.finrca_data_dir)
    assert report["status"] == "success"
    assert report["imported_counts"]["vendors"] > 0
    assert report["imported_counts"]["purchase_orders"] > 0
    assert report["imported_counts"]["invoices"] > 0
    assert report["imported_counts"]["payments"] > 0
    assert report["imported_counts"]["bank_transactions"] > 0

    with SyncSessionLocal() as session:
        vendors = session.execute(select(Vendor)).scalars().all()
        assert len(vendors) >= 40
        invoices = session.execute(select(Invoice)).scalars().all()
        assert len(invoices) >= 200
