"""
Webhook Trigger Component — entry-point node that receives external
webhook POST requests.

Config:
    { "path": "/webhook/order" }

During compilation the path comes from config.path and the route is
registered as POST. The component itself passes the body through,
optionally filtering by a schema.
"""

from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("webhook_trigger")
class WebhookTriggerComponent(BaseComponent):
    """Passes the incoming webhook payload through."""

    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> dict:
        schema = config.get("request_schema", {})
        if not schema:
            return dict(request_data)

        extracted: dict = {}
        for field_name in schema:
            if field_name in request_data:
                extracted[field_name] = request_data[field_name]
        return extracted
