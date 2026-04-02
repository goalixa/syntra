"""
BaseAgent module - Abstract base class for Syntra agents.

This module provides the base class that all Syntra agents inherit from.
Compatible with both standalone usage and CrewAI integration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """
    Abstract base class for all Syntra agents.

    Provides the interface that all agents must implement.
    Compatible with both direct instantiation and CrewAI Agent wrapping.
    """

    def __init__(self, name: str, role: str = None, goal: str = None, backstory: str = None):
        """
        Initialize the agent.

        Args:
            name: Agent identifier
            role: Agent's role description (for CrewAI)
            goal: Agent's goal (for CrewAI)
            backstory: Agent's background (for CrewAI)
        """
        self.name = name
        self.role = role or f"{name.capitalize()} Agent"
        self.goal = goal or f"Perform {name} tasks"
        self.backstory = backstory or f"Expert in {name} operations"

    @abstractmethod
    def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the agent's primary task.

        Args:
            task: Task description
            context: Additional context (optional)

        Returns:
            Dict with task results
        """
        raise NotImplementedError(f"{self.__class__.__name__}.run() not implemented")

    def to_crewai_agent(self):
        """
        Convert this agent to a CrewAI Agent.

        Returns:
            CrewAI Agent instance (or None if CrewAI not available)
        """
        try:
            from crewai import Agent as CrewAIAgent
            return CrewAIAgent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                verbose=True
            )
        except ImportError:
            return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
