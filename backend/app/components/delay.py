"""
Delay Component — pauses execution for a configurable duration.

Config:
    { "seconds": "5", "seconds_mode": "static" }

Supports field modes: static value, input reference, or expression.
"""

import asyncio
from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.db_connectors.interpolation import resolve_field_mapping


@register_component("delay")
class DelayComponent(BaseComponent):
    """Sleeps for the configured duration then passes upstream data through."""

    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> dict:
        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        seconds_mapping = {
            "mode": config.get("seconds_mode", "static"),
            "value": config.get("seconds", "1"),
        }
        raw_seconds = resolve_field_mapping(seconds_mapping, merged)

        try:
            seconds = max(0, float(raw_seconds))
        except (ValueError, TypeError):
            seconds = 1

        await asyncio.sleep(seconds)

        return merged
