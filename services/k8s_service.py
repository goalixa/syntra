"""
Kubernetes Service - Python K8s client wrapper

Provides a clean interface for Kubernetes operations using the official Python client.
Replaces subprocess kubectl calls with proper API-based interactions.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException


class KubernetesService:
    """
    Kubernetes client wrapper for Syntra incident debugging.

    Loads kubeconfig from ~/.kube/config or uses in-cluster config.
    """

    def __init__(self):
        """Initialize Kubernetes client with proper configuration."""
        self._load_config()

        # Core API clients
        self.core_v1 = client.CoreV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.apps_v1 = client.AppsV1Api()

    def _load_config(self):
        """Load Kubernetes configuration from kubeconfig or in-cluster."""
        try:
            # Try in-cluster config first (for running in K8s pods)
            config.load_incluster_config()
        except config.ConfigException:
            try:
                # Fall back to kubeconfig file
                kubeconfig_path = os.path.expanduser(
                    os.getenv("KUBECONFIG_PATH", "~/.kube/config")
                )
                config.load_kube_config(config_file=kubeconfig_path)
            except config.ConfigException as e:
                raise RuntimeError(
                    f"Could not load Kubernetes configuration. "
                    f"Either run in-cluster or set KUBECONFIG_PATH. Error: {e}"
                )

    def get_pod_state(
        self,
        namespace: str,
        pod_name: str
    ) -> Dict[str, Any]:
        """
        Get detailed pod state including status, phase, and conditions.

        Args:
            namespace: Kubernetes namespace
            pod_name: Name of the pod

        Returns:
            Dict with pod status, phase, conditions, and container statuses

        Raises:
            ApiException: If pod doesn't exist or API call fails
        """
        try:
            pod = self.core_v1.read_namespaced_pod(namespace, pod_name)

            # Extract relevant state information
            state = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "pod_ip": pod.status.pod_ip,
                "node_name": pod.spec.node_name,
                "start_time": pod.status.start_time.isoformat() if pod.status.start_time else None,
                "conditions": [],
                "container_statuses": [],
                "init_container_statuses": [],
                "labels": pod.metadata.labels or {},
                "annotations": pod.metadata.annotations or {},
            }

            # Extract conditions
            if pod.status.conditions:
                for condition in pod.status.conditions:
                    state["conditions"].append({
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                        "last_transition_time": condition.last_transition_time.isoformat() if condition.last_transition_time else None,
                    })

            # Extract container statuses
            if pod.status.container_statuses:
                for cs in pod.status.container_statuses:
                    state["container_statuses"].append({
                        "name": cs.name,
                        "image": cs.image,
                        "image_id": cs.image_id,
                        "ready": cs.ready,
                        "restart_count": cs.restart_count,
                        "started": cs.started,
                        "state": cs.state,
                        "last_state": {
                            "state": cs.last_state.state if cs.last_state else None,
                            "terminated": {
                                "reason": cs.last_state.terminated.reason if cs.last_state and cs.last_state.terminated else None,
                                "exit_code": cs.last_state.terminated.exit_code if cs.last_state and cs.last_state.terminated else None,
                                "finished_at": cs.last_state.terminated.finished_at.isoformat() if cs.last_state and cs.last_state.terminated else None,
                            } if cs.last_state and cs.last_state.terminated else None,
                        } if cs.last_state else None,
                        "state": cs.state,  # running, waiting, terminated
                    })

            # Extract init container statuses
            if pod.status.init_container_statuses:
                for ics in pod.status.init_container_statuses:
                    state["init_container_statuses"].append({
                        "name": ics.name,
                        "image": ics.image,
                        "ready": ics.ready,
                        "restart_count": ics.restart_count,
                        "terminated": ics.terminated.terminated.reason if ics.terminated else None,
                        "exit_code": ics.terminated.exit_code if ics.terminated else None,
                        "finished_at": ics.terminated.finished_at.isoformat() if ics.terminated else None,
                    })

            return state

        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Pod '{pod_name}' not found in namespace '{namespace}'")
            raise

    def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        container: Optional[str] = None,
        tail_lines: int = 100,
        timestamps: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get log lines from a pod with timestamps.

        Args:
            namespace: Kubernetes namespace
            pod_name: Name of the pod
            container: Container name (if multiple containers, defaults to first)
            tail_lines: Number of lines from end of logs
            timestamps: Whether to include timestamps in log output

        Returns:
            List of dicts with timestamp and log line

        Raises:
            ApiException: If pod doesn't exist or logs aren't available
        """
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                namespace=namespace,
                name=pod_name,
                container=container,
                tail_lines=tail_lines,
                timestamps=timestamps
            )

            # Parse logs into structured format
            log_lines = []
            for line in logs.split('\n'):
                if not line:
                    continue

                log_entry = {"raw": line}

                # Try to extract timestamp (K8s logs typically start with timestamp)
                if timestamps and ' ' in line:
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        potential_timestamp, content = parts
                        # Check if it looks like an ISO timestamp
                        if potential_timestamp.count(':') >= 2 and potential_timestamp.count('-') >= 2:
                            log_entry["timestamp"] = potential_timestamp
                            log_entry["content"] = content
                        else:
                            log_entry["content"] = line
                else:
                    log_entry["content"] = line

                log_lines.append(log_entry)

            return log_lines

        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Pod '{pod_name}' not found in namespace '{namespace}'")
            raise

    def get_events(
        self,
        namespace: str,
        pod_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get events from namespace, optionally filtered by pod.

        Args:
            namespace: Kubernetes namespace
            pod_name: Optional pod name to filter events
            limit: Maximum number of events to return

        Returns:
            List of event dicts with metadata

        Raises:
            ApiException: If API call fails
        """
        try:
            if pod_name:
                # Get events specific to a pod
                events = self.core_v1.list_namespaced_event(
                    namespace=namespace,
                    field_selector=f"involvedObject.name={pod_name}",
                    limit=limit
                )
            else:
                # Get all namespace events
                events = self.core_v1.list_namespaced_event(
                    namespace=namespace,
                    limit=limit
                )

            event_list = []
            for event in events.items:
                event_list.append({
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "source": event.source.component if event.source else None,
                    "object": {
                        "kind": event.involved_object.kind if event.involved_object else None,
                        "name": event.involved_object.name if event.involved_object else None,
                    } if event.involved_object else None,
                    "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                    "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None,
                    "count": event.count,
                })

            return event_list

        except ApiException as e:
            raise ValueError(f"Failed to get events for namespace '{namespace}': {e}")

    def list_pods(
        self,
        namespace: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all pods in a namespace.

        Args:
            namespace: Kubernetes namespace
            limit: Maximum number of pods to return

        Returns:
            List of pod summaries with name, status, phase, and issues

        Raises:
            ApiException: If namespace doesn't exist or API call fails
        """
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                limit=limit
            )

            pod_list = []
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "pod_ip": pod.status.pod_ip,
                    "node_name": pod.spec.node_name,
                    "labels": pod.metadata.labels or {},
                    "start_time": pod.status.start_time.isoformat() if pod.status.start_time else None,
                    "issues": [],
                }

                # Detect common issues
                if pod.status.phase == "Failed":
                    pod_info["issues"].append(f"Phase: Failed")
                elif pod.status.phase == "Pending":
                    pod_info["issues"].append(f"Phase: Pending")

                # Check container statuses for issues
                if pod.status.container_statuses:
                    for cs in pod.status.container_statuses:
                        if cs.waiting:
                            pod_info["issues"].append(f"Container {cs.name}: Waiting")
                        if cs.terminated and cs.terminated.exit_code != 0:
                            pod_info["issues"].append(
                                f"Container {cs.name}: Exited {cs.terminated.exit_code}"
                            )
                        if cs.restart_count > 0:
                            pod_info["issues"].append(
                                f"Container {cs.name}: Restarted {cs.restart_count} times"
                            )

                pod_list.append(pod_info)

            return pod_list

        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Namespace '{namespace}' not found")
            raise

    def check_connectivity(self) -> bool:
        """
        Check if the Kubernetes API is accessible.

        Returns:
            True if connected, False otherwise
        """
        try:
            self.core_v1.list_pod_for_all_namespaces(limit=1)
            return True
        except Exception:
            return False


# Singleton instance for reuse
_k8s_service_instance: Optional[KubernetesService] = None


def get_k8s_service() -> KubernetesService:
    """
    Get or create singleton KubernetesService instance.

    Returns:
        KubernetesService instance
    """
    global _k8s_service_instance
    if _k8s_service_instance is None:
        _k8s_service_instance = KubernetesService()
    return _k8s_service_instance
