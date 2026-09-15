"""
Assistant service managing conversation queries and agent planner execution.
"""
from typing import Dict, Any
from backend.app.agent.planner import AgentPlanner
from backend.app.schemas.assistant import AssistantRequest, AssistantResponse


class AssistantService:
    """Service layer delegating to the autonomous AgentPlanner."""

    _planner_instance = None

    @classmethod
    def get_planner(cls) -> AgentPlanner:
        if cls._planner_instance is None:
            cls._planner_instance = AgentPlanner()
        return cls._planner_instance

    @classmethod
    def ask_assistant(cls, request: AssistantRequest) -> AssistantResponse:
        """Processes user message through the planner."""
        planner = cls.get_planner()
        return planner.process_query(request.message)
