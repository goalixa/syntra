"""
Syntra - AI DevOps Orchestration Service

FastAPI application entry point with security middleware.
"""

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os

from api.routes import router as api_router
from api.admin_routes import router as admin_router
from api.auth_middleware import get_security_headers
from config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="AI-powered incident analysis and DevOps orchestration for Kubernetes"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        for header, value in get_security_headers().items():
            response.headers[header] = value

        return response


# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS for API gateway integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://syntra.goalixa.com",
        "https://api.goalixa.com",
        "http://localhost:8000",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After"]
)

# Include API routes (public API with API key auth)
app.include_router(api_router, prefix="/api")

# Include admin routes (admin panel with token auth)
app.include_router(admin_router, prefix="/api/admin")

# Mount static files for admin panel (CSS, JS)
app.mount("/admin/static", StaticFiles(directory="admin/static"), name="admin_static")


@app.get("/admin")
@app.get("/admin/")
async def admin_panel():
    """Serve the admin panel index.html."""
    index_path = os.path.join("admin/static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return Response(content="Admin panel not found", status_code=404)


@app.get("/")
def root():
    """Root endpoint with service information."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "admin_panel": "👉 https://syntra.goalixa.com/admin",
        "api_endpoint": "👉 https://api.goalixa.com/api",
        "api_docs": "👉 https://api.goalixa.com/docs",
        "authentication": {
            "admin_panel": "SSO + MFA (in production)",
            "cli_api": "API Key via X-API-Key header"
        },
        "endpoints": {
            "POST /api/ask": "AI incident analysis (requires API key)",
            "GET /api/health": "Health check (no auth)",
            "GET /api/rate-limit": "Check rate limit status",
            "GET /admin": "Admin panel UI",
            "POST /api/admin/auth": "Admin authentication"
        }
    }


@app.get("/health")
def health():
    """Health check endpoint for Kubernetes probes."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   🚀 {settings.PROJECT_NAME} v{settings.API_VERSION}                    ║
║                                                            ║
║   Admin Panel: https://syntra.goalixa.com/admin         ║
║   API Endpoint: https://api.goalixa.com/api             ║
║   API Docs:    https://api.goalixa.com/docs             ║
║                                                            ║
║   ✅ Security headers enabled                             ║
║   ✅ Rate limiting active                                 ║
║   ✅ API key authentication                               ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print(f"{settings.PROJECT_NAME} shutting down...")
