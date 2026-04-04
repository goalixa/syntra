"""
Goalixa Auth Service Client

Handles authentication and user management via the centralized Goalixa Auth Service.
"""

import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import jwt
import logging

logger = logging.getLogger(__name__)


class AuthServiceClient:
    """Client for interacting with Goalixa Auth Service."""

    def __init__(self):
        self.auth_service_url = os.getenv(
            "AUTH_SERVICE_URL",
            "http://goalixa-auth:5000"  # Default for local development
        )
        self.jwt_secret = os.getenv("AUTH_JWT_SECRET", "your-jwt-secret")
        self.syntra_admin_api_key = os.getenv("SYNTRA_ADMIN_API_KEY", "")
        self.api_timeout = 10  # seconds

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the auth service."""
        url = f"{self.auth_service_url}{endpoint}"
        kwargs.setdefault("timeout", self.api_timeout)

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Auth service unavailable: {str(e)}"
            }

    # ============================================================
    # Authentication Methods
    # ============================================================

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with email and password.

        Returns:
            Dict with success status, user info, and cookies
        """
        return self._make_request(
            "POST",
            "/api/login",
            json={"email": email, "password": password}
        )

    def logout(self, refresh_token: str) -> Dict[str, Any]:
        """
        Logout user and revoke refresh token.

        Args:
            refresh_token: The refresh token to revoke

        Returns:
            Dict with success status
        """
        return self._make_request(
            "POST",
            "/api/logout",
            json={"refresh_token": refresh_token}
        )

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            Dict with new access token
        """
        return self._make_request(
            "POST",
            "/api/refresh",
            json={"refresh_token": refresh_token}
        )

    # ============================================================
    # User Management
    # ============================================================

    def get_current_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get current user info from access token.

        Args:
            access_token: JWT access token

        Returns:
            User info dict or None if invalid
        """
        try:
            # Decode JWT without verification (auth service verifies)
            # In production, verify with auth service
            payload = jwt.decode(
                access_token,
                options={"verify_signature": False}
            )

            # Get full user info from auth service
            return self._make_request(
                "GET",
                "/api/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        except jwt.DecodeError:
            return None

    def get_user_sessions(self, access_token: str) -> Dict[str, Any]:
        """
        Get all active sessions for user.

        Args:
            access_token: JWT access token

        Returns:
            Dict with list of sessions
        """
        return self._make_request(
            "GET",
            "/api/sessions",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    def revoke_session(self, access_token: str, token_id: str) -> Dict[str, Any]:
        """
        Revoke a specific session.

        Args:
            access_token: JWT access token
            token_id: Session token ID to revoke

        Returns:
            Dict with success status
        """
        return self._make_request(
            "POST",
            f"/api/sessions/{token_id}/revoke",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    def revoke_all_sessions(self, access_token: str) -> Dict[str, Any]:
        """
        Revoke all sessions except current.

        Args:
            access_token: JWT access token

        Returns:
            Dict with success status
        """
        return self._make_request(
            "POST",
            "/api/sessions/revoke-all",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    # ============================================================
    # Token Validation (for other services)
    # ============================================================

    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an access token and return its payload.

        Args:
            token: JWT access token

        Returns:
            Token payload dict or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={"require": ["sub", "email", "type", "exp"]}
            )

            # Ensure it's an access token
            if payload.get("type") != "access":
                return None

            # Check expiration
            if payload.get("exp", 0) < datetime.now().timestamp():
                return None

            return payload

        except jwt.PyJWTError:
            return None

    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from access token.

        Args:
            token: JWT access token

        Returns:
            User info dict or None if invalid
        """
        payload = self.validate_access_token(token)
        if not payload:
            return None

        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "authenticated": True
        }

    # ============================================================
    # Syntra-Specific Methods
    # ============================================================

    def syntra_login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Syntra-specific login that returns user with role information.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with success status, tokens, and user with Syntra role
        """
        return self._make_request(
            "POST",
            "/api/syntra/login",
            json={"email": email, "password": password}
        )

    def syntra_validate_token(self, access_token: str) -> Dict[str, Any]:
        """
        Validate a Syntra JWT token with the auth service.

        Args:
            access_token: JWT access token

        Returns:
            Dict with valid status and user with Syntra profile
        """
        try:
            return self._make_request(
                "GET",
                "/api/syntra/validate",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        except requests.RequestException as e:
            logger.error(f"Syntra token validation failed: {e}")
            return {"valid": False, "error": str(e)}

    def syntra_create_user(
        self,
        email: str,
        password: str,
        role: str = "operator",
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Syntra user via admin API.

        Requires SYNTRA_ADMIN_API_KEY to be configured.

        Args:
            email: User email
            password: User password
            role: User role (admin, operator, viewer)
            department: Optional department

        Returns:
            Dict with created user info
        """
        headers = {}
        if self.syntra_admin_api_key:
            headers["X-Syntra-Admin-API-Key"] = self.syntra_admin_api_key
        else:
            logger.warning("SYNTRA_ADMIN_API_KEY not configured, user creation may fail")

        data = {
            "email": email,
            "password": password,
            "role": role
        }
        if department:
            data["department"] = department

        return self._make_request(
            "POST",
            "/api/syntra/admin/create-user",
            json=data,
            headers=headers
        )

    def syntra_list_users(self, access_token: str) -> Dict[str, Any]:
        """
        List all Syntra users (admin only).

        Args:
            access_token: Admin JWT access token

        Returns:
            Dict with list of Syntra users
        """
        return self._make_request(
            "GET",
            "/api/syntra/users",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    def syntra_get_user(self, user_id: int, access_token: str) -> Dict[str, Any]:
        """
        Get a specific Syntra user by ID.

        Args:
            user_id: User ID to fetch
            access_token: JWT access token

        Returns:
            Dict with user info
        """
        return self._make_request(
            "GET",
            f"/api/syntra/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    def syntra_update_user(
        self,
        user_id: int,
        access_token: str,
        role: Optional[str] = None,
        department: Optional[str] = None,
        active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update a Syntra user's profile (admin only).

        Args:
            user_id: User ID to update
            access_token: Admin JWT access token
            role: New role (optional)
            department: New department (optional)
            active: Active status (optional)

        Returns:
            Dict with updated user info
        """
        data = {}
        if role is not None:
            data["role"] = role
        if department is not None:
            data["department"] = department
        if active is not None:
            data["active"] = active

        return self._make_request(
            "PATCH",
            f"/api/syntra/users/{user_id}",
            json=data,
            headers={"Authorization": f"Bearer {access_token}"}
        )


# Global auth client instance
auth_client = AuthServiceClient()
