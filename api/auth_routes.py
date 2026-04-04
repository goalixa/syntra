"""
Authentication Proxy Routes for Syntra

Proxies authentication requests to the Goalixa Auth Service
and manages JWT tokens for Syntra admin panel.
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import requests
import os
import json

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
            return JSONResponse(content=auth_data, status_code=401)

        # Create response with user data
        response_data = {
            "success": True,
            "user": auth_data.get("user"),
            "email_verified": auth_data.get("email_verified", False),
            "message": auth_data.get("message", "Login successful")
        }

        # Create response and set cookies from auth service
        response = JSONResponse(
            content=response_data,
            status_code=200
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

        response = JSONResponse(
            content=response_data,
            status_code=200
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
        response = JSONResponse(
            content={"success": True},
            status_code=200
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
        response = JSONResponse(
            content={"success": True},
            status_code=200
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


# ============================================================
# Syntra-Specific Authentication Endpoints
# ============================================================

class SyntraLoginRequest(BaseModel):
    """Syntra login request model."""
    email: str
    password: str


class SyntraCreateUserRequest(BaseModel):
    """Syntra admin create user request model."""
    email: str
    password: str
    role: str = "operator"  # admin, operator, viewer
    department: Optional[str] = None


@router.post("/syntra/login")
async def syntra_login(creds: SyntraLoginRequest):
    """
    Syntra-specific login endpoint.

    Returns user with Syntra role information and JWT tokens.
    """
    try:
        # Call Syntra login endpoint on auth service
        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/api/syntra/login",
            json={
                "email": creds.email,
                "password": creds.password
            },
            timeout=10
        )

        auth_response.raise_for_status()
        auth_data = auth_response.json()

        if not auth_data.get("success"):
            return JSONResponse(content=auth_data, status_code=401)

        # Return success with user info and tokens
        response_data = {
            "success": True,
            "user": auth_data.get("user"),
            "access_token": auth_data.get("access_token"),
            "refresh_token": auth_data.get("refresh_token"),
        }

        response = JSONResponse(content=response_data)

        # Set cookies from auth service
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


@router.post("/syntra/validate")
async def syntra_validate_token(request: Request):
    """
    Validate Syntra JWT token and return user with Syntra profile.

    Expects Bearer token in Authorization header.
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid Authorization header"
            )

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Validate with auth service
        auth_response = requests.get(
            f"{AUTH_SERVICE_URL}/api/syntra/validate",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )

        auth_response.raise_for_status()
        return auth_response.json()

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )


@router.post("/syntra/admin/create-user")
async def syntra_create_user(user_req: SyntraCreateUserRequest, request: Request):
    """
    Create a new Syntra user via admin API.

    Requires X-Syntra-Admin-API-Key header for service-to-service communication.
    """
    try:
        # Forward request to auth service with admin key
        admin_key = os.getenv("SYNTRA_ADMIN_API_KEY", "")
        if not admin_key:
            raise HTTPException(
                status_code=500,
                detail="SYNTRA_ADMIN_API_KEY not configured"
            )

        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/api/syntra/admin/create-user",
            json={
                "email": user_req.email,
                "password": user_req.password,
                "role": user_req.role,
                "department": user_req.department
            },
            headers={"X-Syntra-Admin-API-Key": admin_key},
            timeout=10
        )

        auth_response.raise_for_status()
        return auth_response.json()

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )


@router.get("/syntra/users")
async def syntra_list_users(request: Request):
    """
    List all Syntra users.

    Requires admin role.
    """
    try:
        access_token = request.cookies.get("goalixa_access")
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )

        return auth_client.syntra_list_users(access_token)

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )


@router.get("/syntra/users/{user_id}")
async def syntra_get_user(user_id: int, request: Request):
    """
    Get a specific Syntra user by ID.

    Requires admin role or own user ID.
    """
    try:
        access_token = request.cookies.get("goalixa_access")
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )

        return auth_client.syntra_get_user(user_id, access_token)

    except requests.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Auth service unavailable: {str(e)}"
        )
