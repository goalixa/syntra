"""
Syntra - AI DevOps Orchestration Service

FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from config import settings

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


@app.get("/")
def root():
    """Root endpoint with service information."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "endpoints": {
            "POST /api/ask": "AI incident analysis",
            "GET /api/health": "Health check",
            "GET /": "Service information"
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
