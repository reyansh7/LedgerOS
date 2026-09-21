"""Supabase JWT Authentication & Role-Based Access Control (RBAC) Dependency."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass
from fastapi import Depends, HTTPException, Header, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from core.config import settings
from core.governance.rbac import RBACManager, UserRole, Permission

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)

# Cached PyJWKClient instance for fetching and caching Supabase signing keys
_jwks_client: Optional[jwt.PyJWKClient] = None


def get_jwks_client() -> Optional[jwt.PyJWKClient]:
    global _jwks_client
    if _jwks_client is None and settings.supabase_jwks_url:
        _jwks_client = jwt.PyJWKClient(settings.supabase_jwks_url, cache_jwk_set=True, lifespan=3600)
    return _jwks_client


@dataclass
class UserIdentity:
    user_id: str
    email: str
    role: UserRole
    claims: dict[str, Any]


def resolve_role(role_str: Optional[str]) -> UserRole:
    """Safely converts string to UserRole enum (case-insensitive)."""
    if not role_str:
        return UserRole.FINANCE_ANALYST
    norm = role_str.strip().upper()
    for r in UserRole:
        if r.value == norm or r.name == norm:
            return r
    return UserRole.FINANCE_ANALYST


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    x_dev_role: Optional[str] = Header(None, alias="X-Dev-Role"),
) -> UserIdentity:
    """
    Authenticates caller via Supabase JWT or authorized development identity.
    Enforces the security chain:
      Authorization: Bearer <JWT>
              ↓
      Verify JWT signature & algorithm
              ↓
      Validate issuer (if configured)
              ↓
      Validate audience (authenticated)
              ↓
      Validate expiration
              ↓
      Extract authenticated user ID (sub)
              ↓
      Extract server-trusted role (app_metadata only - never client user_metadata)
              ↓
      Apply RBAC
    """
    token = credentials.credentials if credentials else None

    # 1. When JWT is provided, verify against Supabase JWKS or secret
    if token:
        jwks = get_jwks_client()
        expected_issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else None
        
        try:
            # If JWKS URL configured, fetch public key dynamically
            if jwks:
                signing_key = jwks.get_signing_key_from_jwt(token)
                key = signing_key.key
                algorithms = ["RS256", "ES256"]
            elif settings.supabase_secret_key:
                # Fallback to Supabase JWT secret HMAC verification
                key = settings.supabase_secret_key
                algorithms = ["HS256"]
            else:
                # Token provided but no verification key available
                raise HTTPException(
                    status_code=401,
                    detail="Supabase JWKS/Secret not configured to verify incoming Bearer token.",
                )

            decode_kwargs: dict[str, Any] = {
                "algorithms": algorithms,
                "audience": "authenticated",
                "options": {"verify_exp": True, "verify_aud": True},
            }
            if expected_issuer:
                decode_kwargs["issuer"] = expected_issuer
                decode_kwargs["options"]["verify_iss"] = True

            claims = jwt.decode(token, key, **decode_kwargs)

            user_id = claims.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing required subject ('sub').")

            email = claims.get("email", "")

            # Security Rule: Resolve role exclusively from server-controlled app_metadata.
            # Never trust user_metadata as it can be modified by end users.
            server_role_str = claims.get("app_metadata", {}).get("role")
            role = resolve_role(server_role_str)

            return UserIdentity(user_id=user_id, email=email, role=role, claims=claims)

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Authentication token has expired.")
        except jwt.InvalidIssuerError:
            raise HTTPException(status_code=401, detail="Token issuer does not match Supabase auth service.")
        except jwt.InvalidAudienceError:
            raise HTTPException(status_code=401, detail="Token audience is invalid; must be 'authenticated'.")
        except jwt.PyJWTError as e:
            logger.warning(f"Supabase JWT validation error: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

    # 2. In development / test mode without token, provide structured dev identity
    if settings.env in ["development", "test"]:
        dev_role = resolve_role(x_dev_role) if x_dev_role else UserRole.FINANCE_CONTROLLER
        return UserIdentity(
            user_id="usr_dev_controller_01",
            email="controller@ledgeros.local",
            role=dev_role,
            claims={"sub": "usr_dev_controller_01", "role": dev_role.value},
        )

    # 3. Production requirement
    raise HTTPException(status_code=401, detail="Missing authorization header (Bearer token required).")


def require_role(required_role: UserRole):
    """FastAPI dependency enforcing a specific UserRole."""
    async def role_checker(user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
        if user.role != required_role and user.role != UserRole.FINANCE_ADMIN:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {required_role.value}. User role: {user.role.value}.",
            )
        return user
    return role_checker


def require_permission(permission: Permission):
    """FastAPI dependency enforcing specific operational permission via RBAC."""
    async def perm_checker(user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
        try:
            RBACManager.require_permission(user.role, permission)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        return user
    return perm_checker
