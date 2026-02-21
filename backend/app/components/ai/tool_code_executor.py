"""Code Executor tool node — sandboxed Python execution, connects via ai_tool handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_code_executor")
class ToolCodeExecutorComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_tool",
            "tool_name": "code_executor",
            "timeout": int(config.get("timeout", 10)),
        }
