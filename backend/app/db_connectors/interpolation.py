"""
Variable interpolation utility for DB node configs.

Supports three modes:
  - interpolate: Replace {{input.field_name}} placeholders
  - evaluate_expression: Evaluate expressions like input.data.field or input.items[0]
  - resolve_field_mapping: Process a field mapping with mode (static/input/expression)
"""

import re
from typing import Any, List


def interpolate(template: Any, context: dict) -> Any:
    """
    Recursively replace {{input.field}} with values from context.

    Supports str, dict, and list templates.
    """
    if isinstance(template, str):
        def _replace(match):
            key = match.group(1)
            val = context.get(key, "")
            return str(val) if val is not None else ""
        return re.sub(r"\{\{input\.(\w+)\}\}", _replace, template)

    if isinstance(template, dict):
        return {k: interpolate(v, context) for k, v in template.items()}

    if isinstance(template, list):
        return [interpolate(v, context) for v in template]

    return template


def evaluate_expression(expr: str, context: dict) -> Any:
    """
    Evaluate a dot-notation expression against context.
    
    Supports:
      - input.field → context["field"]
      - input.data.name → context["data"]["name"]
      - input.items[0] → context["items"][0]
      - input.items[0].name → context["items"][0]["name"]
    """
    if not expr:
        return None
    
    expr = expr.strip()
    if expr.startswith("input."):
        expr = expr[6:]
    
    parts = re.split(r'\.|\[|\]', expr)
    parts = [p for p in parts if p]
    
    result = context
    for part in parts:
        if result is None:
            return None
        try:
            if part.isdigit():
                result = result[int(part)]
            else:
                result = result.get(part) if isinstance(result, dict) else getattr(result, part, None)
        except (KeyError, IndexError, TypeError, AttributeError):
            return None
    
    return result


def resolve_field_mapping(mapping: dict, context: dict) -> Any:
    """
    Resolve a single field mapping based on its mode.

    Modes:
      - static:     return the literal value as-is
      - input:      flat key lookup → context.get(value)
      - expression: dot-path / bracket traversal → context["a"]["b"][0]["c"]
    """
    mode = mapping.get("mode", "expression")
    value = mapping.get("value", "")

    if mode == "static":
        return value
    elif mode == "input":
        key = value.strip()
        if key.startswith("input."):
            key = key[6:]
        if not key or key == "input":
            return context
        return context.get(key)
    elif mode == "expression":
        if value.startswith("{{") and value.endswith("}}"):
            value = value[2:-2].strip()
        val = value.strip()
        if not val or val == "input":
            return context
        return evaluate_expression(val, context)

    return value


def resolve_filter_mappings(mappings: List[dict], context: dict) -> dict:
    """
    Convert a list of filter mappings into a filter dict.
    
    Each mapping: {"key": "fieldName", "mode": "...", "value": "..."}
    Returns: {"fieldName": resolved_value, ...}
    """
    result = {}
    for mapping in mappings:
        key = mapping.get("key", "")
        if key:
            result[key] = resolve_field_mapping(mapping, context)
    return result
