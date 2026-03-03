import json
from typing import List
from app.ai.memory.manager import BaseMemory


class RedisMemoryBackend(BaseMemory):
    def __init__(self, redis_url: str = "redis://localhost:6379", **kwargs):
        self._url = redis_url
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(self._url, decode_responses=True)
        return self._client

    async def add(self, key: str, message: dict) -> None:
        client = await self._get_client()
        await client.rpush(f"memory:{key}", json.dumps(message))

    async def get(self, key: str, limit: int = 50) -> List[dict]:
        client = await self._get_client()
        items = await client.lrange(f"memory:{key}", -limit, -1)
        return [json.loads(i) for i in items]

    async def clear(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(f"memory:{key}")
