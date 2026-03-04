"""Pydantic models for the multi-agent builder system."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentName(str, Enum):
    REQUIREMENT = "requirement"
    PLANNER = "planner"
    BUILDER = "builder"
    REVIEWER = "reviewer"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    CLARIFYING = "clarifying"
    PLANNING = "planning"
    BUILDING = "building"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    COMPLETED = "completed"
    FAILED = "failed"


class WSEventType(str, Enum):
    AGENT_THINKING = "agent_thinking"
    AGENT_MESSAGE = "agent_message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    NODE_ADDED = "node_added"
    EDGE_ADDED = "edge_added"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"
    STATUS_CHANGE = "status_change"
    NEEDS_INPUT = "needs_input"
    ERROR = "error"
    COMPLETED = "completed"


class WSEvent(BaseModel):
    type: WSEventType
    agent: Optional[AgentName] = None
    data: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ConversationMessage(BaseModel):
    role: str  # user | assistant
    content: str
    agent: Optional[AgentName] = None
    metadata: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SessionStartRequest(BaseModel):
    prompt: str
    project_id: Optional[str] = None
    user_id: str = "anonymous"
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1:8b"
    api_key: Optional[str] = None


class SessionMessageRequest(BaseModel):
    message: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    api_key: Optional[str] = None


class SecretsSubmitRequest(BaseModel):
    secrets: dict[str, dict[str, str]] = Field(
        ...,
        description='Map of node_id -> {field_key: secret_value}. Example: {"abc123": {"api_key": "sk-xxx"}}',
    )


class SessionResponse(BaseModel):
    session_id: str
    status: str
    conversation: list[dict] = []
    artifacts: dict = {}


class GraphNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: str
    position: dict = Field(default_factory=lambda: {"x": 0, "y": 0})
    data: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str
    target: str
    sourceHandle: str = "output"
    targetHandle: str = "input"
