"""
API schemas for Syntra.

Request and response models for the incident analysis API.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    """Request model for AI-powered incident analysis."""
    prompt: str = Field(..., description="User's request or query")
    namespace: Optional[str] = Field(None, description="Kubernetes namespace")
    pod_name: Optional[str] = Field(None, description="Pod name to analyze")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class DiagnosisResult(BaseModel):
    """Diagnosis result from incident analysis."""
    incident_type: str = Field(..., description="Type of incident detected")
    confidence: float = Field(..., description="Confidence score (0-1)")
    diagnosis: str = Field(..., description="Root cause explanation")
    remediation: str = Field(..., description="Suggested fix")
    method: str = Field(..., description="Analysis method used")


class EvidenceMetadata(BaseModel):
    """Metadata about collected evidence."""
    namespace: str
    pod_name: str
    log_lines_collected: int
    events_collected: int
    containers_count: int


class AIResponse(BaseModel):
    """Response model for AI incident analysis."""
    response: str = Field(..., description="Human-readable summary")
    agent_used: str = Field(..., description="Which agent handled the request")
    results: Optional[Dict[str, Any]] = Field(None, description="Detailed results")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Execution metadata")
    required_info: Optional[list] = Field(None, description="Missing required information")
    hint: Optional[str] = Field(None, description="Hint for completing the request")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
