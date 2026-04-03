"""
Syntra API package.

Contains all API routes and schemas for the Syntra service.
"""

from api.routes import router as api_router
from api.admin_routes import router as admin_router
from api.schemas import AIRequest, AIResponse

__all__ = ['api_router', 'admin_router', 'AIRequest', 'AIResponse']
