"""REST API for the multi-agent workflow builder."""

from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
import httpx

from app.multi_agent.schemas import (
    SecretsSubmitRequest,
    SessionMessageRequest,
    SessionStartRequest,
)
from app.multi_agent.session import SessionManager
from app.multi_agent.orchestrator import MultiAgentOrchestrator
from app.multi_agent.ws import create_ws_emitter

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/agent", tags=["agent-builder"])

_session_mgr = SessionManager()


@router.get("/ollama/models")
async def list_ollama_models():
    """List Ollama models using OLLAMA_BASE_URL (e.g. host.docker.internal:11500 for Docker)."""
    from app.core.config import settings
    base_url = (getattr(settings, "OLLAMA_BASE_URL", None) or "http://localhost:11434").rstrip("/")
    url = f"{base_url}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            models = [m.get("name", m.get("model", "")) for m in data.get("models", []) if m.get("name") or m.get("model")]
            return {"models": models}
    except httpx.ConnectError as e:
        logger.warning(f"Ollama connection failed ({url}): {e}")
        raise HTTPException(status_code=503, detail=f"Cannot reach Ollama at {base_url}. Check OLLAMA_BASE_URL and that Ollama is running.")
    except httpx.HTTPStatusError as e:
        logger.warning(f"Ollama API error: {e}")
        raise HTTPException(status_code=502, detail=f"Ollama returned {e.response.status_code}")
    except Exception as e:
        logger.warning(f"Ollama models list failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


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


def _get_llm(provider: str, model: str, api_key: str | None = None, temperature: float = 0.7, **extra):
    from app.ai.llm.registry import get_llm
    from app.core.config import settings
    key = _resolve_api_key(provider, api_key)
    kwargs = dict(extra)
    if provider == "ollama":
        kwargs["base_url"] = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434") or "http://localhost:11434"
    return get_llm(
        provider=provider,
        model=model,
        api_key=key,
        temperature=temperature,
        **kwargs,
    )


async def _run_agent_after_start(session_id: str, prompt: str):
    """Run the orchestrator for the first message so the client receives WS events."""
    await asyncio.sleep(0.5)  # give client time to connect to WebSocket
    session = await _session_mgr.get(session_id)
    if not session or not prompt.strip():
        return
    llm = _llm_from_session_or_request(session)
    orchestrator = MultiAgentOrchestrator(
        llm=llm,
        session_mgr=_session_mgr,
        session_id=session_id,
        ws_emitter=create_ws_emitter(session_id),
    )
    try:
        await orchestrator.run_initial(prompt)
    except Exception as exc:
        logger.exception(f"Agent run failed for session {session_id}: {exc}")


async def _start_session_impl(request: SessionStartRequest, background_tasks: BackgroundTasks | None = None):
    """Create a new multi-agent builder session. If prompt is set, run the agent in the background."""
    session_id = await _session_mgr.create(user_id=request.user_id, project_id=request.project_id)
    await _session_mgr.update_artifact(
        session_id,
        "llm_config",
        {
            "llm_provider": request.llm_provider,
            "llm_model": request.llm_model,
            "api_key": request.api_key,
        },
    )
    logger.info(f"Started session {session_id}")
    if request.prompt and request.prompt.strip() and background_tasks:
        background_tasks.add_task(_run_agent_after_start, session_id, request.prompt.strip())
    return {"session_id": session_id}


@router.post("/session")
async def start_session(request: SessionStartRequest, background_tasks: BackgroundTasks):
    """Create a new multi-agent builder session (POST /agent/session)."""
    return await _start_session_impl(request, background_tasks)


@router.post("/session/start")
async def start_session_alias(request: SessionStartRequest, background_tasks: BackgroundTasks):
    """Create a new session — alias for POST /session (copilot uses /agent/session/start). Runs agent if prompt is provided."""
    return await _start_session_impl(request, background_tasks)


def _llm_from_session_or_request(session: dict, request: SessionMessageRequest | None = None):
    """Build LLM from session's llm_config, with optional overrides from request."""
    cfg = (session.get("artifacts") or {}).get("llm_config") or {}
    provider = (request and request.llm_provider) or cfg.get("llm_provider", "ollama")
    model = (request and request.llm_model) or cfg.get("llm_model", "llama3.1:8b")
    api_key = (request and request.api_key) or cfg.get("api_key")
    return _get_llm(provider=provider, model=model, api_key=api_key)


@router.post("/session/{session_id}/message")
async def send_message(session_id: str, request: SessionMessageRequest):
    """Send a message to the multi-agent system."""
    session = await _session_mgr.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    llm = _llm_from_session_or_request(session, request)
    orchestrator = MultiAgentOrchestrator(
        llm=llm,
        session_mgr=_session_mgr,
        session_id=session_id,
        ws_emitter=create_ws_emitter(session_id),
    )

    if getattr(request, "is_followup", False):
        await orchestrator.run_followup(request.message)
    else:
        await orchestrator.run_initial(request.message)

    return {"status": "processing"}


@router.post("/session/{session_id}/secrets")
async def submit_secrets(session_id: str, request: SecretsSubmitRequest):
    """Submit secret values (API keys, passwords) that the builder requested."""
    session = await _session_mgr.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Store secrets in session artifacts
    secrets = session.get("artifacts", {}).get("secrets", {})
    secrets.update(request.secrets)
    await _session_mgr.update_artifact(session_id, "secrets", secrets)

    # Resume the workflow
    llm = _llm_from_session_or_request(session)
    orchestrator = MultiAgentOrchestrator(
        llm=llm,
        session_mgr=_session_mgr,
        session_id=session_id,
        ws_emitter=create_ws_emitter(session_id),
    )

    await orchestrator.run_followup("User submitted secrets")

    return {"status": "processing"}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session state."""
    session = await _session_mgr.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


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


# Optimized system integration
@router.post("/optimized/build")
async def build_workflow_optimized(request: SessionStartRequest):
    """Build workflow using optimized multi-agent system (faster, reduced hallucination)."""
    from app.multi_agent.optimized_system import process_optimized_workflow_request
    
    try:
        llm = _get_llm(
            provider=request.llm_provider,
            model=request.llm_model,
            api_key=request.api_key,
        )
        result = await process_optimized_workflow_request(
            user_message=request.prompt,
            llm=llm,
            session_manager=_session_mgr,
        )
        
        return {
            "session_id": result["session_id"],
            "status": result["status"],
            "success": result["success"],
            "performance_metrics": result.get("performance_metrics", {}),
            "optimization_enabled": True
        }
        
    except Exception as exc:
        logger.error(f"Optimized build failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Optimized build failed: {exc}")


@router.get("/optimized/performance")
async def get_performance_metrics():
    """Get system performance metrics and optimization statistics."""
    from app.multi_agent import get_system_performance_report
    
    try:
        report = get_system_performance_report()
        return {
            "system_status": "healthy",
            "optimization_enabled": True,
            "performance_report": report,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as exc:
        logger.error(f"Failed to get performance metrics: {exc}")
        raise HTTPException(status_code=500, detail=f"Performance metrics unavailable: {exc}")


@router.get("/optimized/status/{session_id}")
async def get_optimized_session_status(session_id: str):
    """Get status of an optimized session."""
    from app.multi_agent.optimized_system import OptimizedMultiAgentSystem
    
    try:
        session = await _session_mgr.get(session_id)
        llm = _llm_from_session_or_request(session) if session else _get_llm(provider="ollama", model="llama3.1:8b")
        system = OptimizedMultiAgentSystem(
            llm=llm,
            session_manager=_session_mgr,
            session_id=session_id
        )
        
        status = await system.get_session_status()
        return status
        
    except Exception as exc:
        logger.error(f"Failed to get optimized session status: {exc}")
        raise HTTPException(status_code=500, detail=f"Session status unavailable: {exc}")


@router.post("/optimized/cancel/{session_id}")
async def cancel_optimized_session(session_id: str):
    """Cancel an optimized session."""
    try:
        session = await _session_mgr.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Mark session as cancelled
        session["status"] = "cancelled"
        await _session_mgr.update(session_id, session)
        
        return {"message": "Session cancelled", "session_id": session_id}
        
    except Exception as exc:
        logger.error(f"Failed to cancel session: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel session: {exc}")