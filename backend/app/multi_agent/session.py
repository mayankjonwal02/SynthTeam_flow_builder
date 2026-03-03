"""Session manager for multi-agent builder — Redis cache + Postgres persistence."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from app.db.session import AsyncSessionLocal
from app.models.models import AgentSession

logger = logging.getLogger("uvicorn.error")

REDIS_TTL = 3600  # 1 hour


class SessionManager:

    def __init__(self, redis_url: str | None = None):
        if redis_url is None:
            try:
                from app.core.config import settings
                redis_url = settings.REDIS_URL
            except Exception:
                redis_url = "redis://localhost:6379"
        self._redis_url = redis_url
        self._redis = None
        self._redis_failed = False

    async def _get_redis(self):
        if self._redis_failed:
            return None
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception as exc:
                logger.warning(f"Redis unavailable, using Postgres only: {exc}")
                self._redis = None
                self._redis_failed = True
        return self._redis

    def _redis_key(self, session_id: str) -> str:
        return f"agent_session:{session_id}"

    async def create(self, user_id: str, project_id: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        session_data = {
            "id": session_id,
            "user_id": user_id,
            "project_id": project_id,
            "status": "active",
            "conversation": [],
            "artifacts": {},
            "created_at": now,
        }

        async with AsyncSessionLocal() as db:
            row = AgentSession(
                id=uuid.UUID(session_id),
                user_id=user_id,
                project_id=uuid.UUID(project_id) if project_id else None,
                status="active",
                conversation=[],
                artifacts={},
            )
            db.add(row)
            await db.commit()

        redis = await self._get_redis()
        if redis:
            await redis.set(
                self._redis_key(session_id),
                json.dumps(session_data),
                ex=REDIS_TTL,
            )

        return session_id

    async def get(self, session_id: str) -> Optional[dict]:
        redis = await self._get_redis()
        if redis:
            cached = await redis.get(self._redis_key(session_id))
            if cached:
                await redis.expire(self._redis_key(session_id), REDIS_TTL)
                return json.loads(cached)

        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(AgentSession).where(AgentSession.id == uuid.UUID(session_id))
            )
            row = res.scalar()
            if not row:
                return None

            data = {
                "id": str(row.id),
                "user_id": row.user_id,
                "project_id": str(row.project_id) if row.project_id else None,
                "status": row.status,
                "conversation": row.conversation or [],
                "artifacts": row.artifacts or {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }

            if redis:
                await redis.set(
                    self._redis_key(session_id), json.dumps(data), ex=REDIS_TTL
                )

            return data

    async def _persist(self, session_id: str, data: dict):
        if data.get("_redis_only"):
            return

        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(AgentSession).where(AgentSession.id == uuid.UUID(session_id))
            )
            row = res.scalar()
            if row:
                row.status = data.get("status", row.status)
                row.conversation = data.get("conversation", row.conversation)
                row.artifacts = data.get("artifacts", row.artifacts)
                await db.commit()

    async def _save(self, session_id: str, data: dict):
        redis = await self._get_redis()
        if redis:
            await redis.set(
                self._redis_key(session_id), json.dumps(data), ex=REDIS_TTL
            )
        await self._persist(session_id, data)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        data = await self.get(session_id)
        if not data:
            return
        msg = {
            "role": role,
            "content": content,
            "agent": agent,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        data["conversation"].append(msg)
        await self._save(session_id, data)

    async def update_status(self, session_id: str, status: str):
        data = await self.get(session_id)
        if not data:
            return
        data["status"] = status
        await self._save(session_id, data)

    async def update_artifact(self, session_id: str, key: str, value: Any):
        data = await self.get(session_id)
        if not data:
            return
        data["artifacts"][key] = value
        await self._save(session_id, data)

    async def get_conversation(self, session_id: str, limit: int = 50) -> list[dict]:
        data = await self.get(session_id)
        if not data:
            return []
        return data["conversation"][-limit:]
