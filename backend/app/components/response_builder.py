"""
Response Builder Component — the terminal node in a pipeline.

Collects data from upstream nodes and builds the final API response
using `field_mappings` from the node's config.

Each field mapping has:
  - name:   the response field name
  - type:   the data type (string, int, float, bool)
  - source: "input" (pull from upstream data) or "static" (hardcoded value)
  - value:  for input → the key to look up; for static → the literal value

Falls back to the old `response_schema` behavior if no field_mappings exist.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


_COERCE = {
    "string":   str,
    "int":      lambda v: int(v) if v != "" else 0,
    "float":    lambda v: float(v) if v != "" else 0.0,
    "bool":     lambda v: v.lower() in ("true", "1", "yes") if isinstance(v, str) else bool(v),
    "list":     lambda v: list(v) if not isinstance(v, list) else v,
    "dict":     lambda v: dict(v) if not isinstance(v, dict) else v,
    "json":     lambda v: dict(v) if not isinstance(v, dict) else v,
    "base64":   str,
    "bytes":    str,
    "image":    str,
    "audio":    str,
    "video":    str,
    "file":     str,
    "date":     str,
    "datetime": str,
    "url":      str,
    "email":    str,
    "uuid":     str,
    "any":      lambda v: v,
}


@register_component("response_builder")
class ResponseBuilderComponent(BaseComponent):

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

        if field_mappings:
            response: dict = {}
            for mapping in field_mappings:
                name   = mapping["name"]
                ftype  = mapping.get("type", "string")
                source = mapping.get("source", "input")
                value  = mapping.get("value", "")

                if source == "input":
                    raw = merged.get(value, merged.get(name))
                    if raw is not None:
                        response[name] = raw
                    else:
                        defaults = {"string": "", "int": 0, "float": 0.0, "bool": False}
                        response[name] = defaults.get(ftype, None)
                else:
                    coercer = _COERCE.get(ftype, str)
                    try:
                        response[name] = coercer(value)
                    except (ValueError, TypeError):
                        response[name] = value

            return response

        schema = config.get("response_schema", {})

        if not schema:
            return merged

        response = {}
        for field_name, field_type in schema.items():
            if field_name in merged:
                response[field_name] = merged[field_name]
            else:
                defaults = {"string": "", "int": 0, "float": 0.0, "bool": False}
                response[field_name] = defaults.get(field_type, None)

        return response
