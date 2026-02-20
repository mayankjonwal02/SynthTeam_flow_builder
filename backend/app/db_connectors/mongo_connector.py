"""MongoDB connector using motor (async driver)."""

from datetime import datetime, date
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any, Dict, List, Optional

from app.db_connectors.base import BaseConnector
from app.db_connectors.connector_registry import register_connector


def _serialize_value(val: Any) -> Any:
    """Recursively serialize MongoDB-specific types to JSON-compatible types."""
    if isinstance(val, ObjectId):
        return str(val)
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_serialize_value(item) for item in val]
    return val


@register_connector("mongodb")
class MongoConnector(BaseConnector):

    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._db = None

    async def connect(self, credentials: dict) -> None:
        if self._client is not None:
            return
        direct_uri = credentials.get("uri")
        explicit_database = credentials.get("database", "")

        if direct_uri:
            self._client = AsyncIOMotorClient(direct_uri)
            if explicit_database:
                db_name = explicit_database
            else:
                default_db = self._client.get_default_database()
                db_name = default_db.name if default_db is not None else "test"
            self._db = self._client[db_name]
        else:
            host = credentials.get("host", "localhost")
            port = int(credentials.get("port", 27017))
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            database = explicit_database or "test"

            if username and password:
                uri = f"mongodb://{username}:{password}@{host}:{port}"
            else:
                uri = f"mongodb://{host}:{port}"

            self._client = AsyncIOMotorClient(uri)
            self._db = self._client[database]

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None

    def _serialize(self, doc: dict) -> dict:
        """Serialize a MongoDB document to JSON-compatible dict."""
        return _serialize_value(doc)

    async def insert(self, table: str, data: dict) -> dict:
        result = await self._db[table].insert_one(data)
        data["_id"] = str(result.inserted_id)
        return data

    async def update(self, table: str, filters: dict, data: dict) -> dict:
        result = await self._db[table].update_many(filters, {"$set": data})
        return {"matched": result.matched_count, "modified": result.modified_count}

    async def delete(self, table: str, filters: dict) -> dict:
        result = await self._db[table].delete_many(filters)
        return {"deleted": result.deleted_count}

    async def find(self, table: str, filters: dict) -> List[dict]:
        cursor = self._db[table].find(filters or {})
        docs = await cursor.to_list(length=1000)
        return [self._serialize(d) for d in docs]

    async def raw_query(self, query: str, params: Optional[dict] = None) -> List[dict]:
        # For MongoDB, raw_query runs an aggregate pipeline (JSON string)
        import json
        pipeline = json.loads(query) if isinstance(query, str) else query
        collection = params.get("collection", "default") if params else "default"
        cursor = self._db[collection].aggregate(pipeline)
        docs = await cursor.to_list(length=1000)
        return [self._serialize(d) for d in docs]

    async def begin_transaction(self) -> Any:
        session = await self._client.start_session()
        session.start_transaction()
        return session

    async def commit(self, txn: Any = None) -> None:
        if txn:
            await txn.commit_transaction()
            await txn.end_session()

    async def rollback(self, txn: Any = None) -> None:
        if txn:
            await txn.abort_transaction()
            await txn.end_session()
