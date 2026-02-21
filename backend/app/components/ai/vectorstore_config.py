"""Vector Store config node — provides vector DB config via ai_vectorstore handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("vectorstore_config")
class VectorStoreConfigComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_vectorstore",
            "provider": config.get("provider", "qdrant"),
            "collection": config.get("collection", "default"),
            "api_key": config.get("api_key", ""),
            "url": config.get("url", ""),
        }
