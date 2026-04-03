"""
LLM tools for CrewAI agents.

Provides tool functions that agents can call to interact with Claude/LLM services.
"""

import sys
import os
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Note: llm_service will be implemented in Week 2
# For now, we provide a stub interface


async def diagnose_with_llm(
    pod_state: Dict[str, Any],
    logs: List[Dict[str, str]],
    events: List[Dict[str, Any]],
    context: str = ""
) -> Dict[str, Any]:
    """
    Use LLM (Claude) to analyze incident data and provide diagnosis.

    This tool will be implemented in Week 2 (Task 2.1).
    For now, returns a placeholder.

    Args:
        pod_state: Pod state dictionary
        logs: List of log entries
        events: List of event entries
        context: Additional context about the incident

    Returns:
        Dict with diagnosis, confidence, and recommendations

    Note:
        This is a placeholder. The actual implementation will call Claude API
        via services/llm_service.py once created.
    """
    # TODO: Implement in Week 2 (Task 2.1)
    # Will call: services.llm_service.diagnose(pod_state, logs, events, context)

    # Placeholder for now
    return {
        "diagnosis": "LLM diagnosis not yet implemented",
        "confidence": 0.0,
        "recommendation": "",
        "raw_response": ""
    }


def llm_available() -> bool:
    """
    Check if LLM service is available.

    Returns:
        True if LLM can be called, False otherwise
    """
    # TODO: Check if ANTHROPIC_API_KEY is configured
    return os.getenv("ANTHROPIC_API_KEY") is not None
