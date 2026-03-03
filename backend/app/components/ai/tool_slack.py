"""Slack tool node — sends Slack notifications via webhook, connects via ai_tool handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_slack")
class ToolSlackComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_tool",
            "tool_name": "slack_notifier",
            "webhook_url": config.get("webhook_url", ""),
        }
