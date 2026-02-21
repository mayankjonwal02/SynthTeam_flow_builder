"""DB Query tool node — executes database queries, connects via ai_tool handle."""

from typing import Any, Dict
from app.components.base import BaseComponent
from app.components.component_registry import register_component


@register_component("tool_db_query")
class ToolDBQueryComponent(BaseComponent):

    async def execute(self, request_data: dict, inputs: Dict[str, Any], config: dict) -> dict:
        db_type = config.get("db_type", "postgres")
        tool_map = {
            "postgres": "postgres_query",
            "mysql": "mysql_query",
            "sqlite": "sqlite_query",
            "mongo": "mongo_query",
        }
        return {
            "__handle_type__": "ai_tool",
            "tool_name": tool_map.get(db_type, "postgres_query"),
            "connection_id": config.get("connection_id", ""),
            "uri": config.get("uri", ""),
        }
