"""Email tool node — sends email via SMTP, connects via ai_tool handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_email")
class ToolEmailComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        return {
            "__handle_type__": "ai_tool",
            "tool_name": "email_sender",
            "smtp_host": config.get("smtp_host", ""),
            "smtp_port": int(config.get("smtp_port") or 587),
            "username": config.get("username", ""),
            "password": config.get("password", ""),
            "from_email": config.get("from_email", ""),
        }
