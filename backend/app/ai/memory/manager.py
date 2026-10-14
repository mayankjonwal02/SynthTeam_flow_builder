"""Memory Manager — pluggable backends for agent conversation memory."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("uvicorn.error")


class MemoryManager:
    """Factory for creating memory backends."""

    @staticmethod
    def create(backend: str = "in_memory", **kwargs) -> "BaseMemory":
        # Empty values from node configs mean "use the default"
        kwargs = {k: v for k, v in kwargs.items() if v not in (None, "")}
        if backend == "redis" and "redis_url" not in kwargs:
            from app.core.config import settings
            kwargs["redis_url"] = settings.REDIS_URL
        if backend == "in_memory":
            from app.ai.memory.in_memory import InMemoryBackend
            return InMemoryBackend(**kwargs)
        elif backend == "redis":
            from app.ai.memory.redis_memory import RedisMemoryBackend
            return RedisMemoryBackend(**kwargs)
        elif backend == "vector":
            from app.ai.memory.vector_memory import VectorMemoryBackend
            return VectorMemoryBackend(**kwargs)
        raise ValueError(f"Unknown memory backend: {backend}")


class BaseMemory:
    """Interface for memory backends."""

    async def add(self, key: str, message: dict) -> None:
        raise NotImplementedError

    async def get(self, key: str, limit: int = 50) -> List[dict]:
        raise NotImplementedError

    async def clear(self, key: str) -> None:
        raise NotImplementedError
