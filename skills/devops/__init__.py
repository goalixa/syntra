"""
DevOps skill implementation.

This skill provides Kubernetes operations, deployment patterns, and troubleshooting
expertise to enhance the DevOpsAgent.
"""

import os
from typing import Any, Dict

from .base_skill import BaseSkill
from .devops.tools.deployment_tools import DeploymentTools
from .devops.tools.troubleshooting_tools import TroubleshootingTools
from .devops.tools.config_tools import ConfigTools


class DevopsSkill(BaseSkill):
    """DevOps domain skill for Syntra agents."""

    def __init__(self):
        super().__init__("devops", "0.1.0")

        # Initialize tool instances
        self._deployment_tools = DeploymentTools()
        self._troubleshooting_tools = TroubleshootingTools()
        self._config_tools = ConfigTools()

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this skill.

        Returns:
            Dict describing DevOps capabilities
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": "Kubernetes operations and DevOps expertise",
            "capabilities": [
                "Deploy applications to Kubernetes",
                "Rollback deployments",
                "Scale applications",
                "Diagnose pod issues",
                "Manage ConfigMaps and Secrets",
                "Analyze node health",
                "Troubleshoot K8s incidents"
            ],
            "supported_operations": [
                "apply_manifest",
                "rollback_deployment",
                "scale_deployment",
                "restart_deployment",
                "check_deployment_health",
                "diagnose_pod",
                "get_pod_events",
                "search_logs",
                "check_resource_quotas",
                "analyze_node_health",
                "get_configmap",
                "update_configmap",
                "get_secret",
                "create_secret"
            ],
            "incident_patterns": self._get_incident_patterns()
        }

    def get_tools(self) -> Dict[str, Any]:
        """
        Get the tools this skill provides.

        Returns:
            Dict mapping tool names to implementations
        """
        return {
            # Deployment tools
            "deploy_manifest": self._deployment_tools.deploy_manifest,
            "rollback_deployment": self._deployment_tools.rollback_deployment,
            "scale_deployment": self._deployment_tools.scale_deployment,
            "restart_deployment": self._deployment_tools.restart_deployment,
            "check_deployment_health": self._deployment_tools.check_deployment_health,
            "get_deployment_history": self._deployment_tools.get_deployment_history,

            # Troubleshooting tools
            "diagnose_pod": self._troubleshooting_tools.diagnose_pod,
            "get_pod_events": self._troubleshooting_tools.get_pod_events,
            "search_logs": self._troubleshooting_tools.search_logs,
            "check_resource_quotas": self._troubleshooting_tools.check_resource_quotas,
            "analyze_node_health": self._troubleshooting_tools.analyze_node_health,

            # Config tools
            "get_configmap": self._config_tools.get_configmap,
            "update_configmap": self._config_tools.update_configmap,
            "create_configmap_from_file": self._config_tools.create_configmap_from_file,
            "get_secret": self._config_tools.get_secret,
            "create_secret": self._config_tools.create_secret,
            "list_configmaps": self._config_tools.list_configmaps,
            "list_secrets": self._config_tools.list_secrets,
            "compare_configmap": self._config_tools.compare_configmap
        }

    def _get_incident_patterns(self) -> list:
        """
        Get the known incident patterns from docs.

        Returns:
            List of incident patterns
        """
        patterns = [
            {
                "name": "Pod Pending",
                "symptom": "Pod stays in Pending state",
                "causes": ["Insufficient resources", "Affinity rules", "PVC issues"],
                "remediation": "Check resources, add nodes, adjust affinity"
            },
            {
                "name": "ImagePullBackOff",
                "symptom": "Pod fails to pull container image",
                "causes": ["Invalid image", "Missing secret", "Auth failure"],
                "remediation": "Fix image name, create pull secret"
            },
            {
                "name": "CrashLoopBackOff",
                "symptom": "Container restarts repeatedly",
                "causes": ["Startup failure", "Missing config", "OOM", "Probe failure"],
                "remediation": "Check logs, fix config, increase memory"
            },
            {
                "name": "OOMKilled",
                "symptom": "Container terminated due to memory limit",
                "causes": ["Low memory limit", "Memory leak", "Too many requests"],
                "remediation": "Increase limits, fix leaks, implement caching"
            },
            {
                "name": "Evicted Pod",
                "symptom": "Pod evicted from node",
                "causes": ["Disk pressure", "Memory pressure", "Network issues"],
                "remediation": "Free disk, add nodes, reduce pressure"
            },
            {
                "name": "Unhealthy Readiness Probe",
                "symptom": "Pod ready condition is False",
                "causes": ["App not ready", "Misconfigured probe", "Slow startup"],
                "remediation": "Fix probe, increase initialDelaySeconds"
            },
            {
                "name": "Deployment Rollout Stuck",
                "symptom": "Deployment doesn't progress",
                "causes": ["Image pull failure", "Container can't start", "Probe failure"],
                "remediation": "Check image, fix config, adjust resources"
            },
            {
                "name": "Service Not Reaching Pod",
                "symptom": "Service can't communicate with pods",
                "causes": ["Wrong label", "Missing endpoints", "Network policy"],
                "remediation": "Fix labels, check endpoints, adjust network policy"
            },
            {
                "name": "Ingress 502/504",
                "symptom": "Ingress returns 502 or 504",
                "causes": ["No ready pods", "Port mismatch", "Backend timeout"],
                "remediation": "Ensure pods ready, verify port, increase timeout"
            }
        ]
        return patterns

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate that the skill has required context.

        Args:
            context: Context from agent

        Returns:
            True if skill can operate
        """
        # Check for required context keys
        required = ['namespace']
        return any(key in context for key in required)