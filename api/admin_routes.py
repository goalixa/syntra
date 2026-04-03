"""
Admin panel routes for Syntra.

Provides endpoints for the admin panel UI including authentication,
configuration management, and system monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import secrets
import hashlib

router = APIRouter()


# Models
class AuthRequest(BaseModel):
    """Authentication request model."""
    username: Optional[str] = None
    password: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response model."""
    token: str
    user: Dict[str, Any]


class ConfigUpdate(BaseModel):
    """Configuration update model."""
    model: Optional[str] = None
    namespace: Optional[str] = None
    timeout: Optional[int] = None
    debug: Optional[bool] = None
    systemPrompt: Optional[str] = None


class ActivityLog(BaseModel):
    """Activity log entry model."""
    timestamp: int
    level: str
    message: str
    agent: Optional[str] = None


class AgentStatus(BaseModel):
    """Agent status model."""
    name: str
    description: str
    status: str
    tasksCompleted: int
    successRate: float


# In-memory storage (replace with database in production)
admin_tokens: Dict[str, Dict[str, Any]] = {}
admin_config: Dict[str, Any] = {
    "model": "claude",
    "namespace": "production",
    "timeout": 300,
    "debug": False,
    "systemPrompt": ""
}
activity_logs: List[Dict[str, Any]] = []


def generate_token(user_data: Dict[str, Any]) -> str:
    """Generate a secure authentication token."""
    raw = f"{user_data['user_id']}:{secrets.token_hex(16)}:{datetime.now().isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_current_user(token: str) -> Dict[str, Any]:
    """Validate token and return current user."""
    if token not in admin_tokens:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_data = admin_tokens[token]

    # Check token age (24 hour expiry)
    token_age = (datetime.now() - datetime.fromisoformat(user_data['created_at'])).total_seconds()
    if token_age > 86400:
        del admin_tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")

    return user_data


# Routes
@router.post("/auth", response_model=AuthResponse)
async def authenticate(request: AuthRequest) -> AuthResponse:
    """
    Authenticate admin user.

    For demonstration purposes, this accepts any authentication request.
    In production, integrate with Goalixa Auth Service.
    """
    # Demo user - in production, validate against auth service
    user_data = {
        "user_id": "admin_001",
        "name": "Admin User",
        "email": "admin@syntra.devops",
        "role": "administrator",
        "created_at": datetime.now().isoformat()
    }

    token = generate_token(user_data)
    admin_tokens[token] = user_data

    # Log authentication
    add_log("SUCCESS", "Admin user authenticated", "System")

    return AuthResponse(
        token=token,
        user={
            "id": user_data["user_id"],
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data["role"]
        }
    )


@router.get("/overview")
async def get_overview() -> Dict[str, Any]:
    """Get dashboard overview statistics."""
    return {
        "totalTasks": 156,
        "taskGrowth": 12,
        "activeAgents": 4,
        "successRate": 98.5,
        "successRateChange": "+0.3%",
        "avgResponseTime": "2.3s",
        "responseTimeChange": "-0.2s",
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


@router.get("/agents")
async def get_agents() -> Dict[str, List[AgentStatus]]:
    """Get status of all Syntra agents."""
    return {
        "agents": [
            AgentStatus(
                name="Planner Agent",
                description="Breaks down complex tasks into executable steps",
                status="Active",
                tasksCompleted=45,
                successRate=98.0
            ),
            AgentStatus(
                name="DevOps Agent",
                description="Executes Kubernetes and infrastructure operations",
                status="Active",
                tasksCompleted=78,
                successRate=99.0
            ),
            AgentStatus(
                name="Reviewer Agent",
                description="Validates changes and provides feedback",
                status="Active",
                tasksCompleted=33,
                successRate=95.0
            ),
            AgentStatus(
                name="Evidence Collector",
                description="Gathers logs and diagnostic information",
                status="Active",
                tasksCompleted=56,
                successRate=100.0
            )
        ]
    }


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Get current Syntra configuration."""
    return admin_config.copy()


@router.post("/config")
async def update_config(config: ConfigUpdate) -> Dict[str, Any]:
    """Update Syntra configuration."""
    # Update only provided fields
    update_data = config.dict(exclude_unset=True)
    admin_config.update(update_data)

    add_log("INFO", f"Configuration updated: {', '.join(update_data.keys())}", "System")

    return admin_config.copy()


@router.get("/logs")
async def get_logs(limit: int = 50, level: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Get activity logs with optional filtering."""
    logs = activity_logs.copy()

    # Filter by level if specified
    if level:
        logs = [log for log in logs if log["level"] == level.upper()]

    # Sort by timestamp descending and limit
    logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

    return {"logs": logs}


def add_log(level: str, message: str, agent: Optional[str] = None) -> None:
    """Add a log entry."""
    log_entry = {
        "timestamp": int(datetime.now().timestamp() * 1000),
        "level": level.upper(),
        "message": message,
        "agent": agent
    }
    activity_logs.append(log_entry)

    # Keep only last 1000 logs
    if len(activity_logs) > 1000:
        activity_logs[:] = activity_logs[-1000:]


# Initialize with some sample logs
add_log("INFO", "Syntra admin panel initialized", "System")
add_log("SUCCESS", "All agents operational", "System")
add_log("INFO", "Connected to Kubernetes cluster", "DevOps Agent")
