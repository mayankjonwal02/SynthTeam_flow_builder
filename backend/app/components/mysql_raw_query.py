"""MySQL Raw Query."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin
from app.db_connectors.sql_safety import build_bound_query

@register_component("mysql_raw_query")
class MySQLRawQueryComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "mysql"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        # Values are bound as parameters, never pasted into the SQL text
        query, params = build_bound_query(config.get("query", ""), merged, "mysql")
        rows = await connector.raw_query(query, params)
        return {"rows": rows, "count": len(rows)}
