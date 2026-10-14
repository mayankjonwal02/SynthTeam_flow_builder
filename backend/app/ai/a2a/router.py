"""A2A FastAPI router — agent communication endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import verify_token
from app.ai.a2a.protocol import (
    A2AMessage, A2AResponse, AgentCapability,
    AGENT_INSTANCES, get_agent_instance, list_agent_instances,
)

router = APIRouter(prefix="/api/agents", tags=["A2A"], dependencies=[Depends(verify_token)])


@router.get("/")
async def list_agents():
    return {"agents": list_agent_instances()}


@router.get("/{agent_id}/capabilities")
async def get_capabilities(agent_id: str):
    instance = get_agent_instance(agent_id)
    if not instance:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    return AgentCapability(
        agent_id=agent_id,
        name=instance.get("name", agent_id),
        description=instance.get("description", ""),
        tools=instance.get("tools", []),
        accepts_actions=instance.get("accepts_actions", ["request"]),
    )


@router.post("/{agent_id}/message")
async def send_message(agent_id: str, message: A2AMessage):
    instance = get_agent_instance(agent_id)
    if not instance:
        raise HTTPException(404, f"Agent '{agent_id}' not found")

    handler = instance.get("handler")
    if handler:
        result = await handler(message)
        return A2AResponse(status="success", from_agent=agent_id, payload=result)

    return A2AResponse(
        status="error",
        from_agent=agent_id,
        payload={"error": "Agent has no message handler configured"},
    )
