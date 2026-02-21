"""Gmail tool node — sends email via Gmail SMTP. Config: email, app password. Agent chooses: to, subject, body."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_gmail")
class ToolGmailComponent(BaseComponent):
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_tool",
            "tool_name": "gmail_sender",
            "email": config.get("email", "").strip(),
            "password": config.get("app_password", config.get("password", "")).strip(),
        }
