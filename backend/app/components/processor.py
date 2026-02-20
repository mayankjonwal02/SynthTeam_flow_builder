"""
Echo Processor Component — a pass-through / transformation node.

In its default mode (no field_mappings) it merges all upstream inputs into
a single dict and returns them unchanged ("echo").

When field_mappings are provided, it builds a new dict with the specified
fields resolved via static/input/expression modes.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.db_connectors.interpolation import resolve_field_mapping


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

        field_mappings = config.get("field_mappings")
        if not field_mappings:
            return merged

        result: dict = {}
        for mapping in field_mappings:
            name = mapping.get("name", "")
            if not name:
                continue
            resolved = resolve_field_mapping({
                "mode": mapping.get("source", "expression"),
                "value": mapping.get("value", ""),
            }, merged)
            result[name] = resolved

        return result
