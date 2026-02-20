"""PostgreSQL Update -- update rows in a Postgres table."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("pg_update")
class PGUpdateComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "postgres"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        filters = self._resolve_filters(config, merged)
        data = self._clean_data(merged)
        result = await connector.update(config.get("table", ""), filters, data)
        return {"updated": result}
