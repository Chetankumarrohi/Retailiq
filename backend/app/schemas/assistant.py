"""
Pydantic schemas for AI Assistant API.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000, description="Natural language question from user")
    conversation_id: Optional[str] = Field(None, description="Optional conversation/session ID")


class ToolTraceStep(BaseModel):
    step: int
    tool: str
    reason: str
    input_summary: Optional[Dict[str, Any]] = None
    output_summary: Optional[str] = None


class PolicyCitation(BaseModel):
    document: str
    section: str
    snippet: str


class AssistantResponse(BaseModel):
    answer: str
    tools_used: List[str]
    trace: List[ToolTraceStep]
    sources: List[PolicyCitation] = []
    error: Optional[str] = None
