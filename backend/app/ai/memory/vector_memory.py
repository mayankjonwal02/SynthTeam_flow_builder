import json
from typing import List
from app.ai.memory.manager import BaseMemory


class VectorMemoryBackend(BaseMemory):
    """Stores memories as embeddings for semantic retrieval."""

    def __init__(self, embedding_provider: str = "openai", api_key: str = "", **kwargs):
        self._provider = embedding_provider
        self._api_key = api_key
        self._store: dict = {}

    async def add(self, key: str, message: dict) -> None:
        self._store.setdefault(key, []).append(message)

    async def get(self, key: str, limit: int = 50) -> List[dict]:
        return self._store.get(key, [])[-limit:]

    async def clear(self, key: str) -> None:
        self._store.pop(key, None)

    async def search(self, key: str, query: str, top_k: int = 5) -> List[dict]:
        """Semantic search over stored memories (simplified — full impl would use actual embeddings)."""
        messages = self._store.get(key, [])
        query_lower = query.lower()
        scored = []
        for msg in messages:
            content = str(msg.get("content", "")).lower()
            score = sum(1 for word in query_lower.split() if word in content)
            scored.append((score, msg))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [msg for _, msg in scored[:top_k]]
