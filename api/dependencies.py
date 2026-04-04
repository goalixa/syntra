"""
FastAPI dependencies for authentication and authorization.

Validates JWT tokens with the Goalixa Auth Service and provides user context.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from api.auth_client import auth_client

logger = logging.getLogger(__name__)

# Security scheme for Bearer token authentication
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token and return current user with Syntra profile.

    This dependency checks for a valid JWT token in the Authorization header
    or in cookies (goalixa_access). It validates the token with the auth service
    and returns the user with their Syntra role information.

    Returns:
        Dict with user info including Syntra role, or None if not authenticated

    Raises:
        HTTPException: If token is invalid but authentication is required
    """
    token = None

    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    # Fall back to cookie
    elif request.cookies:
        token = request.cookies.get("goalixa_access")

    if not token:
        return None

    # Validate token with auth service
    result = auth_client.syntra_validate_token(token)

    if not result.get("valid"):
        logger.warning(f"Invalid token: {result.get('error', 'Unknown error')}")
        return None

    return result.get("user")


async def require_auth(
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require authentication. Raises 401 if not authenticated.

    Use this dependency for endpoints that require a logged-in user.

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_admin(
    user: Dict[str, Any] = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Require admin role. Raises 403 if user is not an admin.

    Use this dependency for endpoints that require admin privileges.

    Raises:
        HTTPException: 403 if user is not an admin
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


async def require_operator(
    user: Dict[str, Any] = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Require operator or admin role.

    Use this dependency for endpoints that require operator-level access.

    Raises:
        HTTPException: 403 if user is not an operator or admin
    """
    if user.get("role") not in {"admin", "operator"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator or admin access required"
        )
    return user


def require_roles(*roles: str):
    """
    Factory function to create a dependency that requires specific roles.

    Args:
        *roles: Allowed roles (e.g., "admin", "operator", "viewer")

    Returns:
        Dependency function that checks for the required roles

    Example:
        @router.get("/admin-only")
        async def admin_endpoint(user: Dict = Depends(require_roles("admin"))):
            return {"message": "Welcome admin"}
    """
    async def role_checker(user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: one of {', '.join(roles)}"
            )
        return user

    return role_checker


async def optional_auth(
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns user if logged in, None otherwise.

    Use this for endpoints that work with or without authentication.
    """
    return user
