"""Supabase Raw Query."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("supa_raw_query")
class SupaRawQueryComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "supabase"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        query = self._interpolate(config.get("query", ""), merged)
        rows = await connector.raw_query(query, merged)
        return {"rows": rows, "count": len(rows)}
