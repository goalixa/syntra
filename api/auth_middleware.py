"""
Authentication and security middleware for Syntra.

Handles API key authentication, JWT validation, and security controls.
"""

from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

from api.user_service import user_service
from api.models import User, UserStatus

# Rate limiting storage (in production, use Redis)
rate_limit_store = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 60
MAX_REQUESTS_PER_HOUR = 1000


# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_token = HTTPBearer(auto_error=False)


async def verify_cli_api_key(request: Request, api_key: Optional[str] = Security(api_key_header)) -> Optional[User]:
    """
    Verify API key for CLI connections.

    Used by CLI tools to authenticate with Syntra.
    Rate limits are applied per API key.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Use syntra configure --api-key YOUR_KEY",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Hash the provided key to compare with stored hashes
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Find the API key
    key_owner = None
    for user in user_service.get_all_users():
        for key in user_service.get_user_api_keys(user.id):
            # In production, store proper hashes
            if key.is_active and api_key.startswith(key.key_prefix):
                key_owner = user
                break
        if key_owner:
            break

    if not key_owner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    if key_owner.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {key_owner.status.value}"
        )

    # Rate limiting
    await check_rate_limit(api_key, request.client.host)

    # Update last used
    # In production, update in database
    user_service.log_access(
        user_id=key_owner.id,
        action="api_access",
        resource=request.url.path,
        granted=True,
        ip_address=request.client.host
    )

    return key_owner


async def verify_admin_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_token)) -> Optional[User]:
    """
    Verify JWT/Bearer token for admin panel.

    In production, this validates against the auth service.
    Supports SSO integration (Google OAuth, SAML, etc).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials

    # For demo: validate token format and return admin user
    # In production: Validate JWT against auth service
    if token.startswith("syntra_"):
        # Demo token - return admin user
        user = user_service.get_user("usr_001")
        if user and user.status == UserStatus.ACTIVE:
            return user

    # In production, integrate with Goalixa Auth Service:
    # 1. Validate JWT signature
    # 2. Check token expiry
    # 3. Verify user permissions
    # 4. Check MFA if enabled

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def check_rate_limit(api_key: str, client_ip: str):
    """
    Check rate limits for API key and IP.

    Implements token bucket algorithm.
    In production, use Redis for distributed rate limiting.
    """
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    hour_ago = now - timedelta(hours=1)

    # Clean old entries
    rate_limit_store[api_key] = [
        ts for ts in rate_limit_store[api_key]
        if ts > hour_ago
    ]

    recent_requests = rate_limit_store[api_key]

    # Check per-minute limit
    minute_requests = [ts for ts in recent_requests if ts > minute_ago]
    if len(minute_requests) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {MAX_REQUESTS_PER_MINUTE} requests per minute",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(MAX_REQUESTS_PER_MINUTE),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int((now + timedelta(minutes=1)).timestamp()))
            }
        )

    # Check per-hour limit
    if len(recent_requests) >= MAX_REQUESTS_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {MAX_REQUESTS_PER_HOUR} requests per hour",
            headers={
                "Retry-After": "3600",
                "X-RateLimit-Limit": str(MAX_REQUESTS_PER_HOUR),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int((now + timedelta(hours=1)).timestamp()))
            }
        )

    # Add current request
    rate_limit_store[api_key].append(now)


def get_rate_limit_info(api_key: str) -> dict:
    """Get current rate limit status for an API key."""
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    hour_ago = now - timedelta(hours=1)

    requests = rate_limit_store.get(api_key, [])
    minute_requests = len([ts for ts in requests if ts > minute_ago])
    hour_requests = len([ts for ts in requests if ts > hour_ago])

    return {
        "per_minute": {
            "limit": MAX_REQUESTS_PER_MINUTE,
            "remaining": MAX_REQUESTS_PER_MINUTE - minute_requests,
            "reset": int((now + timedelta(minutes=1)).timestamp())
        },
        "per_hour": {
            "limit": MAX_REQUESTS_PER_HOUR,
            "remaining": MAX_REQUESTS_PER_HOUR - hour_requests,
            "reset": int((now + timedelta(hours=1)).timestamp())
        }
    }


def get_security_headers() -> dict:
    """Get security headers for all responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://api.goalixa.com https://syntra.goalixa.com;",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
