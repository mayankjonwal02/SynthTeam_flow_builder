"""
If-Condition Component — evaluates a boolean condition on upstream data.

Config:
    {
        "field":      "age",
        "field_mode": "expression",   # static | input | expression
        "operator":   ">",
        "value":      18,
        "value_mode": "static"        # static | input | expression
    }

Returns:
    {
        "__condition__": True/False,
        "data": <merged upstream inputs>
    }

Downstream edges with a "condition" property will only pass data
through if the condition result matches the edge's expected value.
"""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.db_connectors.interpolation import resolve_field_mapping


_OPERATORS = {
    "==":     lambda a, b: a == b,
    "!=":     lambda a, b: a != b,
    ">":      lambda a, b: a > b,
    "<":      lambda a, b: a < b,
    ">=":     lambda a, b: a >= b,
    "<=":     lambda a, b: a <= b,
    "in":     lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}


def _coerce_value(val, reference):
    """Attempt to coerce the comparison value to the same type as the field."""
    if reference is None:
        return val
    try:
        return type(reference)(val)
    except (ValueError, TypeError):
        return val


def _evaluate(field_val, operator: str, compare_val) -> bool:
    """Evaluate a single condition expression."""
    op_fn = _OPERATORS.get(operator)
    if op_fn is None:
        raise ValueError(f"Unsupported operator: {operator}")

    coerced = _coerce_value(compare_val, field_val)

    try:
        return bool(op_fn(field_val, coerced))
    except TypeError:
        return False


@register_component("if_condition")
class IfConditionComponent(BaseComponent):
    """Evaluates a condition and wraps the result for conditional edge routing."""

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

        field_mapping = {
            "mode": config.get("field_mode", "expression"),
            "value": config.get("field", ""),
        }
        value_mapping = {
            "mode": config.get("value_mode", "static"),
            "value": config.get("value", ""),
        }

        field_val = resolve_field_mapping(field_mapping, merged)
        compare_val = resolve_field_mapping(value_mapping, merged)
        operator = config.get("operator", "==")

        result = _evaluate(field_val, operator, compare_val)

        return {"__condition__": result, "data": merged}
