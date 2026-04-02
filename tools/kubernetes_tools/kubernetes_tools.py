"""
Kubernetes tools - now using Python K8s client instead of subprocess.

This module provides a convenience wrapper around the services layer.
"""

import sys
import os
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.k8s_service import get_k8s_service


def get_pods(namespace: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all pods in a namespace.

    Args:
        namespace: Kubernetes namespace
        limit: Maximum number of pods to return (default 100)

    Returns:
        List of pod summaries with name, status, phase, and issues

    Raises:
        ValueError: If namespace doesn't exist
        RuntimeError: If K8s configuration is invalid
    """
    k8s = get_k8s_service()
    return k8s.list_pods(namespace, limit=limit)


def get_pod_state(namespace: str, pod_name: str) -> Dict[str, Any]:
    """
    Get detailed pod state.

    Args:
        namespace: Kubernetes namespace
        pod_name: Name of the pod

    Returns:
        Dict with pod status, phase, conditions, and container statuses
    """
    k8s = get_k8s_service()
    return k8s.get_pod_state(namespace, pod_name)


def get_pod_logs(
    namespace: str,
    pod_name: str,
    container: str = None,
    tail_lines: int = 100
) -> List[Dict[str, str]]:
    """
    Get log lines from a pod.

    Args:
        namespace: Kubernetes namespace
        pod_name: Name of the pod
        container: Container name (if multiple)
        tail_lines: Number of lines from end (default 100)

    Returns:
        List of dicts with timestamp and log line
    """
    k8s = get_k8s_service()
    return k8s.get_pod_logs(namespace, pod_name, container, tail_lines)


def get_events(namespace: str, pod_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get events from namespace.

    Args:
        namespace: Kubernetes namespace
        pod_name: Optional pod name to filter events
        limit: Maximum number of events (default 50)

    Returns:
        List of event dicts with metadata
    """
    k8s = get_k8s_service()
    return k8s.get_events(namespace, pod_name, limit)
