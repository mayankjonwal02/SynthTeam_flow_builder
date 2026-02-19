"""
Loop ForEach Component — iterates over an array field in upstream data.

This is a 4-handle node:
  - "in" (left-top target):      receives initial data containing the array
  - "loop_back" (left-bottom target): receives output from the last body node
                                      (used internally by the executor per iteration)
  - "loop_out" (right-top source):    sends current element to body nodes
  - "done" (right-bottom source):     sends collected results after all iterations

Config:
    { "array_field": "items" }

The component itself merges inputs from the "in" handle and returns them.
The executor handles the actual per-element iteration logic using
the handle-aware edge_map and forward_adj.
"""

from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("loop_foreach")
class LoopForEachComponent(BaseComponent):
    """Entry point for a loop. The executor handles per-element iteration."""

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

        return {"data": merged}
