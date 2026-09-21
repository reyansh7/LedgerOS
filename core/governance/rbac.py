"""Role-Based Access Control (RBAC) for LedgerOS Financial Governance."""

from __future__ import annotations

from enum import Enum
from typing import Set


class UserRole(str, Enum):
    FINANCE_ANALYST = "FINANCE_ANALYST"
    FINANCE_CONTROLLER = "FINANCE_CONTROLLER"
    FINANCE_ADMIN = "FINANCE_ADMIN"
    AUDITOR = "AUDITOR"
    SYSTEM_AGENT = "SYSTEM_AGENT"


class Permission(str, Enum):
    INVESTIGATE = "investigate"
    READ_EVIDENCE = "read_evidence"
    APPROVE_ACTION = "approve_action"
    EXECUTE_ACTION = "execute_action"
    CONFIGURE_POLICY = "configure_policy"
    READ_AUDIT = "read_audit"
    VERIFY_AUDIT = "verify_audit"
    RUN_RECONCILIATION = "run_reconciliation"


ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.FINANCE_ANALYST: {
        Permission.INVESTIGATE,
        Permission.READ_EVIDENCE,
        Permission.READ_AUDIT,
    },
    UserRole.FINANCE_CONTROLLER: {
        Permission.INVESTIGATE,
        Permission.READ_EVIDENCE,
        Permission.APPROVE_ACTION,
        Permission.EXECUTE_ACTION,
        Permission.READ_AUDIT,
        Permission.VERIFY_AUDIT,
        Permission.RUN_RECONCILIATION,
    },
    UserRole.FINANCE_ADMIN: {
        Permission.INVESTIGATE,
        Permission.READ_EVIDENCE,
        Permission.APPROVE_ACTION,
        Permission.EXECUTE_ACTION,
        Permission.CONFIGURE_POLICY,
        Permission.READ_AUDIT,
        Permission.VERIFY_AUDIT,
        Permission.RUN_RECONCILIATION,
    },
    UserRole.AUDITOR: {
        Permission.READ_EVIDENCE,
        Permission.READ_AUDIT,
        Permission.VERIFY_AUDIT,
    },
    UserRole.SYSTEM_AGENT: {
        Permission.INVESTIGATE,
        Permission.READ_EVIDENCE,
        Permission.RUN_RECONCILIATION,
    },
}


class RBACManager:
    """Validates role permissions for financial actions and administrative operations."""

    @staticmethod
    def has_permission(role: UserRole | str, permission: Permission | str) -> bool:
        try:
            r = UserRole(role) if isinstance(role, str) else role
            p = Permission(permission) if isinstance(permission, str) else permission
            return p in ROLE_PERMISSIONS.get(r, set())
        except ValueError:
            return False

    @staticmethod
    def require_permission(role: UserRole | str, permission: Permission | str) -> None:
        if not RBACManager.has_permission(role, permission):
            raise PermissionError(
                f"Role '{role}' is not authorized to perform action requiring permission '{permission}'."
            )


rbac_manager = RBACManager()
