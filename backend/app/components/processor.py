"""
Echo Processor Component — a pass-through / transformation node.

In its default mode it merges all upstream inputs into a single dict
and returns them unchanged ("echo").  This serves as the base template
for future processor types (LLM calls, data transforms, etc.).
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("echo_processor")
class EchoProcessorComponent(BaseComponent):

    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> dict:
        merged: dict = {}
        for _node_id, output in inputs.items():
            if isinstance(output, dict):
                merged.update(output)
            else:
                merged[_node_id] = output

        return merged
