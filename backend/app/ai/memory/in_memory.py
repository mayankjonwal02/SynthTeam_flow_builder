from typing import Dict, List
from app.ai.memory.manager import BaseMemory

_STORE: Dict[str, List[dict]] = {}

# Per-conversation cap so a long-running process can't grow without bound
MAX_MESSAGES_PER_KEY = 1000


class InMemoryBackend(BaseMemory):
    """Process-local memory; lost on restart. Accepts and ignores backend options."""

    def __init__(self, **kwargs):
        pass

    async def add(self, key: str, message: dict) -> None:
        messages = _STORE.setdefault(key, [])
        messages.append(message)
        if len(messages) > MAX_MESSAGES_PER_KEY:
            del messages[: len(messages) - MAX_MESSAGES_PER_KEY]

    async def get(self, key: str, limit: int = 50) -> List[dict]:
        return _STORE.get(key, [])[-limit:]

    async def clear(self, key: str) -> None:
        _STORE.pop(key, None)
