"""WebSocket endpoint for streaming multi-agent builder events."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.auth import decode_clerk_token

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

ConnectionStore: dict[str, set[WebSocket]] = defaultdict(set)

# Strong references so scheduled broadcasts aren't garbage-collected mid-flight
_pending: set[asyncio.Task] = set()

MAX_CONNECTIONS_PER_SESSION = 5
WS_POLICY_VIOLATION = 1008


async def broadcast(session_id: str, event_type: str, data: dict):
    """Send an event to all WebSocket connections for a session."""
    payload = json.dumps({
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, default=str)

    dead: list[WebSocket] = []
    for ws in list(ConnectionStore.get(session_id, set())):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)

    for ws in dead:
        ConnectionStore[session_id].discard(ws)


def create_ws_emitter(session_id: str):
    """Return a sync-safe callback that queues WS broadcasts.

    Must be created on the event loop. Agent tools call the emitter
    synchronously, sometimes from LangGraph worker threads that have no
    event loop, so those calls are handed back to the captured loop.
    """
    loop = asyncio.get_running_loop()
    loop_thread = threading.get_ident()

    def emitter(event_type: str, data: dict):
        coro = broadcast(session_id, event_type, data)
        try:
            if threading.get_ident() == loop_thread:
                task = loop.create_task(coro)
                _pending.add(task)
                task.add_done_callback(_pending.discard)
            else:
                asyncio.run_coroutine_threadsafe(coro, loop)
        except RuntimeError:
            coro.close()  # loop closed (shutdown)
    return emitter


@router.websocket("/ws/agent/{session_id}")
async def agent_ws(websocket: WebSocket, session_id: str):
    # Browsers can't set headers on WebSockets, so the Clerk token comes in the query string
    token = websocket.query_params.get("token", "")
    try:
        claims = decode_clerk_token(token)
    except HTTPException:
        await websocket.close(code=WS_POLICY_VIOLATION, reason="Unauthorized")
        return

    from app.multi_agent.api import get_session_manager

    try:
        session = await get_session_manager().get(session_id)
    except Exception:
        session = None
    if not session or session.get("user_id") != claims.get("sub"):
        await websocket.close(code=WS_POLICY_VIOLATION, reason="Session not found")
        return
    if len(ConnectionStore[session_id]) >= MAX_CONNECTIONS_PER_SESSION:
        await websocket.close(code=WS_POLICY_VIOLATION, reason="Too many connections")
        return

    await websocket.accept()
    ConnectionStore[session_id].add(websocket)
    logger.info(f"WS connected: session={session_id}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ConnectionStore[session_id].discard(websocket)
        if not ConnectionStore[session_id]:
            ConnectionStore.pop(session_id, None)
        logger.info(f"WS disconnected: session={session_id}")
