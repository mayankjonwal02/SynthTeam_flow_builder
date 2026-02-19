"""
Merge/Join Component — waits for all parent nodes and merges their outputs.

No special executor logic needed: topological ordering guarantees all
parents complete before this node runs. The component simply merges
every parent output into a single flat dict.
"""

from typing import Any, Dict

from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("merge_join")
class MergeJoinComponent(BaseComponent):
    """Merges all parent outputs into one dict."""

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
            else:
                pass
        return merged
