"""
Review skill placeholder.
"""

from ..base_skill import BaseSkill


class ReviewSkill(BaseSkill):
    """Code review skill for Syntra agents."""

    def __init__(self):
        super().__init__("review", "0.1.0")

    def get_capabilities(self):
        return {
            "name": self.name,
            "version": self.version,
            "description": "Code review and security expertise",
            "capabilities": [
                "Security checks",
                "Code quality",
                "Git analysis",
                "Best practices"
            ]
        }

    def get_tools(self):
        return {}  # TODO: Implement security_tools, quality_tools