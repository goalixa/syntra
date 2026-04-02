"""
IncidentAgent module - Analyzes and diagnoses Kubernetes incidents.

This agent specializes in identifying root causes of pod failures,
crashes, and performance issues using rule-based detection and LLM analysis.
"""

import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.base_agent import BaseAgent
from agents.tools.rule_tools import classify_incident, get_rule_based_diagnosis
from agents.tools.llm_tools import diagnose_with_llm, llm_available


class IncidentAgent(BaseAgent):
    """
    Agent responsible for analyzing Kubernetes incidents.

    Uses a hybrid approach:
    1. Rule-based detection for fast, high-confidence common patterns
    2. LLM analysis for complex or unknown issues

    Threshold: Falls back to LLM if rule-based confidence < 70%
    """

    def __init__(self):
        super().__init__(
            name="incident",
            role="Kubernetes Incident Analyzer",
            goal="Diagnose root cause of pod failures, crashes, and performance issues from pod state, logs, and events",
            backstory="You are a senior DevOps engineer with 10+ years of experience debugging Kubernetes clusters. You've seen every failure mode - OOM kills, crash loops, image pull errors, network issues, and mysterious deadlocks. You know that the fastest path to resolution is combining pattern matching with deep analysis."
        )
        self.confidence_threshold = 0.70  # 70% threshold for LLM fallback

    def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze an incident and provide diagnosis.

        Args:
            task: Description of the incident (e.g., "diagnose pod my-app-123 in namespace production")
            context: Additional context including:
                - namespace: Kubernetes namespace
                - pod_name: Pod to analyze
                - force_llm: Skip rules, go straight to LLM
                - evidence: Pre-gathered evidence (logs, events, pod_state)

        Returns:
            Dict with:
                - diagnosis: Root cause explanation
                - confidence: 0.0-1.0 score
                - incident_type: Type of incident (oom, crash_loop, etc.)
                - evidence: Supporting evidence
                - remediation: Suggested fix
                - method: "rule_based" or "llm"
        """
        context = context or {}

        # Extract parameters
        namespace = context.get("namespace")
        pod_name = context.get("pod_name")
        force_llm = context.get("force_llm", False)

        if not namespace or not pod_name:
            return self._error_response("Missing required context: namespace and pod_name")

        try:
            # Phase 1: Rule-based classification (fast, deterministic)
            if not force_llm:
                rule_result = get_rule_based_diagnosis(namespace, pod_name)

                # High confidence rule match? Return immediately
                if rule_result["confidence"] >= self.confidence_threshold:
                    return {
                        "status": "success",
                        "method": "rule_based",
                        "diagnosis": rule_result["primary_detection"].get("remediation", "Incident detected"),
                        "confidence": rule_result["confidence"],
                        "incident_type": rule_result["incident_type"],
                        "evidence": {
                            "details": rule_result["primary_detection"].get("details", []),
                            "affected_containers": rule_result["primary_detection"].get("affected_containers", [])
                        },
                        "remediation": rule_result.get("remediation", "Requires investigation"),
                        "raw_result": rule_result
                    }

            # Phase 2: LLM analysis (for complex or low-confidence cases)
            if llm_available():
                # Gather evidence if not provided
                if "evidence" not in context:
                    from agents.tools.k8s_tools import get_pod_details, fetch_pod_logs, fetch_events

                    pod_state = get_pod_details(namespace, pod_name)
                    logs = fetch_pod_logs(namespace, pod_name, tail_lines=200)
                    events = fetch_events(namespace, pod_name, limit=50)

                    evidence = {
                        "pod_state": pod_state,
                        "logs": logs,
                        "events": events
                    }
                else:
                    evidence = context["evidence"]

                # Call LLM for diagnosis
                llm_result = diagnose_with_llm(
                    pod_state=evidence.get("pod_state", {}),
                    logs=evidence.get("logs", []),
                    events=evidence.get("events", []),
                    context=task
                )

                return {
                    "status": "success",
                    "method": "llm",
                    "diagnosis": llm_result.get("diagnosis", "Analysis complete"),
                    "confidence": llm_result.get("confidence", 0.5),
                    "incident_type": llm_result.get("incident_type", "unknown"),
                    "evidence": evidence,
                    "remediation": llm_result.get("recommendation", "Requires further investigation"),
                    "raw_result": llm_result
                }

            # No LLM available, return best rule result
            if not force_llm:
                rule_result = get_rule_based_diagnosis(namespace, pod_name)
                return {
                    "status": "success",
                    "method": "rule_based_fallback",
                    "diagnosis": rule_result["primary_detection"].get("remediation", "Pattern detected"),
                    "confidence": rule_result["confidence"],
                    "incident_type": rule_result["incident_type"],
                    "evidence": {
                        "details": rule_result["primary_detection"].get("details", []),
                        "affected_containers": rule_result["primary_detection"].get("affected_containers", [])
                    },
                    "remediation": rule_result.get("remediation", "Requires investigation"),
                    "raw_result": rule_result
                }

            # Nothing worked
            return self._error_response("No diagnosis methods available - LLM not configured and no rules matched")

        except Exception as e:
            return self._error_response(f"Analysis failed: {str(e)}")

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Format an error response."""
        return {
            "status": "error",
            "error": message,
            "confidence": 0.0,
            "method": "none"
        }

    def classify_from_evidence(
        self,
        pod_state: Dict[str, Any],
        logs: list,
        events: list
    ) -> Dict[str, Any]:
        """
        Classify incident from pre-gathered evidence.

        Useful when evidence has been collected by EvidenceCollectorAgent.

        Args:
            pod_state: Pod state dictionary
            logs: List of log entries
            events: List of event entries

        Returns:
            Classification result with incident type and confidence
        """
        # Use rule-based classification
        result = classify_incident(pod_state, logs)

        return {
            "incident_type": result["incident_type"],
            "confidence": result["confidence"],
            "detection_method": result["detection_method"],
            "primary_detection": result["primary_detection"],
            "all_detections": result.get("all_detections", [])
        }
