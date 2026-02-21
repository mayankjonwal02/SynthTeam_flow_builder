"""Database query tools for agents — one per DB type."""

import json
from app.ai.tools.registry import register_tool
from app.ai.tools.base import SynthTool


class BaseDBQueryTool(SynthTool):
    """Base for DB query tools. Input: JSON with 'uri', 'query'."""
    db_type: str = ""

    def _run(self, input_str: str) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._arun(input_str))

    async def _arun(self, input_str: str) -> str:
        try:
            params = json.loads(input_str) if isinstance(input_str, str) else input_str
            uri = params.get("uri", "")
            query = params.get("query", "")
            from app.db_connectors.pool_manager import get_or_create_pool
            connector = await get_or_create_pool(
                f"tool_{hash(uri)}", self.db_type, {"uri": uri}
            )
            rows = await connector.raw_query(query)
            return json.dumps(rows[:50], default=str)
        except Exception as e:
            return f"DB query failed: {e}"


@register_tool("db_query_postgres")
class PostgresQueryTool(BaseDBQueryTool):
    name: str = "db_query_postgres"
    description: str = "Execute a SQL query on PostgreSQL. Input: JSON with 'uri' and 'query'."
    db_type: str = "postgres"


@register_tool("db_query_mysql")
class MySQLQueryTool(BaseDBQueryTool):
    name: str = "db_query_mysql"
    description: str = "Execute a SQL query on MySQL. Input: JSON with 'uri' and 'query'."
    db_type: str = "mysql"


@register_tool("db_query_sqlite")
class SQLiteQueryTool(BaseDBQueryTool):
    name: str = "db_query_sqlite"
    description: str = "Execute a SQL query on SQLite. Input: JSON with 'uri' (file path) and 'query'."
    db_type: str = "sqlite"


@register_tool("db_query_mongo")
class MongoQueryTool(SynthTool):
    name: str = "db_query_mongo"
    description: str = "Execute a MongoDB find query. Input: JSON with 'uri', 'database', 'collection', 'filter'."

    def _run(self, input_str: str) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._arun(input_str))

    async def _arun(self, input_str: str) -> str:
        try:
            params = json.loads(input_str) if isinstance(input_str, str) else input_str
            from app.db_connectors.pool_manager import get_or_create_pool
            connector = await get_or_create_pool(
                f"tool_{hash(params.get('uri', ''))}", "mongodb",
                {"uri": params.get("uri", ""), "database": params.get("database", "test")}
            )
            docs = await connector.find(params.get("collection", ""), params.get("filter", {}))
            return json.dumps(docs[:50], default=str)
        except Exception as e:
            return f"MongoDB query failed: {e}"
