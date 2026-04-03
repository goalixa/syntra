"""
Syntra - AI DevOps Orchestration Service

FastAPI application entry point.
"""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import router as api_router
from api.admin_routes import router as admin_router
from config import settings
import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="AI-powered incident analysis and DevOps orchestration for Kubernetes"
)

# Configure CORS for API gateway integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Include admin routes
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
    """Root endpoint with service information and admin panel link."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "admin_panel": "👉 Access at: /admin",
        "api_docs": "👉 API docs at: /docs",
        "endpoints": {
            "POST /api/ask": "AI incident analysis",
            "GET /api/health": "Health check",
            "GET /admin": "Admin panel UI",
            "POST /api/admin/auth": "Admin authentication",
            "GET /api/admin/overview": "Admin dashboard overview",
            "GET /api/admin/agents": "Agent status",
            "GET /api/admin/config": "Get configuration",
            "POST /api/admin/config": "Update configuration",
            "GET /api/admin/logs": "Activity logs"
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
    print(f"{settings.PROJECT_NAME} v{settings.API_VERSION} starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print(f"{settings.PROJECT_NAME} shutting down...")
