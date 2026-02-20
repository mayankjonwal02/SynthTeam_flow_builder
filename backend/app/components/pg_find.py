"""PostgreSQL Find -- query rows from a Postgres table."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("pg_find")
class PGFindComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "postgres"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        filters = self._resolve_filters(config, merged)
        rows = await connector.find(config.get("table", ""), filters)
        return {"rows": rows, "count": len(rows)}
