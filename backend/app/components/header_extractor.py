"""
Header Extractor Component — extracts selected HTTP headers from the
request and returns them as a dict.

Config:
    { "headers": ["authorization", "x-request-id"] }

Requires that the endpoint handler injects request headers into
request_data["__headers__"].
"""

from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("header_extractor")
class HeaderExtractorComponent(BaseComponent):
    """Extracts configured headers from the request and merges with upstream data."""

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

        raw_headers = request_data.get("__headers__", {})
        wanted = config.get("headers", [])

        extracted: dict = {}
        for h in wanted:
            key = h.lower()
            if key in raw_headers:
                extracted[key] = raw_headers[key]

        merged["__extracted_headers__"] = extracted
        return merged
