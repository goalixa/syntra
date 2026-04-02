"""
EvidenceCollectorAgent module - Gathers diagnostic evidence from Kubernetes.

This agent is responsible for collecting all relevant data for incident analysis:
pod state, logs, events, and related information.
"""

import sys
import os
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.base_agent import BaseAgent
from agents.tools.k8s_tools import (
    get_pod_details,
    fetch_pod_logs,
    fetch_events,
    list_pods_in_namespace,
    check_k8s_connectivity
)


class EvidenceCollectorAgent(BaseAgent):
    """
    Agent responsible for gathering diagnostic evidence.

    Collects pod state, logs, events, and related information to provide
    complete context for incident analysis.
    """

    def __init__(self):
        super().__init__(
            name="evidence_collector",
            role="Evidence Collector",
            goal="Gather complete diagnostic evidence from Kubernetes clusters including pod state, logs, and events",
            backstory="You are a forensic investigator for Kubernetes incidents. You know that the key to solving any incident is having complete, accurate evidence. You collect methodically - pod state first, then logs, then events, then related context. You never miss a detail because that detail might be the smoking gun."
        )

    def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Collect evidence for an incident.

        Args:
            task: Description of what to collect (e.g., "collect evidence for pod my-app-123")
            context: Additional context including:
                - namespace: Kubernetes namespace
                - pod_name: Pod to collect evidence from
                - log_lines: Number of log lines to collect (default 200)
                - event_limit: Number of events to collect (default 50)
                - include_related: Also collect evidence from related pods

        Returns:
            Dict with:
                - status: "success" or "error"
                - evidence: Collected evidence (pod_state, logs, events)
                - metadata: Collection metadata (timestamps, counts)
        """
        context = context or {}

        # Extract parameters
        namespace = context.get("namespace")
        pod_name = context.get("pod_name")
        log_lines = context.get("log_lines", 200)
        event_limit = context.get("event_limit", 50)
        include_related = context.get("include_related", False)

        if not namespace or not pod_name:
            return {
                "status": "error",
                "error": "Missing required context: namespace and pod_name",
                "evidence": {}
            }

        try:
            # Verify connectivity first
            if not check_k8s_connectivity():
                return {
                    "status": "error",
                    "error": "Cannot connect to Kubernetes cluster",
                    "evidence": {}
                }

            # Collect pod state
            pod_state = get_pod_details(namespace, pod_name)

            # Collect logs from all containers
            logs = []
            for container in pod_state.get("container_statuses", []):
                container_name = container["name"]
                container_logs = fetch_pod_logs(
                    namespace,
                    pod_name,
                    container=container_name,
                    tail_lines=log_lines
                )
                logs.extend(container_logs)

            # Collect events
            events = fetch_events(namespace, pod_name, limit=event_limit)

            # Build evidence package
            evidence = {
                "pod_state": pod_state,
                "logs": logs,
                "events": events,
                "related_pods": []
            }

            # Collect evidence from related pods if requested
            if include_related:
                related = self._collect_related_evidence(
                    namespace,
                    pod_state,
                    log_lines // 2,  # Fewer logs for related pods
                    event_limit // 2
                )
                evidence["related_pods"] = related

            return {
                "status": "success",
                "evidence": evidence,
                "metadata": {
                    "namespace": namespace,
                    "pod_name": pod_name,
                    "log_lines_collected": len(logs),
                    "events_collected": len(events),
                    "related_pods_collected": len(evidence["related_pods"]),
                    "pod_phase": pod_state.get("phase"),
                    "containers_count": len(pod_state.get("container_statuses", []))
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "evidence": {}
            }

    def collect_namespace_overview(
        self,
        namespace: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Collect an overview of all pods in a namespace.

        Useful for identifying problematic pods when specific target isn't known.

        Args:
            namespace: Kubernetes namespace
            limit: Maximum number of pods to return

        Returns:
            Dict with pod list and issue summary
        """
        try:
            pods = list_pods_in_namespace(namespace, limit)

            # Categorize by status
            overview = {
                "total": len(pods),
                "running": [],
                "pending": [],
                "failed": [],
                "unknown": [],
                "issues_detected": []
            }

            for pod in pods:
                phase = pod.get("phase", "Unknown")
                overview[phase.lower()].append(pod["name"])

                # Flag pods with issues
                if pod.get("restart_count", 0) > 0:
                    overview["issues_detected"].append({
                        "pod": pod["name"],
                        "issue": f"Restart count: {pod['restart_count']}"
                    })

                if pod.get("not_ready", False):
                    overview["issues_detected"].append({
                        "pod": pod["name"],
                        "issue": "Pod not ready"
                    })

            return {
                "status": "success",
                "overview": overview,
                "pods": pods
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "overview": {}
            }

    def _collect_related_evidence(
        self,
        namespace: str,
        pod_state: Dict[str, Any],
        log_lines: int,
        event_limit: int
    ) -> List[Dict[str, Any]]:
        """
        Collect evidence from pods related to the incident pod.

        Finds related pods by:
        - Same deployment/replicaset
        - Same service selector
        - Same node

        Args:
            namespace: Kubernetes namespace
            pod_state: State of the incident pod
            log_lines: Log lines to collect per pod
            event_limit: Events to collect per pod

        Returns:
            List of related pod evidence
        """
        related = []

        # Find pods from same replicaset/deployment
        # (This is simplified - real implementation would query more intelligently)
        owner = pod_state.get("metadata", {}).get("ownerReferences", [{}])[0]
        if owner:
            owner_name = owner.get("name")
            if owner_name:
                try:
                    # List pods and find siblings
                    all_pods = list_pods_in_namespace(namespace, limit=100)
                    siblings = [
                        p for p in all_pods
                        if p.get("name") != pod_state.get("name")
                        and owner_name in p.get("name", "")
                    ][:3]  # Max 3 siblings

                    for sibling in siblings:
                        try:
                            sibling_state = get_pod_details(namespace, sibling["name"])
                            sibling_logs = fetch_pod_logs(
                                namespace,
                                sibling["name"],
                                tail_lines=log_lines
                            )

                            related.append({
                                "name": sibling["name"],
                                "state": sibling_state,
                                "logs": sibling_logs,
                                "relationship": "sibling"
                            })
                        except Exception:
                            continue

                except Exception:
                    pass

        return related
