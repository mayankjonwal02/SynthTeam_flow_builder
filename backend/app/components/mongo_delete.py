"""MongoDB Delete -- delete documents matching a filter."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("mongo_delete")
class MongoDeleteComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "mongodb"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        filter_doc = self._resolve_filters(config, merged)
        result = await connector.delete(config.get("collection", ""), filter_doc)
        return {"deleted": result}
