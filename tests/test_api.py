"""Test FastAPI REST endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app


@pytest.mark.asyncio
async def test_api_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_dashboard_stats():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "match_rate" in data
        assert "open_exceptions" in data


@pytest.mark.asyncio
async def test_exceptions_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/exceptions?limit=5")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)


@pytest.mark.asyncio
async def test_evaluations_run():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/evaluations/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "detection_recall_pct" in data
        assert "benchmark_ground_truth_total" in data
