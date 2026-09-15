"""
AI Business Assistant conversational API endpoint.
"""
from fastapi import APIRouter
from backend.app.schemas.assistant import AssistantRequest, AssistantResponse
from backend.app.services.assistant_service import AssistantService

router = APIRouter(tags=["AI Assistant"])


@router.post("/assistant/chat", response_model=AssistantResponse, summary="Chat with autonomous business assistant")
def chat_with_assistant(request: AssistantRequest):
    """
    Routes natural language queries through the autonomous Planner-Executor agent.
    Executes read-only SQL queries, ML forecasts, or policy retrieval and returns
    a grounded answer with a visible tool execution trace.
    """
    return AssistantService.ask_assistant(request)
