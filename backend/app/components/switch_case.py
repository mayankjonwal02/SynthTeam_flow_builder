"""
Switch/Case Component — routes data to different branches based on a field value.

Config:
    {
        "field": "status",
        "cases": ["approved", "rejected", "pending"]
    }

Returns:
    {
        "__case__": "approved",   (or None if no match)
        "data": <merged upstream inputs>
    }

Downstream edges carry "condition": "approved" etc.  The executor
only forwards data through edges whose condition matches __case__.
"""

from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("switch_case")
class SwitchCaseComponent(BaseComponent):
    """Evaluates a field and emits a __case__ value for edge routing."""

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

        field = config.get("field", "")
        cases = config.get("cases", [])
        value = merged.get(field)

        matched = str(value) if value is not None and str(value) in cases else None

        return {"__case__": matched, "data": merged}
