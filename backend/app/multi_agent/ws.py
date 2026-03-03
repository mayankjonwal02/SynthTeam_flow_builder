"""WebSocket endpoint for streaming multi-agent builder events."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

ConnectionStore: dict[str, set[WebSocket]] = defaultdict(set)


async def broadcast(session_id: str, event_type: str, data: dict):
    """Send an event to all WebSocket connections for a session."""
    payload = json.dumps({
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
    })

    dead: list[WebSocket] = []
    for ws in ConnectionStore.get(session_id, set()):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)

    for ws in dead:
        ConnectionStore[session_id].discard(ws)


def create_ws_emitter(session_id: str):
    """Return a sync-safe callback that queues WS broadcasts.

    Agent tools call this synchronously, so we schedule the coroutine
    onto the running event loop rather than awaiting directly.
    """
    def emitter(event_type: str, data: dict):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast(session_id, event_type, data))
        except RuntimeError:
            pass
    return emitter


@router.websocket("/ws/agent/{session_id}")
async def agent_ws(websocket: WebSocket, session_id: str):
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
            del ConnectionStore[session_id]
        logger.info(f"WS disconnected: session={session_id}")
