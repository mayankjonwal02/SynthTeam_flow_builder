"""Workflow Invoker tool node — calls other deployed workflows, connects via ai_tool handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_workflow")
class ToolWorkflowComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_tool",
            "tool_name": "workflow_invoker",
            "workflow_url": config.get("workflow_url", ""),
            "method": config.get("method", "POST"),
        }
