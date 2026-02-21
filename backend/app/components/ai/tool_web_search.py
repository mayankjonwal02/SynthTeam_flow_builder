"""Web Search tool node — config for Tavily web search, connects via ai_tool handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_web_search")
class ToolWebSearchComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_tool",
            "tool_name": "web_search",
            "api_key": config.get("api_key", ""),
            "max_results": int(config.get("max_results", 5)),
        }
