"""
PlannerAgent module - Plans and coordinates multi-agent incident response.

This agent breaks down user requests into actionable steps, determines
which agents should handle which tasks, and orchestrates the workflow.
"""

import sys
import os
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """
    Agent responsible for planning incident response workflows.

    Analyzes user requests and creates execution plans by:
    1. Understanding the user's intent
    2. Identifying required information
    3. Determining which agents to invoke
    4. Creating an ordered task list
    """

    def __init__(self):
        super().__init__(
            name="planner",
            role="Incident Response Planner",
            goal="Break down complex incident response requests into clear, actionable steps and coordinate multi-agent workflows",
            backstory="You are an incident commander who has managed hundreds of production outages. You know that chaos comes from unclear objectives and missing information. Your strength is asking the right questions, identifying what's needed, and creating a clear execution plan that any team can follow."
        )

    def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create an execution plan for the given task.

        Args:
            task: User's request (e.g., "diagnose why my pod is crashing")
            context: Additional context including:
                - namespace: Kubernetes namespace (if known)
                - pod_name: Pod name (if known)
                - urgency: "low", "medium", "high"

        Returns:
            Dict with:
                - plan: Execution plan with ordered steps
                - required_info: Information that's still needed
                - agents_to_use: List of agents that should be involved
                - estimated_steps: Number of steps in the plan
        """
        context = context or {}

        # Parse the task to understand intent
        intent = self._classify_intent(task)

        # Build plan based on intent
        plan = self._build_plan(intent, task, context)

        return {
            "status": "success",
            "plan": plan,
            "intent": intent,
            "required_info": plan.get("required_info", []),
            "agents_to_use": plan.get("agents", []),
            "estimated_steps": len(plan.get("steps", []))
        }

    def _classify_intent(self, task: str) -> str:
        """
        Classify the user's intent from their request.

        Returns one of:
        - "diagnose_pod": Investigate a specific pod's issue
        - "namespace_overview": Check health of entire namespace
        - "collect_evidence": Gather data for analysis
        - "general_help": Unclear intent, needs clarification
        """
        task_lower = task.lower()

        # Direct pod diagnosis
        if any(word in task_lower for word in ["diagnose", "debug", "investigate", "what's wrong"]):
            if "pod" in task_lower or "namespace" in task_lower:
                return "diagnose_pod"

        # Namespace health check
        if any(word in task_lower for word in ["namespace", "all pods", "overview", "status"]):
            return "namespace_overview"

        # Evidence collection
        if any(word in task_lower for word in ["collect", "gather", "get logs", "get events"]):
            return "collect_evidence"

        return "general_help"

    def _build_plan(self, intent: str, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build an execution plan based on intent and available context."""
        namespace = context.get("namespace")
        pod_name = context.get("pod_name")

        plan = {
            "task": task,
            "intent": intent,
            "agents": [],
            "steps": [],
            "required_info": []
        }

        if intent == "diagnose_pod":
            plan = self._build_diagnosis_plan(plan, namespace, pod_name)
        elif intent == "namespace_overview":
            plan = self._build_overview_plan(plan, namespace)
        elif intent == "collect_evidence":
            plan = self._build_evidence_plan(plan, namespace, pod_name)
        else:
            plan = self._build_general_plan(plan)

        return plan

    def _build_diagnosis_plan(
        self,
        plan: Dict[str, Any],
        namespace: str = None,
        pod_name: str = None
    ) -> Dict[str, Any]:
        """Build plan for pod diagnosis."""
        plan["agents"] = ["evidence_collector", "incident"]

        # Check what info we have
        required = []
        if not namespace:
            required.append("namespace")
        if not pod_name:
            required.append("pod_name")

        plan["required_info"] = required

        # Build steps
        if required:
            plan["steps"] = [
                {
                    "step": 1,
                    "agent": "planner",
                    "action": "Gather missing information",
                    "details": f"Need: {', '.join(required)}"
                }
            ]
        else:
            plan["steps"] = [
                {
                    "step": 1,
                    "agent": "evidence_collector",
                    "action": "Collect pod state, logs, and events",
                    "details": f"From {namespace}/{pod_name}"
                },
                {
                    "step": 2,
                    "agent": "incident",
                    "action": "Analyze evidence and diagnose root cause",
                    "details": "Apply rule-based detection, fallback to LLM if needed"
                },
                {
                    "step": 3,
                    "agent": "incident",
                    "action": "Provide remediation recommendations",
                    "details": "Specific steps to resolve the issue"
                }
            ]

        return plan

    def _build_overview_plan(
        self,
        plan: Dict[str, Any],
        namespace: str = None
    ) -> Dict[str, Any]:
        """Build plan for namespace overview."""
        plan["agents"] = ["evidence_collector"]

        if not namespace:
            plan["required_info"] = ["namespace"]
            plan["steps"] = [
                {
                    "step": 1,
                    "agent": "planner",
                    "action": "Get namespace name",
                    "details": "Which namespace should be checked?"
                }
            ]
        else:
            plan["steps"] = [
                {
                    "step": 1,
                    "agent": "evidence_collector",
                    "action": "List all pods in namespace",
                    "details": f"Scanning {namespace}"
                },
                {
                    "step": 2,
                    "agent": "evidence_collector",
                    "action": "Identify problematic pods",
                    "details": "Flag pods with restarts, errors, or not-ready status"
                },
                {
                    "step": 3,
                    "agent": "planner",
                    "action": "Provide summary and recommendations",
                    "details": "Overview of namespace health"
                }
            ]

        return plan

    def _build_evidence_plan(
        self,
        plan: Dict[str, Any],
        namespace: str = None,
        pod_name: str = None
    ) -> Dict[str, Any]:
        """Build plan for evidence collection."""
        plan["agents"] = ["evidence_collector"]

        required = []
        if not namespace:
            required.append("namespace")
        if not pod_name:
            required.append("pod_name")

        plan["required_info"] = required

        if required:
            plan["steps"] = [
                {
                    "step": 1,
                    "agent": "planner",
                    "action": "Get target information",
                    "details": f"Need: {', '.join(required)}"
                }
            ]
        else:
            plan["steps"] = [
                {
                    "step": 1,
                    "agent": "evidence_collector",
                    "action": "Collect pod state",
                    "details": f"{namespace}/{pod_name}"
                },
                {
                    "step": 2,
                    "agent": "evidence_collector",
                    "action": "Collect logs and events",
                    "details": "Recent logs and event history"
                },
                {
                    "step": 3,
                    "agent": "evidence_collector",
                    "action": "Package evidence",
                    "details": "Return complete evidence bundle"
                }
            ]

        return plan

    def _build_general_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Build plan for unclear intent."""
        plan["agents"] = ["planner"]
        plan["steps"] = [
            {
                "step": 1,
                "agent": "planner",
                "action": "Clarify user intent",
                "details": "Ask what specific operation is needed"
            }
        ]
        plan["required_info"] = ["clarification"]

        return plan
