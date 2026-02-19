"""
Parallel Split Component — pass-through that signals the executor to
run downstream children concurrently via asyncio.gather.

The component itself simply forwards upstream data. The special
parallel execution behavior is handled by the executor when it
detects the "parallel_split" component name.
"""

from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("parallel_split")
class ParallelSplitComponent(BaseComponent):
    """Passes input through; executor handles concurrent child execution."""

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
        return merged
