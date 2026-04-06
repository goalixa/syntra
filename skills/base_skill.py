"""
Base skill module - Abstract base class for Syntra skills.

This module provides the base class that all domain skills inherit from.
Skills provide domain expertise to enhance agent capabilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseSkill(ABC):
    """
    Abstract base class for all Syntra skills.

    Skills provide domain expertise, tools, and patterns to agents.
    They encapsulate knowledge specific to a domain (DevOps, Incident, etc.)
    """

    def __init__(self, name: str, version: str = "0.1.0"):
        """
        Initialize the skill.

        Args:
            name: Skill identifier
            version: Skill version
        """
        self.name = name
        self.version = version

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities this skill provides.

        Returns:
            Dict describing skill capabilities
        """
        raise NotImplementedError(f"{self.__class__.__name__}.get_capabilities() not implemented")

    @abstractmethod
    def get_tools(self) -> Dict[str, Any]:
        """
        Get the tools this skill provides to agents.

        Returns:
            Dict mapping tool names to tool functions/classes
        """
        raise NotImplementedError(f"{self.__class__.__name__}.get_tools() not implemented")

    def get_documentation(self) -> str:
        """
        Get the skill documentation (from SKILL.md).

        Returns:
            Path to SKILL.md file
        """
        import os
        skill_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(skill_dir, 'SKILL.md')

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate that the skill has the required context to operate.

        Args:
            context: Context dictionary from agent

        Returns:
            True if skill can operate with given context
        """
        return True  # Default: no special validation

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', version='{self.version}')"