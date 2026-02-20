"""SQLite connector using aiosqlite (for local dev / testing)."""

import aiosqlite
from typing import Any, Dict, List, Optional

from app.db_connectors.base import BaseConnector
from app.db_connectors.connector_registry import register_connector


@register_connector("sqlite")
class SQLiteConnector(BaseConnector):

    def __init__(self):
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self, credentials: dict) -> None:
        if self._conn:
            return
        uri = credentials.get("uri")
        if uri:
            path = uri.replace("sqlite:///", "").replace("sqlite://", "") or ":memory:"
        else:
            path = credentials.get("database", ":memory:")
        self._conn = await aiosqlite.connect(path)
        self._conn.row_factory = aiosqlite.Row

    async def disconnect(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def insert(self, table: str, data: dict) -> dict:
        cols = ", ".join(data.keys())
        phs = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} ({cols}) VALUES ({phs})"
        cursor = await self._conn.execute(query, tuple(data.values()))
        await self._conn.commit()
        data["rowid"] = cursor.lastrowid
        return data

    async def update(self, table: str, filters: dict, data: dict) -> dict:
        set_parts = [f"{k} = ?" for k in data.keys()]
        where_parts = [f"{k} = ?" for k in filters.keys()]
        args = tuple(data.values()) + tuple(filters.values())
        query = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        cursor = await self._conn.execute(query, args)
        await self._conn.commit()
        return {"rows_affected": cursor.rowcount}

    async def delete(self, table: str, filters: dict) -> dict:
        where_parts = [f"{k} = ?" for k in filters.keys()]
        query = f"DELETE FROM {table} WHERE {' AND '.join(where_parts)}"
        cursor = await self._conn.execute(query, tuple(filters.values()))
        await self._conn.commit()
        return {"deleted": cursor.rowcount}

    async def find(self, table: str, filters: dict) -> List[dict]:
        if filters:
            where_parts = [f"{k} = ?" for k in filters.keys()]
            query = f"SELECT * FROM {table} WHERE {' AND '.join(where_parts)}"
            cursor = await self._conn.execute(query, tuple(filters.values()))
        else:
            cursor = await self._conn.execute(f"SELECT * FROM {table}")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def raw_query(self, query: str, params: Optional[dict] = None) -> List[dict]:
        if params:
            ordered = list(params.values())
            for key in params.keys():
                query = query.replace(f":{key}", "?")
            cursor = await self._conn.execute(query, ordered)
        else:
            cursor = await self._conn.execute(query)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def begin_transaction(self) -> Any:
        await self._conn.execute("BEGIN")
        return self._conn

    async def commit(self, txn: Any = None) -> None:
        await self._conn.commit()

    async def rollback(self, txn: Any = None) -> None:
        await self._conn.rollback()
