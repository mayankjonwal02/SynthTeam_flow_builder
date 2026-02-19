"""
HTTP Entry Component — the first node in every pipeline.

Extracts fields from the incoming request body based on the
`request_schema` defined in the node's config.  If no schema is
specified, the entire request body is forwarded as-is.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("http_entry")
class HttpEntryComponent(BaseComponent):

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
