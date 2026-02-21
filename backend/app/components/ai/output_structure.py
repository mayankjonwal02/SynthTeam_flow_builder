"""Output Structure config node — provides JSON schema via ai_structure handle."""

import json
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("output_structure")
class OutputStructureComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        schema = config.get("schema", "{}")
        if isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except (json.JSONDecodeError, TypeError):
                schema = {}
        return {
            "__handle_type__": "ai_structure",
            "schema": schema,
        }
