"""REST API for the multi-agent workflow builder."""

from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
import httpx

from app.core.auth import verify_token

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

# Sessions with a pipeline currently running (one run at a time per session)
_running: set[str] = set()


def get_session_manager() -> SessionManager:
    return _session_mgr


async def _get_owned_session(session_id: str, user: dict) -> dict:
    """Load a session and make sure it belongs to the caller (404 otherwise)."""
    try:
        session = await _session_mgr.get(session_id)
    except ValueError:  # malformed id
        session = None
    if not session or session.get("user_id") != user.get("sub"):
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _public_session(session: dict) -> dict:
    """Session as returned to the browser: never echo stored API keys or secrets."""
    data = dict(session)
    artifacts = dict(data.get("artifacts") or {})
    llm_cfg = dict(artifacts.get("llm_config") or {})
    if llm_cfg.pop("api_key", None):
        llm_cfg["has_api_key"] = True
    artifacts["llm_config"] = llm_cfg
    artifacts.pop("secrets", None)
    data["artifacts"] = artifacts
    return data


@router.get("/ollama/models")
async def list_ollama_models(user=Depends(verify_token)):
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


_PROVIDER_ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
}


def _resolve_api_key(provider: str, explicit_key: str | None) -> str | None:
    """Return the explicit key if provided, otherwise the provider's env var (or None)."""
    if explicit_key:
        return explicit_key
    import os
    from app.core.config import settings

    env_name = _PROVIDER_ENV_KEYS.get(provider)
    if not env_name:
        return None
    return getattr(settings, env_name, "") or os.environ.get(env_name) or None


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


async def _run_pipeline(session_id: str, message: str, request: SessionMessageRequest | None = None,
                        *, delay: float = 0.0):
    """
    Run the orchestrator for a message in the background; progress goes out over WS.

    The first user message runs the full pipeline; later ones are follow-ups
    (answers to clarification questions or change requests).
    """
    if delay:
        await asyncio.sleep(delay)  # give the client time to open its WebSocket
    emit = create_ws_emitter(session_id)
    try:
        session = await _session_mgr.get(session_id)
        if not session or not message.strip():
            return
        has_user_message = any(m.get("role") == "user" for m in session.get("conversation", []))
        is_followup = request.is_followup if request and request.is_followup is not None else has_user_message
        orchestrator = MultiAgentOrchestrator(
            llm=_llm_from_session_or_request(session, request),
            session_mgr=_session_mgr,
            session_id=session_id,
            ws_emitter=emit,
        )
        if is_followup:
            await orchestrator.run_followup(message)
        else:
            await orchestrator.run_initial(message)
    except Exception as exc:
        logger.exception(f"Agent run failed for session {session_id}: {exc}")
        emit("error", {"message": f"Agent run failed: {exc}"})
        try:
            await _session_mgr.update_status(session_id, "failed")
        except Exception:
            pass
    finally:
        _running.discard(session_id)


def _schedule_run(background_tasks: BackgroundTasks, session_id: str, message: str,
                  request: SessionMessageRequest | None = None, delay: float = 0.0):
    if session_id in _running:
        raise HTTPException(status_code=409, detail="The agents are still working on this session")
    _running.add(session_id)
    background_tasks.add_task(_run_pipeline, session_id, message, request, delay=delay)


async def _start_session_impl(request: SessionStartRequest, user: dict, background_tasks: BackgroundTasks):
    """Create a new multi-agent builder session. If prompt is set, run the agent in the background."""
    if request.project_id:
        from app.api.deps import get_owned_project
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await get_owned_project(db, request.project_id, user)
    session_id = await _session_mgr.create(user_id=user["sub"], project_id=request.project_id)
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
    if request.prompt and request.prompt.strip():
        _schedule_run(background_tasks, session_id, request.prompt.strip(), delay=0.5)
    return {"session_id": session_id}


@router.post("/session")
async def start_session(request: SessionStartRequest, background_tasks: BackgroundTasks,
                        user=Depends(verify_token)):
    """Create a new multi-agent builder session (POST /agent/session)."""
    return await _start_session_impl(request, user, background_tasks)


@router.post("/session/start")
async def start_session_alias(request: SessionStartRequest, background_tasks: BackgroundTasks,
                              user=Depends(verify_token)):
    """Create a new session — alias for POST /session (copilot uses /agent/session/start). Runs agent if prompt is provided."""
    return await _start_session_impl(request, user, background_tasks)


def _llm_from_session_or_request(session: dict, request: SessionMessageRequest | None = None):
    """Build LLM from session's llm_config, with optional overrides from request."""
    cfg = (session.get("artifacts") or {}).get("llm_config") or {}
    provider = (request and request.llm_provider) or cfg.get("llm_provider", "ollama")
    model = (request and request.llm_model) or cfg.get("llm_model", "llama3.1:8b")
    api_key = (request and request.api_key) or cfg.get("api_key")
    return _get_llm(provider=provider, model=model, api_key=api_key)


@router.post("/session/{session_id}/message")
async def send_message(session_id: str, request: SessionMessageRequest,
                       background_tasks: BackgroundTasks, user=Depends(verify_token)):
    """Send a message to the multi-agent system; progress streams over the WebSocket."""
    await _get_owned_session(session_id, user)
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message is empty")
    _schedule_run(background_tasks, session_id, request.message, request)
    return {"status": "processing"}


@router.post("/session/{session_id}/secrets")
async def submit_secrets(session_id: str, request: SecretsSubmitRequest,
                         background_tasks: BackgroundTasks, user=Depends(verify_token)):
    """Fill the secret fields (API keys, passwords) the builder asked for, then resume."""
    session = await _get_owned_session(session_id, user)

    graph = (session.get("artifacts") or {}).get("graph") or {}
    nodes_by_id = {n.get("id"): n for n in graph.get("nodes", [])}
    for node_id, fields in request.secrets.items():
        node = nodes_by_id.get(node_id)
        if not node:
            continue
        config = node.setdefault("data", {}).setdefault("config", {})
        for key, value in fields.items():
            if value:
                config[key] = value
    await _session_mgr.update_artifact(session_id, "graph", graph)

    _schedule_run(background_tasks, session_id, "User submitted secrets",
                  SessionMessageRequest(message="User submitted secrets", is_followup=True))
    return {"status": "processing"}


@router.get("/session/{session_id}")
async def get_session(session_id: str, user=Depends(verify_token)):
    """Get session state (without stored API keys or secrets)."""
    session = await _get_owned_session(session_id, user)
    return _public_session(session)


@router.post("/session/{session_id}/approve")
async def approve_session(session_id: str, user=Depends(verify_token)):
    """User accepts the built workflow as final (the reviewer's 'approved' -> 'completed')."""
    session = await _get_owned_session(session_id, user)
    if not (session.get("artifacts") or {}).get("graph"):
        raise HTTPException(status_code=400, detail="No graph built yet")
    await _session_mgr.update_status(session_id, "completed")
    create_ws_emitter(session_id)("status_change", {"status": "completed"})
    return {"status": "completed"}


@router.post("/session/{session_id}/save")
async def save_to_file(session_id: str, project_id: str | None = None, name: str | None = None,
                       user=Depends(verify_token)):
    """Save the built graph as a workflow file in one of the caller's projects."""
    session = await _get_owned_session(session_id, user)

    graph = session.get("artifacts", {}).get("graph")
    if not graph:
        raise HTTPException(status_code=400, detail="No graph built yet")

    pid = project_id or session.get("project_id")
    if not pid:
        raise HTTPException(status_code=400, detail="project_id required")

    from app.api.deps import get_owned_project
    from app.db.session import AsyncSessionLocal
    from app.models.models import File

    graph_json = {"nodes": graph.get("nodes", []), "edges": graph.get("edges", [])}

    async with AsyncSessionLocal() as db:
        project = await get_owned_project(db, pid, user)
        file = File(
            project_id=project.id,
            name=(name or "").strip() or "Agent-Built Workflow",
            graph_json=graph_json,
        )
        db.add(file)
        await db.commit()
        await db.refresh(file)

    await _session_mgr.update_status(session_id, "completed")

    return {"file_id": str(file.id), "project_id": str(project.id), "status": "saved"}


# Optimized system integration
@router.post("/optimized/build")
async def build_workflow_optimized(request: SessionStartRequest, user=Depends(verify_token)):
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
            user_id=user["sub"],
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
async def get_performance_metrics(user=Depends(verify_token)):
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
async def get_optimized_session_status(session_id: str, user=Depends(verify_token)):
    """Get status of an optimized session."""
    from app.multi_agent.optimized_system import OptimizedMultiAgentSystem

    session = await _get_owned_session(session_id, user)
    try:
        llm = _llm_from_session_or_request(session)
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
async def cancel_optimized_session(session_id: str, user=Depends(verify_token)):
    """Cancel an optimized session."""
    await _get_owned_session(session_id, user)
    await _session_mgr.update_status(session_id, "cancelled")
    return {"message": "Session cancelled", "session_id": session_id}