from typing import Dict, List
from app.ai.memory.manager import BaseMemory

_STORE: Dict[str, List[dict]] = {}


class InMemoryBackend(BaseMemory):
    async def add(self, key: str, message: dict) -> None:
        _STORE.setdefault(key, []).append(message)

    async def get(self, key: str, limit: int = 50) -> List[dict]:
        return _STORE.get(key, [])[-limit:]

    async def clear(self, key: str) -> None:
        _STORE.pop(key, None)
