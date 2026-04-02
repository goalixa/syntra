"""
Rule-based detection tools for CrewAI agents.

Provides tools for detecting common Kubernetes incident patterns without LLM.
Fast, deterministic, and covers the most common scenarios.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class IncidentType(str, Enum):
    """Standard Kubernetes incident types."""
    OOM = "oom"
    CRASH_LOOP = "crash_loop"
    IMAGE_PULL = "image_pull"
    PROBE_FAILURE = "probe_failure"
    UNKNOWN = "unknown"


def detect_oom_killed(pod_state: Dict[str, Any], logs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Detect if pod was killed due to OOM (Out of Memory).

    Checks container states for OOMKilled termination reason.

    Args:
        pod_state: Pod state dictionary
        logs: Log entries (not used for OOM detection but kept for consistency)

    Returns:
        Dict with detected boolean and details
    """
    detected = False
    details = []
    affected_containers = []

    # Check container statuses
    for cs in pod_state.get("container_statuses", []):
        if cs.get("state") == "terminated":
            last_state = cs.get("last_state", {})
            terminated = last_state.get("terminated", {})
            if terminated.get("reason") == "OOMKilled":
                detected = True
                affected_containers.append(cs["name"])
                details.append({
                    "container": cs["name"],
                    "reason": "OOMKilled",
                    "exit_code": terminated.get("exit_code", 137),
                    "finished_at": terminated.get("finished_at")
                })

    # Also check init containers
    for ics in pod_state.get("init_container_statuses", []):
        if ics.get("terminated"):
            if ics["terminated"].get("reason") == "OOMKilled":
                detected = True
                affected_containers.append(ics["name"])
                details.append({
                    "container": ics["name"],
                    "type": "init_container",
                    "reason": "OOMKilled",
                    "exit_code": ics["terminated"].get("exit_code", 137)
                })

    return {
        "incident_type": IncidentType.OOM,
        "detected": detected,
        "confidence": 0.95 if detected else 0.0,  # Very high confidence for OOM
        "details": details,
        "affected_containers": affected_containers,
        "remediation": "Increase memory limit or optimize application memory usage"
    }


def detect_crash_loop_backoff(pod_state: Dict[str, Any], logs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Detect if pod is in CrashLoopBackOff.

    Checks pod phase and container restart counts.

    Args:
        pod_state: Pod state dictionary
        logs: Log entries for additional context

    Returns:
        Dict with detected boolean and details
    """
    detected = False
    details = []
    affected_containers = []

    # Check if pod is in CrashLoopBackOff phase
    if pod_state.get("phase") == "CrashLoopBackOff":
        detected = True
        details.append({
            "phase": "CrashLoopBackOff",
            "message": f"Pod {pod_state.get('name')} is in CrashLoopBackOff"
        })

    # Check container restart counts
    for cs in pod_state.get("container_statuses", []):
        restart_count = cs.get("restart_count", 0)
        if restart_count > 5:
            detected = True
            affected_containers.append(cs["name"])
            details.append({
                "container": cs["name"],
                "restart_count": restart_count,
                "state": cs.get("state", "unknown")
            })

    # Check conditions for CrashLoopBackOff
    for condition in pod_state.get("conditions", []):
        if condition.get("type") == "Ready" and condition.get("status") == "False":
            if condition.get("reason") == "CrashLoopBackOff":
                detected = True
                details.append({
                    "condition": condition.get("type"),
                    "reason": condition.get("reason"),
                    "message": condition.get("message")
                })

    return {
        "incident_type": IncidentType.CRASH_LOOP,
        "detected": detected,
        "confidence": 0.90 if detected else 0.0,
        "details": details,
        "affected_containers": affected_containers,
        "remediation": "Check application logs for crash reasons, fix application errors"
    }


def detect_image_pull_backoff(pod_state: Dict[str, Any], logs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Detect if pod has ImagePullBackOff issues.

    Checks container states and events for image pull errors.

    Args:
        pod_state: Pod state dictionary
        logs: Log entries for additional context

    Returns:
        Dict with detected boolean and details
    """
    detected = False
    details = []
    affected_containers = []

    # Check container states
    for cs in pod_state.get("container_statuses", []):
        if cs.get("state") == "waiting":
            waiting_reason = cs.get("waiting", {}).get("reason", "")
            if "ImagePullBackOff" in waiting_reason or "ErrImagePull" in waiting_reason:
                detected = True
                affected_containers.append(cs["name"])
                details.append({
                    "container": cs["name"],
                    "reason": waiting_reason,
                    "message": cs.get("waiting", {}).get("message", "")
                })

    # Check pod phase
    if pod_state.get("phase") == "ImagePullBackOff":
        detected = True
        details.append({
            "phase": "ImagePullBackOff",
            "message": f"Pod {pod_state.get('name')} cannot pull container image"
        })

    # Check conditions
    for condition in pod_state.get("conditions", []):
        if condition.get("type") in ["ImagesAvailable", "Initialized"]:
            if condition.get("status") == "False":
                detected = True
                details.append({
                    "condition": condition.get("type"),
                    "reason": condition.get("reason"),
                    "message": condition.get("message")
                })

    return {
        "incident_type": IncidentType.IMAGE_PULL,
        "detected": detected,
        "confidence": 0.92 if detected else 0.0,
        "details": details,
        "affected_containers": affected_containers,
        "remediation": "Verify image exists, check registry credentials, fix image name"
    }


def detect_probe_failure(pod_state: Dict[str, Any], logs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Detect if pod has probe failures (readiness/liveness).

    Checks probe statuses and restart counts.

    Args:
        pod_state: Pod state dictionary
        logs: Log entries for additional context

    Returns:
        Dict with detected boolean and details
    """
    detected = False
    details = []
    affected_containers = []

    # Check conditions
    for condition in pod_state.get("conditions", []):
        if condition.get("type") == "Ready" and condition.get("status") == "False":
            if "readiness probe failed" in condition.get("message", "").lower():
                detected = True
                details.append({
                    "condition": "Readiness",
                    "message": condition.get("message")
                })

    # Check containers for probe failures
    for cs in pod_state.get("container_statuses", []):
        restart_count = cs.get("restart_count", 0)
        if restart_count > 0 and cs.get("ready", False) is False:
            # Check if it's probe-related (heuristic)
            detected = True
            affected_containers.append(cs["name"])
            details.append({
                "container": cs["name"],
                "restart_count": restart_count,
                "ready": cs.get("ready", False),
                "started": cs.get("started", False)
            })

    # Also check logs for common probe failure patterns
    probe_keywords = ["readiness probe failed", "liveness probe failed", "connection refused"]
    for log_entry in logs[-10:]:  # Check last 10 log lines
        content = log_entry.get("content", "").lower()
        for keyword in probe_keywords:
            if keyword in content:
                detected = True
                details.append({
                    "source": "logs",
                    "message": log_entry.get("content", "")[:100]  # Truncate long messages
                })
                break

    return {
        "incident_type": IncidentType.PROBE_FAILURE,
        "detected": detected,
        "confidence": 0.75 if detected else 0.0,  # Lower confidence - needs log verification
        "details": details,
        "affected_containers": affected_containers,
        "remediation": "Check probe configuration, verify application is listening on probe port"
    }


def classify_incident(pod_state: Dict[str, Any], logs: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Run all rule-based detection and return the most likely incident type.

    Args:
        pod_state: Pod state dictionary
        logs: Log entries for additional context

    Returns:
        Dict with incident type, confidence, and detection results
    """
    # Run all detectors
    oom_result = detect_oom_killed(pod_state, logs)
    crash_result = detect_crash_loop_backoff(pod_state, logs)
    image_result = detect_image_pull_backoff(pod_state, logs)
    probe_result = detect_probe_failure(pod_state, logs)

    # Find the highest confidence detected incident
    results = [oom_result, crash_result, image_result, probe_result]
    detected_results = [r for r in results if r["detected"]]

    if detected_results:
        # Sort by confidence descending
        detected_results.sort(key=lambda x: x["confidence"], reverse=True)
        best_match = detected_results[0]

        return {
            "incident_type": best_match["incident_type"],
            "confidence": best_match["confidence"],
            "detection_method": "rule_based",
            "primary_detection": best_match,
            "all_detections": detected_results
        }

    # If no pattern matched, return unknown
    return {
        "incident_type": IncidentType.UNKNOWN,
        "confidence": 0.0,
        "detection_method": "rule_based",
        "primary_detection": {
            "incident_type": IncidentType.UNKNOWN,
            "detected": False,
            "confidence": 0.0,
            "details": ["No known pattern matched"],
            "affected_containers": [],
            "remediation": "Requires LLM analysis"
        },
        "all_detections": results
    }


def get_rule_based_diagnosis(
    namespace: str,
    pod_name: str
) -> Dict[str, Any]:
    """
    Get rule-based diagnosis for a pod.

    Main entry point for agents to get rule-based incident classification.

    Args:
        namespace: Kubernetes namespace
        pod_name: Name of the pod

    Returns:
        Dict with classification and recommendations

    Raises:
        ValueError: If pod doesn't exist
    """
    from agents.tools.k8s_tools import get_pod_details, fetch_pod_logs

    # Gather data
    pod_state = get_pod_details(namespace, pod_name)
    logs = fetch_pod_logs(namespace, pod_name, tail_lines=200)

    # Classify
    result = classify_incident(pod_state, logs)

    # Add remediation based on incident type
    remediation_map = {
        IncidentType.OOM: "Increase memory limit in deployment or optimize application",
        IncidentType.CRASH_LOOP: "Check application logs for crash causes and fix",
        IncidentType.IMAGE_PULL: "Verify image exists, check registry credentials, or fix image tag",
        IncidentType.PROBE_FAILURE: "Check probe configuration and application health endpoints",
        IncidentType.UNKNOWN: "Requires further analysis with LLM"
    }

    result["remediation"] = remediation_map.get(result["incident_type"], "Requires analysis")

    return result
