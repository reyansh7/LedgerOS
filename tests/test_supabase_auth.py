"""Tests for Supabase JWT Authentication and Role-Based Access Control (RBAC) Enforcement."""

import time
import pytest
import jwt
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from core.governance.rbac import UserRole, Permission, RBACManager
from apps.api.auth import UserIdentity, resolve_role


def test_rbac_permissions_matrix():
    # Finance Controller must have approval and execution permissions
    assert RBACManager.has_permission(UserRole.FINANCE_CONTROLLER, Permission.APPROVE_ACTION) is True
    assert RBACManager.has_permission(UserRole.FINANCE_CONTROLLER, Permission.EXECUTE_ACTION) is True

    # Finance Analyst must NOT have approval or execution permission
    assert RBACManager.has_permission(UserRole.FINANCE_ANALYST, Permission.APPROVE_ACTION) is False
    assert RBACManager.has_permission(UserRole.FINANCE_ANALYST, Permission.EXECUTE_ACTION) is False
    assert RBACManager.has_permission(UserRole.FINANCE_ANALYST, Permission.READ_EVIDENCE) is True

    # Auditor has read-only audit permissions
    assert RBACManager.has_permission(UserRole.AUDITOR, Permission.READ_AUDIT) is True
    assert RBACManager.has_permission(UserRole.AUDITOR, Permission.APPROVE_ACTION) is False


def test_role_resolution_server_trusted():
    # Resolves uppercase and lowercase
    assert resolve_role("FINANCE_CONTROLLER") == UserRole.FINANCE_CONTROLLER
    assert resolve_role("finance_controller") == UserRole.FINANCE_CONTROLLER
    assert resolve_role("finance_analyst") == UserRole.FINANCE_ANALYST
    # Fallback to least privilege
    assert resolve_role(None) == UserRole.FINANCE_ANALYST
    assert resolve_role("unknown_custom_role") == UserRole.FINANCE_ANALYST


@pytest.mark.asyncio
async def test_approval_endpoint_blocks_unauthorized_role():
    """Verifies that an Analyst cannot approve a financial recovery action (HTTP 403)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Send approval request with Analyst role header
        resp = await client.post(
            "/api/approvals/APP_DUMMY_999/action",
            json={"verdict": "APPROVED", "comment": "Analyst attempting approval"},
            headers={"X-Dev-Role": "finance_analyst"},
        )
        assert resp.status_code == 403
        assert "not authorized" in resp.json()["detail"].lower() or "denied" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_approval_endpoint_allows_controller_role():
    """Verifies that a Controller role passes the RBAC check (reaches 404 for non-existent case, not 403)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Send approval request with Controller role header
        resp = await client.post(
            "/api/approvals/APP_DUMMY_999/action",
            json={"verdict": "APPROVED", "comment": "Controller approval"},
            headers={"X-Dev-Role": "finance_controller"},
        )
        # Should pass authorization (404 since APP_DUMMY_999 doesn't exist in DB, NOT 403 forbidden!)
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_approval_endpoint_rejects_malformed_bearer_token():
    """Verifies that a forged/malformed Bearer token is rejected with HTTP 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/approvals/APP_DUMMY_999/action",
            json={"verdict": "APPROVED", "comment": "Attacker payload"},
            headers={"Authorization": "Bearer forged.malformed.jwt.token"},
        )
        assert resp.status_code == 401
        assert "invalid" in resp.json()["detail"].lower() or "token" in resp.json()["detail"].lower()
