"""LLM Model config node — provides model configuration via ai_model handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("llm_model")
class LLMModelComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_model",
            "provider": config.get("provider") or "openai",
            "model": config.get("model") or "gpt-4o-mini",
            "api_key": config.get("api_key", ""),
            "temperature": float(config.get("temperature") or 0.7),
            "max_tokens": config.get("max_tokens") or None,
            "base_url": config.get("base_url") or None,
        }
