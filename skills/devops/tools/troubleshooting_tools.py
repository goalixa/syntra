"""
Troubleshooting tools for DevOps skill.

Provides diagnostic operations for Kubernetes resources including
log analysis, event inspection, and resource diagnostics.
"""

import sys
import os
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.k8s_service import get_k8s_service


class TroubleshootingTools:
    """Kubernetes troubleshooting operations for DevOpsAgent."""

    def __init__(self):
        self.k8s = get_k8s_service()

    def diagnose_pod(
        self,
        pod_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Run comprehensive diagnostics on a pod.

        Collects: pod state, events, logs, and container status.

        Args:
            pod_name: Name of the pod
            namespace: Target namespace

        Returns:
            Dict with comprehensive diagnostic information
        """
        # Get pod details
        pod_state = self.k8s.get_pod_state(namespace, pod_name)

        # Get recent events
        events = self.k8s.get_events(namespace, pod_name, limit=20)

        # Get logs (last 100 lines)
        logs = self.k8s.get_pod_logs(namespace, pod_name, tail_lines=100)

        # Analyze issues
        issues = self._analyze_pod_issues(pod_state, events, logs)

        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "pod_state": pod_state,
            "recent_events": events,
            "recent_logs": logs,
            "issues_found": issues,
            "recommendation": self._generate_recommendation(issues)
        }

    def _analyze_pod_issues(
        self,
        pod_state: Dict,
        events: List[Dict],
        logs: List[Dict]
    ) -> List[str]:
        """Analyze pod state, events, and logs to identify issues."""
        issues = []

        # Check pod status
        phase = pod_state.get('phase', 'Unknown')
        if phase != 'Running':
            issues.append(f"Pod status is {phase} (expected Running)")

        # Check container states
        containers = pod_state.get('status', {}).get('containerStatuses', [])
        for container in containers:
            state = container.get('state', {})
            if 'terminated' in state:
                term = state['terminated']
                issues.append(f"Container {container['name']} terminated: {term.get('reason', 'unknown')}")
            if 'waiting' in state:
                wait = state['waiting']
                issues.append(f"Container {container['name']} waiting: {wait.get('reason', 'unknown')}")

        # Check events for issues
        for event in events:
            reason = event.get('reason', '')
            if reason in ['FailedScheduling', 'Unhealthy', 'FailedMount', 'FailedPullImage']:
                issues.append(f"Event: {reason} - {event.get('message', '')}")

        # Check logs for errors
        error_keywords = ['ERROR', 'FATAL', 'panic', 'exception', 'crash', 'OutOfMemory']
        for log in logs:
            message = log.get('message', '')
            for keyword in error_keywords:
                if keyword.lower() in message.lower():
                    issues.append(f"Log error: {keyword} found in {log.get('timestamp', 'unknown')}")
                    break

        return issues

    def _generate_recommendation(self, issues: List[str]) -> str:
        """Generate recommendation based on identified issues."""
        if not issues:
            return "No issues found. Pod appears healthy."

        # Map issues to recommendations
        recommendations = []
        for issue in issues:
            if 'Pending' in issue:
                recommendations.append("Check cluster resources (CPU/memory) or pod affinity rules")
            elif 'ImagePullBackOff' in issue:
                recommendations.append("Verify image name and registry credentials")
            elif 'CrashLoopBackOff' in issue:
                recommendations.append("Check application logs for startup errors")
            elif 'OOMKilled' in issue:
                recommendations.append("Increase memory limits or check for memory leaks")
            elif 'Terminated' in issue:
                recommendations.append("Check exit code and application logs")
            elif 'Unhealthy' in issue:
                recommendations.append("Check readiness/liveness probe configuration")

        return "; ".join(recommendations) if recommendations else "Review pod events and logs for details"

    def get_pod_events(
        self,
        pod_name: str,
        namespace: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Get all events related to a specific pod.

        Args:
            pod_name: Name of the pod
            namespace: Target namespace

        Returns:
            List of event dictionaries
        """
        return self.k8s.get_events(namespace, pod_name, limit=100)

    def search_logs(
        self,
        namespace: str,
        pod_pattern: str = "",
        container: str = None,
        since_minutes: int = 60,
        pattern: str = ""
    ) -> List[Dict[str, str]]:
        """
        Search logs across pods matching a pattern.

        Args:
            namespace: Target namespace
            pod_pattern: Regex pattern to match pod names
            container: Container name (optional)
            since_minutes: How far back to search
            pattern: Log message pattern to search for

        Returns:
            List of matching log entries
        """
        # Get all pods in namespace
        all_pods = self.k8s.list_pods(namespace, limit=100)
        matching_pods = [p for p in all_pods if not pod_pattern or pod_pattern in p.get('name', '')]

        results = []
        for pod in matching_pods:
            pod_name = pod.get('name', '')
            logs = self.k8s.get_pod_logs(namespace, pod_name, container, tail_lines=500)

            for log in logs:
                message = log.get('message', '')
                if not pattern or pattern.lower() in message.lower():
                    log['pod'] = pod_name
                    results.append(log)

        return results

    def check_resource_quotas(self, namespace: str = "default") -> Dict[str, Any]:
        """
        Check resource usage and quotas in a namespace.

        Args:
            namespace: Target namespace

        Returns:
            Dict with resource quota information
        """
        import subprocess
        import json

        try:
            result = subprocess.run(
                ['kubectl', 'top', 'pods', '-n', namespace],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # Metrics server might not be available
                return {
                    "success": False,
                    "error": "Resource metrics not available",
                    "hint": "Ensure metrics-server is deployed"
                }

            # Parse output
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            pod_resources = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 3:
                    pod_resources.append({
                        "name": parts[0],
                        "cpu": parts[1],
                        "memory": parts[2]
                    })

            return {
                "success": True,
                "namespace": namespace,
                "pods": pod_resources
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_node_health(self, node_name: str = None) -> Dict[str, Any]:
        """
        Analyze node health, optionally filtered by node name.

        Args:
            node_name: Specific node to analyze (optional)

        Returns:
            Dict with node health information
        """
        import subprocess
        import json

        try:
            cmd = ['kubectl', 'get', 'nodes', '-o', 'json']
            if node_name:
                cmd = ['kubectl', 'get', 'node', node_name, '-o', 'json']

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}

            nodes_data = json.loads(result.stdout)
            items = nodes_data.get('items', [nodes_data]) if node_name else nodes_data.get('items', [])

            node_health = []
            for node in items:
                conditions = node.get('status', {}).get('conditions', [])
                ready = next((c for c in conditions if c.get('type') == 'Ready'), None)

                node_health.append({
                    "name": node['metadata']['name'],
                    "ready": ready.get('status') == 'True' if ready else False,
                    "conditions": [
                        {"type": c.get('type'), "status": c.get('status')}
                        for c in conditions
                    ]
                })

            return {
                "success": True,
                "nodes": node_health
            }
        except Exception as e:
            return {"success": False, "error": str(e)}