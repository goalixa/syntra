"""
Goalixa Auth Service Client

Handles authentication and user management via the centralized Goalixa Auth Service.
"""

import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import jwt


class AuthServiceClient:
    """Client for interacting with Goalixa Auth Service."""

    def __init__(self):
        self.auth_service_url = os.getenv(
            "AUTH_SERVICE_URL",
            "http://goalixa-auth:5000"  # Default for local development
        )
        self.jwt_secret = os.getenv("AUTH_JWT_SECRET", "your-jwt-secret")
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


# Global auth client instance
auth_client = AuthServiceClient()
