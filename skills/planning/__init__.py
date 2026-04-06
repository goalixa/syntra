"""
Planning skill placeholder.
"""

from ..base_skill import BaseSkill


class PlanningSkill(BaseSkill):
    """Task planning skill for Syntra agents."""

    def __init__(self):
        super().__init__("planning", "0.1.0")

    def get_capabilities(self):
        return {
            "name": self.name,
            "version": self.version,
            "description": "Task planning and estimation expertise",
            "capabilities": [
                "Task decomposition",
                "Effort estimation",
                "Prioritization",
                "Dependency analysis"
            ]
        }

    def get_tools(self):
        return {}  # TODO: Implement decomposition_tools, estimation_tools