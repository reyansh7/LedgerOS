"""Tests for RBAC Permissions and Operating Guardrails."""

import pytest
from core.governance.rbac import RBACManager, UserRole, Permission
from core.governance.guardrails import get_active_guardrails


def test_rbac_role_permissions():
    # 1. Finance Controller permissions
    assert RBACManager.has_permission(UserRole.FINANCE_CONTROLLER, Permission.APPROVE_ACTION) is True
    assert RBACManager.has_permission(UserRole.FINANCE_CONTROLLER, Permission.EXECUTE_ACTION) is True
    assert RBACManager.has_permission(UserRole.FINANCE_CONTROLLER, Permission.RUN_RECONCILIATION) is True
    assert RBACManager.has_permission(UserRole.FINANCE_CONTROLLER, Permission.CONFIGURE_POLICY) is False

    # 2. Finance Analyst permissions
    assert RBACManager.has_permission(UserRole.FINANCE_ANALYST, Permission.INVESTIGATE) is True
    assert RBACManager.has_permission(UserRole.FINANCE_ANALYST, Permission.APPROVE_ACTION) is False
    assert RBACManager.has_permission(UserRole.FINANCE_ANALYST, Permission.EXECUTE_ACTION) is False

    # 3. Auditor permissions
    assert RBACManager.has_permission(UserRole.AUDITOR, Permission.READ_AUDIT) is True
    assert RBACManager.has_permission(UserRole.AUDITOR, Permission.VERIFY_AUDIT) is True
    assert RBACManager.has_permission(UserRole.AUDITOR, Permission.APPROVE_ACTION) is False

    # 4. Enforce PermissionError on unauthorized actions
    with pytest.raises(PermissionError):
        RBACManager.require_permission(UserRole.FINANCE_ANALYST, Permission.APPROVE_ACTION)


def test_active_guardrails_integrity():
    guardrails = get_active_guardrails()
    assert len(guardrails) >= 7
    ids = [g["guardrail_id"] for g in guardrails]
    assert "GR-01-PROVENANCE-EVIDENCE" in ids
    assert "GR-02-POLICY-BOUNDARIES" in ids
    assert "GR-03-HUMAN-APPROVAL-GATE" in ids
    assert "GR-04-POST-ACTION-INVARIANT" in ids
    assert "GR-05-IMMUTABLE-AUDIT-CHAIN" in ids
    assert "GR-06-RAW-SQL-PROHIBITION" in ids
    assert "GR-07-GROUND-TRUTH-FIREWALL" in ids
