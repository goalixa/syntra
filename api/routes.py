"""
API routes for Syntra incident analysis.

Public API endpoints for CLI and third-party integration.
All endpoints require API key authentication.
"""

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.security import APIKeyHeader
from typing import Optional

from api.schemas import AIRequest, AIResponse
from api.auth_middleware import verify_cli_api_key, get_rate_limit_info
from orchestration.crew_runner import run_ai_task

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@router.post("/ask", response_model=AIResponse)
async def ask_ai(
    request: Request,
    ai_request: AIRequest,
    user: Optional[dict] = None  # Will be set by auth middleware in production
):
    """
    Main endpoint for AI-powered incident analysis.

    **Authentication**: Requires API key via X-API-Key header

    **Rate Limits**:
    - 60 requests per minute
    - 1000 requests per hour

    Example:
    ```
    curl -X POST https://api.goalixa.com/ask \\
      -H "X-API-Key: sk_your_key_here" \\
      -H "Content-Type: application/json" \\
      -d '{"prompt": "Check pod status in production"}'
    ```
    """
    # Verify API key
    authenticated_user = await verify_cli_api_key(request)

    result = run_ai_task(
        prompt=ai_request.prompt,
        namespace=ai_request.namespace,
        pod_name=ai_request.pod_name,
        context=ai_request.context
    )

    # Add rate limit info to response headers
    if hasattr(request.state, 'api_key'):
        rate_info = get_rate_limit_info(request.state.api_key)
        # Note: In production, add these as response headers

    # Check for error cases
    if "error" in result:
        return AIResponse(
            response=result.get("response", "An error occurred"),
            agent_used=result.get("agent_used", "unknown"),
            required_info=result.get("required_info"),
            hint=result.get("hint")
        )

    return AIResponse(
        response=result.get("response", ""),
        agent_used=result.get("agent_used", "unknown"),
        results=result.get("results"),
        metadata=result.get("metadata"),
        required_info=result.get("required_info"),
        hint=result.get("hint")
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes. No auth required."""
    return {"status": "healthy"}


@router.get("/")
async def root(request: Request):
    """Root endpoint with API information."""
    return {
        "service": "Syntra AI DevOps Orchestrator",
        "version": "0.1.0-alpha",
        "authentication": "API Key required (see: /api/docs)",
        "endpoints": {
            "POST /api/ask": "AI incident analysis (requires API key)",
            "GET /api/health": "Health check (no auth)",
            "GET /api/docs": "API documentation"
        },
        "documentation": {
            "api_keys": "Manage at: https://syntra.goalixa.com/admin",
            "rate_limits": "60 requests/minute, 1000 requests/hour",
            "cli_setup": "syntra configure --api-key YOUR_KEY"
        }
    }


@router.get("/rate-limit")
async def get_rate_limit_status(request: Request):
    """
    Check current rate limit status for your API key.

    Requires API key authentication.
    """
    authenticated_user = await verify_cli_api_key(request)

    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return get_rate_limit_info(api_key)

    return {"error": "API key required"}
