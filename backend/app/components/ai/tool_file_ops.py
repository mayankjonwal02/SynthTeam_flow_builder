"""File Ops tool node — file read/write, connects via ai_tool handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_file_ops")
class ToolFileOpsComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        mode = config.get("mode", "read")
        tool_name = "file_read" if mode == "read" else "file_write"
        return {
            "__handle_type__": "ai_tool",
            "tool_name": tool_name,
            "base_path": config.get("base_path", "/tmp"),
        }
