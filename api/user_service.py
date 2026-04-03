"""
User management service for Syntra admin panel.

Handles user CRUD operations, authentication, access control,
and usage tracking.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import secrets
import hashlib

from api.models import (
    User, UserCreate, UserUpdate, ApiKey, ApiKeyCreate,
    UsageMetrics, UsageRecord, AccessLog, SystemStats,
    UserRole, UserStatus, AuthProvider
)


class UserService:
    """Service for managing users, access, and usage."""

    def __init__(self):
        # In-memory storage (replace with database in production)
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, ApiKey] = {}
        self.usage_records: List[UsageRecord] = []
        self.access_logs: List[AccessLog] = []

        # Initialize with demo users
        self._init_demo_users()

    def _init_demo_users(self):
        """Initialize with demo users for development."""
        demo_users = [
            User(
                id="usr_001",
                email="admin@syntra.devops",
                name="Admin User",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.LOCAL,
                created_at=datetime.now() - timedelta(days=90),
                last_login=datetime.now() - timedelta(hours=2),
                department="Platform",
                permissions=["*"]  # Full access
            ),
            User(
                id="usr_002",
                email="dev@syntra.devops",
                name="Developer User",
                role=UserRole.DEVELOPER,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.GOOGLE,
                created_at=datetime.now() - timedelta(days=45),
                last_login=datetime.now() - timedelta(minutes=30),
                department="Engineering",
                permissions=["tasks:read", "tasks:write", "agents:read", "config:read"]
            ),
            User(
                id="usr_003",
                email="ops@syntra.devops",
                name="Ops User",
                role=UserRole.OPERATOR,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.LOCAL,
                created_at=datetime.now() - timedelta(days=30),
                last_login=datetime.now() - timedelta(hours=6),
                department="Operations",
                permissions=["tasks:read", "tasks:write", "deploy:execute", "logs:read"]
            ),
            User(
                id="usr_004",
                email="viewer@syntra.devops",
                name="Viewer User",
                role=UserRole.VIEWER,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.LOCAL,
                created_at=datetime.now() - timedelta(days=15),
                last_login=datetime.now() - timedelta(days=1),
                department="Management",
                permissions=["tasks:read", "logs:read", "metrics:read"]
            ),
            User(
                id="usr_005",
                email="suspended@syntra.devops",
                name="Suspended User",
                role=UserRole.DEVELOPER,
                status=UserStatus.SUSPENDED,
                auth_provider=AuthProvider.LOCAL,
                created_at=datetime.now() - timedelta(days=60),
                last_login=datetime.now() - timedelta(days=7),
                department="Engineering",
                permissions=[]
            ),
        ]

        for user in demo_users:
            self.users[user.id] = user

        # Initialize with demo usage data
        self._init_demo_usage()

    def _init_demo_usage(self):
        """Initialize with demo usage records."""
        import random

        users = list(self.users.values())
        endpoints = ["/api/ask", "/api/admin/overview", "/api/admin/agents", "/api/admin/config"]
        agents = ["Planner Agent", "DevOps Agent", "Reviewer Agent"]

        # Generate usage for the last 7 days
        for i in range(500):
            user = random.choice(users)
            endpoint = random.choice(endpoints)

            record = UsageRecord(
                id=f"usage_{i}",
                user_id=user.id,
                endpoint=endpoint,
                method="POST" if endpoint == "/api/ask" else "GET",
                status_code=200 if random.random() > 0.05 else 500,
                response_time=random.uniform(0.5, 5.0),
                tokens_used=random.randint(100, 2000),
                timestamp=datetime.now() - timedelta(
                    days=random.randint(0, 7),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                ),
                agent_used=random.choice(agents) if endpoint == "/api/ask" else None
            )
            self.usage_records.append(record)

    # User Management
    def get_all_users(self) -> List[User]:
        """Get all users."""
        return list(self.users.values())

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user_id = f"usr_{secrets.token_hex(4)}"

        user = User(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            role=user_data.role,
            status=UserStatus.ACTIVE,
            auth_provider=AuthProvider.LOCAL,
            created_at=datetime.now(),
            department=user_data.department,
            permissions=user_data.permissions or self._get_default_permissions(user_data.role)
        )

        self.users[user_id] = user

        # Log the creation
        self.log_access(
            user_id="system",
            action="user_created",
            resource=f"user:{user_id}",
            granted=True,
            reason=f"User {user.email} created"
        )

        return user

    def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update an existing user."""
        user = self.users.get(user_id)
        if not user:
            return None

        update_data = user_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        # Log the update
        self.log_access(
            user_id="system",
            action="user_updated",
            resource=f"user:{user_id}",
            granted=True
        )

        return user

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id not in self.users:
            return False

        # Revoke all API keys
        for api_key in list(self.api_keys.values()):
            if api_key.user_id == user_id:
                del self.api_keys[api_key.id]

        del self.users[user_id]

        self.log_access(
            user_id="system",
            action="user_deleted",
            resource=f"user:{user_id}",
            granted=True
        )

        return True

    def suspend_user(self, user_id: str) -> Optional[User]:
        """Suspend a user account."""
        user = self.users.get(user_id)
        if user:
            user.status = UserStatus.SUSPENDED
            self.log_access(
                user_id="system",
                action="user_suspended",
                resource=f"user:{user_id}",
                granted=True
            )
        return user

    def activate_user(self, user_id: str) -> Optional[User]:
        """Activate a user account."""
        user = self.users.get(user_id)
        if user:
            user.status = UserStatus.ACTIVE
            self.log_access(
                user_id="system",
                action="user_activated",
                resource=f"user:{user_id}",
                granted=True
            )
        return user

    def _get_default_permissions(self, role: UserRole) -> List[str]:
        """Get default permissions for a role."""
        permissions_map = {
            UserRole.ADMIN: ["*"],
            UserRole.DEVELOPER: [
                "tasks:read", "tasks:write",
                "agents:read", "agents:execute",
                "config:read",
                "logs:read"
            ],
            UserRole.OPERATOR: [
                "tasks:read", "tasks:write",
                "deploy:execute",
                "logs:read"
            ],
            UserRole.VIEWER: [
                "tasks:read",
                "logs:read",
                "metrics:read"
            ]
        }
        return permissions_map.get(role, [])

    # API Key Management
    def create_api_key(self, user_id: str, key_data: ApiKeyCreate) -> tuple[ApiKey, str]:
        """Create a new API key."""
        raw_key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]

        api_key = ApiKey(
            id=f"key_{secrets.token_hex(4)}",
            user_id=user_id,
            name=key_data.name,
            key_prefix=key_prefix,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=key_data.expires_in_days) if key_data.expires_in_days else None,
            is_active=True
        )

        self.api_keys[api_key.id] = api_key

        return api_key, raw_key

    def get_user_api_keys(self, user_id: str) -> List[ApiKey]:
        """Get all API keys for a user."""
        return [k for k in self.api_keys.values() if k.user_id == user_id]

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id in self.api_keys:
            self.api_keys[key_id].is_active = False
            return True
        return False

    # Usage Tracking
    def record_usage(self, record: UsageRecord):
        """Record a usage event."""
        self.usage_records.append(record)

        # Keep only last 10000 records
        if len(self.usage_records) > 10000:
            self.usage_records = self.usage_records[-10000:]

    def get_user_usage(self, user_id: str, period: str = "daily") -> UsageMetrics:
        """Get usage metrics for a user."""
        now = datetime.now()

        if period == "daily":
            cutoff = now - timedelta(days=1)
        elif period == "weekly":
            cutoff = now - timedelta(weeks=1)
        else:  # monthly
            cutoff = now - timedelta(days=30)

        user_records = [
            r for r in self.usage_records
            if r.user_id == user_id and r.timestamp >= cutoff
        ]

        if not user_records:
            return UsageMetrics(
                user_id=user_id,
                period=period,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time=0.0,
                tokens_used=0,
                cost_estimate=0.0,
                breakdown={}
            )

        total = len(user_records)
        successful = sum(1 for r in user_records if r.status_code == 200)
        failed = total - successful
        avg_time = sum(r.response_time for r in user_records) / total
        tokens = sum(r.tokens_used for r in user_records)

        # Cost estimate (assume $0.0001 per 1K tokens)
        cost = (tokens / 1000) * 0.0001

        # Breakdown by endpoint
        breakdown = defaultdict(int)
        for r in user_records:
            breakdown[r.endpoint] += 1

        return UsageMetrics(
            user_id=user_id,
            period=period,
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            avg_response_time=round(avg_time, 2),
            tokens_used=tokens,
            cost_estimate=round(cost, 4),
            breakdown=dict(breakdown)
        )

    def get_all_usage_metrics(self, period: str = "daily") -> List[UsageMetrics]:
        """Get usage metrics for all users."""
        return [self.get_user_usage(user_id, period) for user_id in self.users.keys()]

    # Access Logging
    def log_access(self, user_id: str, action: str, resource: str,
                   granted: bool, reason: Optional[str] = None,
                   ip_address: Optional[str] = None):
        """Log an access control event."""
        log_entry = AccessLog(
            id=f"log_{secrets.token_hex(4)}",
            user_id=user_id,
            action=action,
            resource=resource,
            granted=granted,
            reason=reason,
            ip_address=ip_address,
            timestamp=datetime.now()
        )
        self.access_logs.append(log_entry)

        # Keep only last 1000 logs
        if len(self.access_logs) > 1000:
            self.access_logs = self.access_logs[-1000:]

    def get_access_logs(self, user_id: Optional[str] = None, limit: int = 100) -> List[AccessLog]:
        """Get access logs."""
        logs = self.access_logs

        if user_id:
            logs = [l for l in logs if l.user_id == user_id]

        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]

    # System Statistics
    def get_system_stats(self) -> SystemStats:
        """Get system-wide statistics."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        today_records = [r for r in self.usage_records if r.timestamp >= today_start]
        month_records = [r for r in self.usage_records if r.timestamp >= month_start]

        active_users = sum(
            1 for u in self.users.values()
            if u.status == UserStatus.ACTIVE and
            u.last_login and
            (now - u.last_login).days <= 7
        )

        return SystemStats(
            total_users=len(self.users),
            active_users=active_users,
            total_requests_today=len(today_records),
            total_requests_month=len(month_records),
            avg_response_time=sum(r.response_time for r in self.usage_records[-1000:]) / min(1000, len(self.usage_records)),
            error_rate=sum(1 for r in self.usage_records if r.status_code >= 400) / max(1, len(self.usage_records)),
            active_sessions=len([u for u in self.users.values() if u.status == UserStatus.ACTIVE]),
            storage_used=0.0  # Would calculate actual storage
        )


# Global user service instance
user_service = UserService()
