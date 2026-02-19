"""
Manual Trigger Component — entry-point node for testing workflows.

Behaves like http_entry but without schema extraction: passes the
entire request body through unchanged.
"""

from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("manual_trigger")
class ManualTriggerComponent(BaseComponent):
    """Passes the full request body through without filtering."""

    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> dict:
        return dict(request_data)
