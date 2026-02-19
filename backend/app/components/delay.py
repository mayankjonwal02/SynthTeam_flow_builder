"""
Delay Component — pauses execution for a configurable duration.

Config:
    { "seconds": 5 }
"""

import asyncio
from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("delay")
class DelayComponent(BaseComponent):
    """Sleeps for the configured duration then passes upstream data through."""

    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> dict:
        seconds = config.get("seconds", 1)
        await asyncio.sleep(seconds)

        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)
        return merged
