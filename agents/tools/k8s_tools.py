"""
Kubernetes tools for CrewAI agents.

Provides tool functions that agents can call to interact with Kubernetes.
These tools wrap the services layer for clean agent integration.
"""

import sys
import os
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.k8s_service import get_k8s_service


def list_pods_in_namespace(namespace: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    List all pods in a namespace.

    Tool for agents to discover what pods exist and identify problematic ones.

    Args:
        namespace: Kubernetes namespace
        limit: Maximum number of pods to return (default 100)

    Returns:
        List of pod summaries

    Raises:
        ValueError: If namespace doesn't exist
    """
    k8s = get_k8s_service()
    return k8s.list_pods(namespace, limit)


def get_pod_details(namespace: str, pod_name: str) -> Dict[str, Any]:
    """
    Get detailed pod state including status, conditions, and container info.

    Tool for agents to get full diagnostic information about a specific pod.

    Args:
        namespace: Kubernetes namespace
        pod_name: Name of the pod

    Returns:
        Dict with comprehensive pod state

    Raises:
        ValueError: If pod doesn't exist
    """
    k8s = get_k8s_service()
    return k8s.get_pod_state(namespace, pod_name)


def fetch_pod_logs(
    namespace: str,
    pod_name: str,
    container: str = None,
    tail_lines: int = 100
) -> List[Dict[str, str]]:
    """
    Fetch recent log lines from a pod.

    Tool for agents to retrieve logs for analysis.

    Args:
        namespace: Kubernetes namespace
        pod_name: Name of the pod
        container: Container name (if multiple)
        tail_lines: Number of lines from end (default 100)

    Returns:
        List of structured log entries with timestamps

    Raises:
        ValueError: If pod doesn't exist or logs unavailable
    """
    k8s = get_k8s_service()
    return k8s.get_pod_logs(namespace, pod_name, container, tail_lines)


def fetch_events(
    namespace: str,
    pod_name: str = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch events from namespace, optionally filtered by pod.

    Tool for agents to get event history for diagnosis.

    Args:
        namespace: Kubernetes namespace
        pod_name: Optional pod name to filter events
        limit: Maximum number of events (default 50)

    Returns:
        List of event dictionaries

    Raises:
        ValueError: If API call fails
    """
    k8s = get_k8s_service()
    return k8s.get_events(namespace, pod_name, limit)


def check_k8s_connectivity() -> bool:
    """
    Check if Kubernetes API is accessible.

    Tool for agents to verify they can reach the cluster.

    Returns:
        True if connected, False otherwise
    """
    k8s = get_k8s_service()
    return k8s.check_connectivity()
