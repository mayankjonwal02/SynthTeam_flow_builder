"""Memory config node — provides memory backend config via ai_memory handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("memory_config")
class MemoryConfigComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_memory",
            "backend": config.get("backend", "in_memory"),
            "session_id": config.get("session_id", "default"),
            "ttl": int(config.get("ttl", 0)),
            "redis_url": config.get("redis_url", ""),
            "max_messages": int(config.get("max_messages", 50)),
        }
