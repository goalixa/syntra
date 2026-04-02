"""
API routes for Syntra incident analysis.
"""

from fastapi import APIRouter, HTTPException

from api.schemas import AIRequest, AIResponse
from orchestration.crew_runner import run_ai_task

router = APIRouter()


@router.post("/ask", response_model=AIResponse)
def ask_ai(request: AIRequest):
    """
    Main endpoint for AI-powered incident analysis.

    Accepts natural language requests and optionally Kubernetes context.
    Returns structured analysis results from the multi-agent system.
    """
    result = run_ai_task(
        prompt=request.prompt,
        namespace=request.namespace,
        pod_name=request.pod_name,
        context=request.context
    )

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
def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {"status": "healthy"}


@router.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "service": "Syntra AI DevOps Orchestrator",
        "version": "0.1.0-alpha",
        "endpoints": {
            "POST /api/ask": "AI incident analysis",
            "GET /api/health": "Health check"
        }
    }
