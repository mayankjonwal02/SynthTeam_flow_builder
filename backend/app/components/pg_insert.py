"""PostgreSQL Insert -- insert data into a Postgres table."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("pg_insert")
class PGInsertComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "postgres"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        data = self._clean_data(merged)
        result = await connector.insert(config.get("table", ""), data)
        return {"inserted": result}
