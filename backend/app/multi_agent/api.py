"""REST API for the multi-agent workflow builder."""

from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.multi_agent.schemas import (
    SessionMessageRequest,
    SessionStartRequest,
)
from app.multi_agent.session import SessionManager
from app.multi_agent.orchestrator import MultiAgentOrchestrator
from app.multi_agent.ws import create_ws_emitter

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/agent", tags=["agent-builder"])

_session_mgr = SessionManager()


def _resolve_api_key(provider: str, explicit_key: str | None) -> str:
    """Return the explicit key if provided, otherwise fall back to env vars."""
    if explicit_key:
        return explicit_key
    try:
        from app.core.config import settings
        env_map = {
            "groq": getattr(settings, "GROQ_API_KEY", ""),
        }
        return env_map.get(provider, "") or ""
    except Exception:
        return ""


def _get_llm(req: SessionStartRequest):
    from app.ai.llm.registry import get_llm
    api_key = _resolve_api_key(req.llm_provider, req.api_key)
    return get_llm(
        provider=req.llm_provider,
        model=req.llm_model,
        api_key=api_key,
    )


_session_llm_cache: dict[str, dict] = {}


@router.post("/session/start")
async def start_session(req: SessionStartRequest, background_tasks: BackgroundTasks):
    """Create a new agent builder session and kick off the pipeline."""
    session_id = await _session_mgr.create(
        user_id="anonymous",
        project_id=req.project_id,
    )

    resolved_key = _resolve_api_key(req.llm_provider, req.api_key)
    _session_llm_cache[session_id] = {
        "provider": req.llm_provider,
        "model": req.llm_model,
        "api_key": resolved_key,
    }

    llm = _get_llm(req)
    emitter = create_ws_emitter(session_id)
    orchestrator = MultiAgentOrchestrator(llm, _session_mgr, session_id, emitter)

    background_tasks.add_task(orchestrator.run_initial, req.prompt)

    return {"session_id": session_id, "status": "processing"}


@router.post("/session/{session_id}/message")
async def send_message(
    session_id: str,
    req: SessionMessageRequest,
    background_tasks: BackgroundTasks,
):
    """Send a follow-up message to an existing session."""
    session = await _session_mgr.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    cached = _session_llm_cache.get(session_id)
    if not cached:
        raise HTTPException(status_code=400, detail="Session LLM config not found. Start a new session.")

    from app.ai.llm.registry import get_llm
    llm = get_llm(
        provider=cached["provider"],
        model=cached["model"],
        api_key=cached["api_key"],
    )

    emitter = create_ws_emitter(session_id)
    orchestrator = MultiAgentOrchestrator(llm, _session_mgr, session_id, emitter)

    background_tasks.add_task(orchestrator.run_followup, req.message)

    return {"status": "processing"}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get the current state of a session."""
    session = await _session_mgr.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/session/{session_id}/approve")
async def approve_session(session_id: str):
    """Mark a session as completed (human approval)."""
    session = await _session_mgr.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await _session_mgr.update_status(session_id, "completed")

    emitter = create_ws_emitter(session_id)
    emitter("status_change", {"status": "completed"})

    return {"status": "completed"}


@router.post("/session/{session_id}/save")
async def save_to_file(session_id: str, project_id: str = None):
    """Save the built graph to a File record in the existing system."""
    session = await _session_mgr.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    graph = session.get("artifacts", {}).get("graph")
    if not graph:
        raise HTTPException(status_code=400, detail="No graph built yet")

    pid = project_id or session.get("project_id")
    if not pid:
        raise HTTPException(status_code=400, detail="project_id required")

    from app.db.session import AsyncSessionLocal
    from app.models.models import File

    graph_json = {"nodes": graph.get("nodes", []), "edges": graph.get("edges", [])}

    async with AsyncSessionLocal() as db:
        file = File(
            project_id=uuid.UUID(pid),
            name=f"Agent-Built Workflow",
            graph_json=graph_json,
        )
        db.add(file)
        await db.commit()
        await db.refresh(file)

    await _session_mgr.update_status(session_id, "completed")

    return {"file_id": str(file.id), "status": "saved"}
