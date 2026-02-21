"""Embedding Model config node — provides embedding config via ai_embedding handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("embedding_model")
class EmbeddingModelComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_embedding",
            "provider": config.get("provider", "openai"),
            "model": config.get("model", ""),
            "api_key": config.get("api_key", ""),
        }
