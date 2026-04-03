"""
Syntra API package.

Contains all API routes, schemas, and services for the Syntra service.
"""

from api.routes import router as api_router
from api.admin_routes import router as admin_router
from api.schemas import AIRequest, AIResponse
from api.user_service import user_service
from api.models import User, UserRole, UserStatus, AuthProvider

__all__ = [
    'api_router',
    'admin_router',
    'AIRequest',
    'AIResponse',
    'user_service',
    'User',
    'UserRole',
    'UserStatus',
    'AuthProvider'
]
