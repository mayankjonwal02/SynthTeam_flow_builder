"""SQLite Insert."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("sqlite_insert")
class SQLiteInsertComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "sqlite"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        result = await connector.insert(config.get("table", ""), self._clean_data(merged))
        return {"inserted": result}
