"""
Authentication Proxy Routes for Syntra

Proxies authentication requests to the Goalixa Auth Service
and manages JWT tokens for Syntra admin panel.
"""

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import requests
import os

from api.auth_client import auth_client

router = APIRouter()

# Auth service URL (can be overridden by environment)
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://goalixa-auth:5000")


class LoginRequest(BaseModel):
    """Login request model."""
    email: str
    password: str
    remember: Optional[bool] = False


class VerifyTokenRequest(BaseModel):
    """Token verification request."""
    token: str


# ============================================================
# Authentication Proxy Endpoints
# ============================================================

@router.post("/login")
async def login(request: Request, creds: LoginRequest):
    """
    Proxy login request to auth service.

    Sets HTTP-only cookies with tokens and returns user info.
    """
    try:
        # Call auth service login endpoint
        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/api/login",
            json={
                "email": creds.email,
                "password": creds.password
            },
            timeout=10
        )

        auth_response.raise_for_status()
        auth_data = auth_response.json()

        if not auth_data.get("success"):
            return auth_data

        # Create response with user data
        response_data = {
            "success": True,
            "user": auth_data.get("user"),
            "email_verified": auth_data.get("email_verified", False),
            "message": auth_data.get("message", "Login successful")
        }

        # Create response and set cookies from auth service
        response = Response(
            content=response_data,
            status_code=200,
            media_type="application/json"
        )

        # Copy cookies from auth service response
        for cookie_name in ["goalixa_access", "goalixa_refresh"]:
            if cookie_name in auth_response.cookies:
                cookie = auth_response.cookies[cookie_name]
                response.set_cookie(
                    key=cookie_name,
                    value=cookie.value,
                    expires=cookie.expires,
                    path=cookie.path,
                    domain=cookie.domain,
                    secure=cookie.secure,
                    httponly=cookie.httponly,
                    samesite=cookie.get('sameSite', 'lax')
                )

        return response

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Proxy token refresh request to auth service.
    """
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("goalixa_refresh")

        if not refresh_token:
            raise HTTPException(
                status_code=401,
                detail="No refresh token found"
            )

        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/api/refresh",
            json={"refresh_token": refresh_token},
            timeout=10
        )

        auth_response.raise_for_status()
        auth_data = auth_response.json()

        # Create response with new access token
        response_data = {
            "success": True,
            "access_token": auth_data.get("access_token")
        }

        response = Response(
            content=response_data,
            status_code=200,
            media_type="application/json"
        )

        # Update cookies from auth service
        for cookie_name in ["goalixa_access", "goalixa_refresh"]:
            if cookie_name in auth_response.cookies:
                cookie = auth_response.cookies[cookie_name]
                response.set_cookie(
                    key=cookie_name,
                    value=cookie.value,
                    expires=cookie.expires,
                    path=cookie.path,
                    domain=cookie.domain,
                    secure=cookie.secure,
                    httponly=cookie.httponly,
                    samesite=cookie.get('sameSite', 'lax')
                )

        return response

    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )


@router.post("/logout")
async def logout(request: Request):
    """
    Proxy logout request to auth service.
    Clears auth cookies.
    """
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("goalixa_refresh")

        # Call auth service logout if we have a refresh token
        if refresh_token:
            requests.post(
                f"{AUTH_SERVICE_URL}/api/logout",
                json={"refresh_token": refresh_token},
                timeout=10
            )

        # Create response that clears cookies
        response = Response(
            content='{"success": true}',
            status_code=200,
            media_type="application/json"
        )

        # Clear auth cookies
        for cookie_name in ["goalixa_access", "goalixa_refresh"]:
            response.delete_cookie(
                key=cookie_name,
                path="/",
                domain=".goalixa.com"  # Clear for all subdomains
            )

        return response

    except requests.RequestException:
        # Even if auth service fails, clear cookies
        response = Response(
            content='{"success": true}',
            status_code=200,
            media_type="application/json"
        )

        for cookie_name in ["goalixa_access", "goalixa_refresh"]:
            response.delete_cookie(
                key=cookie_name,
                path="/",
                domain=".goalixa.com"
            )

        return response


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user info.
    Proxies to auth service /api/me endpoint.
    """
    try:
        # Forward request to auth service with cookies
        cookies = {name: value.value for name, value in request.cookies.items()}

        auth_response = requests.get(
            f"{AUTH_SERVICE_URL}/api/me",
            cookies=cookies,
            timeout=10
        )

        auth_response.raise_for_status()
        return auth_response.json()

    except requests.RequestException as e:
        return {
            "authenticated": False,
            "user": None
        }


@router.post("/verify")
async def verify_token(token_req: VerifyTokenRequest):
    """
    Verify an access token and return user info.
    Used by frontend to check existing sessions.
    """
    user_info = auth_client.get_user_from_token(token_req.token)

    if user_info:
        return {
            "valid": True,
            "user": user_info
        }

    return {
        "valid": False,
        "user": None
    }


# ============================================================
# Session Management
# ============================================================

@router.get("/sessions")
async def get_sessions(request: Request):
    """
    Get all active sessions for current user.
    """
    try:
        access_token = request.cookies.get("goalixa_access")

        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )

        return auth_client.get_user_sessions(access_token)

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )


@router.post("/sessions/{token_id}/revoke")
async def revoke_session(request: Request, token_id: str):
    """
    Revoke a specific session.
    """
    try:
        access_token = request.cookies.get("goalixa_access")

        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )

        return auth_client.revoke_session(access_token, token_id)

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )


@router.post("/sessions/revoke-all")
async def revoke_all_sessions(request: Request):
    """
    Revoke all sessions except current.
    """
    try:
        access_token = request.cookies.get("goalixa_access")

        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )

        return auth_client.revoke_all_sessions(access_token)

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )

