"""MongoDB Update -- update documents matching a filter."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("mongo_update")
class MongoUpdateComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "mongodb"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        filter_doc = self._resolve_filters(config, merged)
        update_data = self._clean_data(merged)
        result = await connector.update(config.get("collection", ""), filter_doc, update_data)
        return {"updated": result}
