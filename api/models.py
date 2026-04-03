"""
Data models for Syntra admin panel.

Defines user, access, and usage tracking models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles with different permission levels."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    OPERATOR = "operator"


class AuthProvider(str, Enum):
    """Authentication providers."""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    SAML = "saml"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseModel):
    """User model."""
    id: str
    email: str
    name: str
    role: UserRole
    status: UserStatus
    auth_provider: AuthProvider = AuthProvider.LOCAL
    created_at: datetime
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    permissions: List[str] = []


class UserCreate(BaseModel):
    """User creation model."""
    email: str
    name: str
    role: UserRole = UserRole.VIEWER
    password: Optional[str] = None
    department: Optional[str] = None
    permissions: List[str] = []


class UserUpdate(BaseModel):
    """User update model."""
    name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    department: Optional[str] = None
    permissions: Optional[List[str]] = None


class ApiKey(BaseModel):
    """API key model."""
    id: str
    user_id: str
    name: str
    key_prefix: str
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class ApiKeyCreate(BaseModel):
    """API key creation model."""
    name: str
    expires_in_days: Optional[int] = None


class UsageMetrics(BaseModel):
    """Usage metrics for a user."""
    user_id: str
    period: str  # daily, weekly, monthly
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    tokens_used: int
    cost_estimate: float
    breakdown: Dict[str, int]


class UsageRecord(BaseModel):
    """Individual usage record."""
    id: str
    user_id: str
    endpoint: str
    method: str
    status_code: int
    response_time: float
    tokens_used: int
    timestamp: datetime
    agent_used: Optional[str] = None


class AccessLog(BaseModel):
    """Access control log."""
    id: str
    user_id: str
    action: str
    resource: str
    granted: bool
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime


class SystemStats(BaseModel):
    """System-wide statistics."""
    total_users: int
    active_users: int
    total_requests_today: int
    total_requests_month: int
    avg_response_time: float
    error_rate: float
    active_sessions: int
    storage_used: float


class Permission(BaseModel):
    """Permission definition."""
    id: str
    name: str
    description: str
    category: str
    resource: str
    actions: List[str]


class RolePermissions(BaseModel):
    """Role with associated permissions."""
    role: UserRole
    permissions: List[str]
    description: str
