"""MongoDB Aggregate -- run an aggregation pipeline."""
from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.components.db_base_mixin import DBNodeMixin

@register_component("mongo_aggregate")
class MongoAggregateComponent(DBNodeMixin, BaseComponent):
    DB_TYPE = "mongodb"
    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        merged = self._merge_inputs(inputs)
        connector = await self._get_connector(config)
        pipeline = config.get("pipeline", "[]")
        params = {"collection": config.get("collection", "default")}
        docs = await connector.raw_query(pipeline, params)
        return {"documents": docs, "count": len(docs)}
