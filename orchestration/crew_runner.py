"""
CrewAI orchestration layer for multi-agent incident response.

Coordinates Planner, Incident, and EvidenceCollector agents using CrewAI.
"""

import sys
import os
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crewai import Crew, Process, Task
from agents.planner_agent.planner_agent import PlannerAgent
from agents.incident_agent.incident_agent import IncidentAgent
from agents.evidence_collector.evidence_collector import EvidenceCollectorAgent


def run_ai_task(
    prompt: str,
    namespace: str = None,
    pod_name: str = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Run an AI task using the multi-agent crew.

    This is the main entry point for incident response operations.

    Args:
        prompt: User's request (e.g., "diagnose why my pod is crashing")
        namespace: Kubernetes namespace (if applicable)
        pod_name: Pod name (if applicable)
        context: Additional context for the task

    Returns:
        Dict with:
            - response: Summary of what was done
            - agent_used: Which agent handled the primary work
            - results: Detailed results from agents
            - metadata: Execution metadata
    """
    context = context or {}
    if namespace:
        context["namespace"] = namespace
    if pod_name:
        context["pod_name"] = pod_name

    # Initialize agents
    planner = PlannerAgent()
    incident = IncidentAgent()
    collector = EvidenceCollectorAgent()

    # Convert to CrewAI agents
    planner_crew = planner.to_crewai_agent()
    incident_crew = incident.to_crewai_agent()
    collector_crew = collector.to_crewai_agent()

    # Step 1: Plan the approach
    plan_result = planner.run(prompt, context)

    if plan_result["status"] == "error":
        return {
            "response": "Planning failed",
            "error": plan_result.get("error"),
            "agent_used": "planner"
        }

    # Check for missing required information
    if plan_result.get("required_info"):
        missing = ", ".join(plan_result["required_info"])
        return {
            "response": f"Missing required information: {missing}",
            "agent_used": "planner",
            "required_info": plan_result["required_info"],
            "hint": "Please provide namespace and pod_name for diagnosis"
        }

    # Step 2: Execute the plan based on intent
    intent = plan_result.get("intent", "general_help")

    if intent == "diagnose_pod":
        return _execute_diagnosis(prompt, context, collector, incident)
    elif intent == "namespace_overview":
        return _execute_overview(prompt, context, collector)
    elif intent == "collect_evidence":
        return _execute_evidence_collection(prompt, context, collector)
    else:
        return {
            "response": "Could not understand the request. Please specify what you'd like to do.",
            "agent_used": "planner",
            "hint": "Try: 'diagnose pod <pod-name> in namespace <namespace>'"
        }


def _execute_diagnosis(
    prompt: str,
    context: Dict[str, Any],
    collector: EvidenceCollectorAgent,
    incident: IncidentAgent
) -> Dict[str, Any]:
    """Execute pod diagnosis workflow."""
    namespace = context.get("namespace")
    pod_name = context.get("pod_name")

    # Collect evidence
    evidence_result = collector.run(
        "Collect evidence for diagnosis",
        {
            "namespace": namespace,
            "pod_name": pod_name,
            "log_lines": 200,
            "event_limit": 50
        }
    )

    if evidence_result["status"] == "error":
        return {
            "response": "Failed to collect evidence",
            "error": evidence_result.get("error"),
            "agent_used": "evidence_collector"
        }

    # Run incident analysis
    diagnosis_result = incident.run(
        prompt,
        {
            "namespace": namespace,
            "pod_name": pod_name,
            "evidence": evidence_result["evidence"]
        }
    )

    if diagnosis_result["status"] == "error":
        return {
            "response": "Failed to diagnose incident",
            "error": diagnosis_result.get("error"),
            "agent_used": "incident",
            "evidence": evidence_result.get("evidence")
        }

    # Format response
    return {
        "response": _format_diagnosis_response(diagnosis_result, evidence_result),
        "agent_used": "incident",
        "results": {
            "diagnosis": diagnosis_result,
            "evidence_metadata": evidence_result.get("metadata")
        },
        "metadata": {
            "method": diagnosis_result.get("method"),
            "confidence": diagnosis_result.get("confidence"),
            "incident_type": diagnosis_result.get("incident_type")
        }
    }


def _execute_overview(
    prompt: str,
    context: Dict[str, Any],
    collector: EvidenceCollectorAgent
) -> Dict[str, Any]:
    """Execute namespace overview workflow."""
    namespace = context.get("namespace")

    if not namespace:
        return {
            "response": "Missing namespace",
            "agent_used": "planner",
            "hint": "Please specify which namespace to overview"
        }

    overview_result = collector.collect_namespace_overview(namespace)

    if overview_result["status"] == "error":
        return {
            "response": "Failed to get namespace overview",
            "error": overview_result.get("error"),
            "agent_used": "evidence_collector"
        }

    overview = overview_result["overview"]

    return {
        "response": _format_overview_response(overview),
        "agent_used": "evidence_collector",
        "results": overview_result
    }


def _execute_evidence_collection(
    prompt: str,
    context: Dict[str, Any],
    collector: EvidenceCollectorAgent
) -> Dict[str, Any]:
    """Execute evidence collection workflow."""
    namespace = context.get("namespace")
    pod_name = context.get("pod_name")

    if not namespace or not pod_name:
        return {
            "response": "Missing namespace or pod_name",
            "agent_used": "planner",
            "hint": "Please specify both namespace and pod_name"
        }

    evidence_result = collector.run(
        prompt,
        {
            "namespace": namespace,
            "pod_name": pod_name,
            "log_lines": context.get("log_lines", 200),
            "event_limit": context.get("event_limit", 50),
            "include_related": context.get("include_related", False)
        }
    )

    if evidence_result["status"] == "error":
        return {
            "response": "Failed to collect evidence",
            "error": evidence_result.get("error"),
            "agent_used": "evidence_collector"
        }

    metadata = evidence_result.get("metadata", {})

    return {
        "response": (
            f"Collected evidence for {namespace}/{pod_name}:\n"
            f"- {metadata.get('log_lines_collected', 0)} log lines\n"
            f"- {metadata.get('events_collected', 0)} events\n"
            f"- {metadata.get('containers_count', 0)} containers"
        ),
        "agent_used": "evidence_collector",
        "results": evidence_result
    }


def _format_diagnosis_response(
    diagnosis: Dict[str, Any],
    evidence: Dict[str, Any]
) -> str:
    """Format diagnosis result into human-readable response."""
    incident_type = diagnosis.get("incident_type", "unknown")
    confidence = diagnosis.get("confidence", 0)
    remediation = diagnosis.get("remediation", "")
    method = diagnosis.get("method", "unknown")

    response_parts = [
        f"**Incident Type**: {incident_type}",
        f"**Confidence**: {confidence:.1%}",
        f"**Method**: {method}",
        f"",
        f"**Diagnosis**: {diagnosis.get('diagnosis', '')}",
        f"",
        f"**Remediation**: {remediation}"
    ]

    return "\n".join(response_parts)


def _format_overview_response(overview: Dict[str, Any]) -> str:
    """Format namespace overview into human-readable response."""
    parts = [
        f"**Namespace Overview**",
        f"",
        f"Total Pods: {overview.get('total', 0)}",
        f"Running: {len(overview.get('running', []))}",
        f"Pending: {len(overview.get('pending', []))}",
        f"Failed: {len(overview.get('failed', []))}",
        f"",
        f"**Issues Detected**: {len(overview.get('issues_detected', []))}"
    ]

    if overview.get("issues_detected"):
        parts.append("")
        for issue in overview["issues_detected"][:5]:  # Show first 5
            parts.append(f"- {issue['pod']}: {issue['issue']}")

    return "\n".join(parts)


def create_crew() -> Crew:
    """
    Create a CrewAI crew with all agents.

    This can be used for more complex multi-agent workflows
    that require CrewAI's process coordination.
    """
    planner = PlannerAgent()
    incident = IncidentAgent()
    collector = EvidenceCollectorAgent()

    return Crew(
        agents=[
            planner.to_crewai_agent(),
            incident.to_crewai_agent(),
            collector.to_crewai_agent()
        ],
        process=Process.sequential,
        verbose=True
    )

