"""HTTP Request tool node — config for making HTTP calls, connects via ai_tool handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_http_request")
class ToolHttpRequestComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_tool",
            "tool_name": "http_request",
            "allowed_methods": config.get("allowed_methods", "GET,POST"),
            "timeout": int(config.get("timeout", 30)),
        }
