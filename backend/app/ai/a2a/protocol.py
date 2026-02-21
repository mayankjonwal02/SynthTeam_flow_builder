"""Agent-to-Agent protocol — message schema and agent metadata."""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime


class A2AMessage(BaseModel):
    from_agent: str
    to_agent: str
    action: str  # "request", "respond", "delegate", "share_memory"
    payload: Dict[str, Any]
    timestamp: str = ""

    def model_post_init(self, __context):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class AgentCapability(BaseModel):
    agent_id: str
    name: str
    description: str
    tools: List[str]
    accepts_actions: List[str]  # what A2A actions this agent handles


class A2AResponse(BaseModel):
    status: str  # "success", "error", "delegated"
    from_agent: str
    payload: Dict[str, Any]


# In-memory registry of active agents
AGENT_INSTANCES: Dict[str, Dict[str, Any]] = {}


def register_agent_instance(agent_id: str, metadata: dict):
    AGENT_INSTANCES[agent_id] = metadata


def get_agent_instance(agent_id: str) -> Optional[dict]:
    return AGENT_INSTANCES.get(agent_id)


def list_agent_instances() -> List[str]:
    return list(AGENT_INSTANCES.keys())
