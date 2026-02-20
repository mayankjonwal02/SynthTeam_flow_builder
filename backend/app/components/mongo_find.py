"""MongoDB Find -- query documents from a collection."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("mongo_find")
class MongoFindComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "mongodb"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        filter_doc = self._resolve_filters(config, merged)
        docs = await connector.find(config.get("collection", ""), filter_doc)
        return {"documents": docs, "count": len(docs)}
