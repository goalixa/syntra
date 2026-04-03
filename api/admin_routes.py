"""
Admin panel routes for Syntra.

Provides comprehensive endpoints for user management, access control,
configuration management, and system monitoring.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import secrets
import hashlib

from api.models import (
    User, UserCreate, UserUpdate, ApiKey, ApiKeyCreate,
    UsageMetrics, UsageRecord, AccessLog, SystemStats,
    UserRole, UserStatus, AuthProvider
)
from api.user_service import user_service

router = APIRouter()


# ============================================================
# AUTHENTICATION (Demo Mode)
# ============================================================

@router.post("/auth")
async def authenticate():
    """
    Authenticate admin user (demo mode).

    In production, integrate with Goalixa Auth Service.
    """
    user_data = {
        "user_id": "usr_001",
        "name": "Admin User",
        "email": "admin@syntra.devops",
        "role": UserRole.ADMIN,
        "created_at": datetime.now().isoformat()
    }

    token = hashlib.sha256(f"{user_data['user_id']}:{secrets.token_hex(16)}:{datetime.now().isoformat()}".encode()).hexdigest()

    user_service.log_access(
        user_id=user_data["user_id"],
        action="login",
        resource="admin_panel",
        granted=True
    )

    return {
        "token": token,
        "user": {
            "id": user_data["user_id"],
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data["role"]
        }
    }


# ============================================================
# SYSTEM OVERVIEW
# ============================================================

@router.get("/overview")
async def get_overview() -> Dict[str, Any]:
    """Get dashboard overview statistics."""
    stats = user_service.get_system_stats()

    return {
        "totalTasks": 156,
        "taskGrowth": 12,
        "activeAgents": 4,
        "successRate": 98.5,
        "successRateChange": "+0.3%",
        "avgResponseTime": f"{stats.avg_response_time:.1f}s",
        "responseTimeChange": "-0.2s",
        "totalUsers": stats.total_users,
        "activeUsers": stats.active_users,
        "totalRequestsToday": stats.total_requests_today,
        "recentActivity": [
            {
                "timestamp": datetime.now().timestamp() - 300,
                "message": "Deployed Core-API v1.2.3 to production",
                "agent": "DevOps Agent",
                "duration": "45s"
            },
            {
                "timestamp": datetime.now().timestamp() - 900,
                "message": "Investigated pod crash in auth-service",
                "agent": "Planner Agent",
                "duration": "2m 15s"
            },
            {
                "timestamp": datetime.now().timestamp() - 1800,
                "message": "Code review completed for PR #234",
                "agent": "Reviewer Agent",
                "duration": "1m 30s"
            }
        ]
    }


@router.get("/stats")
async def get_system_stats() -> SystemStats:
    """Get comprehensive system statistics."""
    return user_service.get_system_stats()


# ============================================================
# USER MANAGEMENT
# ============================================================

@router.get("/users")
async def get_users(
    status: Optional[UserStatus] = None,
    role: Optional[UserRole] = None,
    search: Optional[str] = None
) -> List[User]:
    """
    Get all users with optional filtering.

    - status: Filter by account status
    - role: Filter by role
    - search: Search by name or email
    """
    users = user_service.get_all_users()

    if status:
        users = [u for u in users if u.status == status]
    if role:
        users = [u for u in users if u.role == role]
    if search:
        search_lower = search.lower()
        users = [u for u in users if search_lower in u.name.lower() or search_lower in u.email.lower()]

    return users


@router.get("/users/{user_id}")
async def get_user(user_id: str) -> User:
    """Get user by ID."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users")
async def create_user(user_data: UserCreate) -> User:
    """Create a new user."""
    # Check if email already exists
    if user_service.get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    return user_service.create_user(user_data)


@router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate) -> User:
    """Update an existing user."""
    user = user_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}")
async def delete_user(user_id: str) -> Dict[str, str]:
    """Delete a user."""
    if not user_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/suspend")
async def suspend_user(user_id: str) -> User:
    """Suspend a user account."""
    user = user_service.suspend_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/activate")
async def activate_user(user_id: str) -> User:
    """Activate a suspended user account."""
    user = user_service.activate_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============================================================
# USER USAGE & ACTIVITY
# ============================================================

@router.get("/users/{user_id}/usage")
async def get_user_usage(
    user_id: str,
    period: str = Query("daily", enum=["daily", "weekly", "monthly"])
) -> UsageMetrics:
    """Get usage metrics for a specific user."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_service.get_user_usage(user_id, period)


@router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=500)
) -> List[UsageRecord]:
    """Get recent activity/usage records for a user."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_records = [r for r in user_service.usage_records if r.user_id == user_id]
    return sorted(user_records, key=lambda x: x.timestamp, reverse=True)[:limit]


@router.get("/users/{user_id}/access-logs")
async def get_user_access_logs(
    user_id: str,
    limit: int = Query(100, ge=1, le=500)
) -> List[AccessLog]:
    """Get access control logs for a user."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_service.get_access_logs(user_id=user_id, limit=limit)


# ============================================================
# API KEY MANAGEMENT
# ============================================================

@router.get("/users/{user_id}/api-keys")
async def get_user_api_keys(user_id: str) -> List[ApiKey]:
    """Get all API keys for a user."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_service.get_user_api_keys(user_id)


@router.post("/users/{user_id}/api-keys")
async def create_api_key(user_id: str, key_data: ApiKeyCreate) -> Dict[str, Any]:
    """Create a new API key for a user."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    api_key, raw_key = user_service.create_api_key(user_id, key_data)

    return {
        "api_key": api_key,
        "raw_key": raw_key  # Only shown once at creation
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str) -> Dict[str, str]:
    """Revoke an API key."""
    if not user_service.revoke_api_key(key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked successfully"}


# ============================================================
# AGENT MANAGEMENT
# ============================================================

@router.get("/agents")
async def get_agents() -> Dict[str, List[Dict[str, Any]]]:
    """Get status of all Syntra agents."""
    return {
        "agents": [
            {
                "id": "agent_001",
                "name": "Planner Agent",
                "description": "Breaks down complex tasks into executable steps",
                "status": "Active",
                "type": "planner",
                "tasksCompleted": 45,
                "successRate": 98.0,
                "avgResponseTime": 1.2,
                "lastActive": datetime.now().isoformat()
            },
            {
                "id": "agent_002",
                "name": "DevOps Agent",
                "description": "Executes Kubernetes and infrastructure operations",
                "status": "Active",
                "type": "executor",
                "tasksCompleted": 78,
                "successRate": 99.0,
                "avgResponseTime": 3.5,
                "lastActive": datetime.now().isoformat()
            },
            {
                "id": "agent_003",
                "name": "Reviewer Agent",
                "description": "Validates changes and provides feedback",
                "status": "Active",
                "type": "reviewer",
                "tasksCompleted": 33,
                "successRate": 95.0,
                "avgResponseTime": 2.1,
                "lastActive": datetime.now().isoformat()
            },
            {
                "id": "agent_004",
                "name": "Evidence Collector",
                "description": "Gathers logs and diagnostic information",
                "status": "Active",
                "type": "collector",
                "tasksCompleted": 56,
                "successRate": 100.0,
                "avgResponseTime": 0.8,
                "lastActive": datetime.now().isoformat()
            }
        ]
    }


# ============================================================
# CONFIGURATION MANAGEMENT
# ============================================================

# In-memory config storage
admin_config: Dict[str, Any] = {
    "model": "claude",
    "namespace": "production",
    "timeout": 300,
    "debug": False,
    "systemPrompt": "",
    "maxTokens": 4000,
    "temperature": 0.7,
    "rateLimits": {
        "requestsPerMinute": 60,
        "requestsPerDay": 1000
    }
}


class ConfigUpdate(BaseModel):
    """Configuration update model."""
    model: Optional[str] = None
    namespace: Optional[str] = None
    timeout: Optional[int] = None
    debug: Optional[bool] = None
    systemPrompt: Optional[str] = None
    maxTokens: Optional[int] = None
    temperature: Optional[float] = None


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Get current Syntra configuration."""
    return admin_config.copy()


@router.post("/config")
async def update_config(config: ConfigUpdate) -> Dict[str, Any]:
    """Update Syntra configuration."""
    update_data = config.dict(exclude_unset=True)
    admin_config.update(update_data)

    user_service.log_access(
        user_id="system",
        action="config_updated",
        resource="system_config",
        granted=True,
        reason=f"Updated: {', '.join(update_data.keys())}"
    )

    return admin_config.copy()


# ============================================================
# ACTIVITY LOGS
# ============================================================

activity_logs: List[Dict[str, Any]] = []


def add_log(level: str, message: str, agent: Optional[str] = None) -> None:
    """Add a system log entry."""
    log_entry = {
        "timestamp": int(datetime.now().timestamp() * 1000),
        "level": level.upper(),
        "message": message,
        "agent": agent
    }
    activity_logs.append(log_entry)

    if len(activity_logs) > 1000:
        activity_logs[:] = activity_logs[-1000:]


@router.get("/logs")
async def get_logs(
    limit: int = Query(50, ge=1, le=500),
    level: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Get system activity logs."""
    logs = activity_logs.copy()

    if level:
        logs = [log for log in logs if log["level"] == level.upper()]

    logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

    return {"logs": logs}


# ============================================================
# ACCESS CONTROL LOGS
# ============================================================

@router.get("/access-logs")
async def get_all_access_logs(
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[str] = None
) -> List[AccessLog]:
    """Get all access control logs."""
    return user_service.get_access_logs(user_id=user_id, limit=limit)


# Initialize with sample logs
add_log("INFO", "Syntra admin panel initialized", "System")
add_log("SUCCESS", "All agents operational", "System")
add_log("INFO", "Connected to Kubernetes cluster", "DevOps Agent")
