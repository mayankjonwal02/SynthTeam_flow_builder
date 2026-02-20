"""MySQL connector using aiomysql."""

import aiomysql
from typing import Any, Dict, List, Optional

from app.db_connectors.base import BaseConnector
from app.db_connectors.connector_registry import register_connector


@register_connector("mysql")
class MySQLConnector(BaseConnector):

    def __init__(self):
        self._pool: Optional[aiomysql.Pool] = None
        self._txn_conn: Optional[aiomysql.Connection] = None

    async def connect(self, credentials: dict) -> None:
        if self._pool:
            return
        uri = credentials.get("uri")
        if uri:
            from urllib.parse import urlparse
            p = urlparse(uri)
            self._pool = await aiomysql.create_pool(
                host=p.hostname or "localhost",
                port=p.port or 3306,
                user=p.username or "",
                password=p.password or "",
                db=p.path.lstrip("/") if p.path else "",
                minsize=1, maxsize=10, autocommit=True,
            )
        else:
            self._pool = await aiomysql.create_pool(
                host=credentials.get("host", "localhost"),
                port=int(credentials.get("port", 3306)),
                user=credentials.get("username", ""),
                password=credentials.get("password", ""),
                db=credentials.get("database", ""),
                minsize=1, maxsize=10, autocommit=True,
            )

    async def disconnect(self) -> None:
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def _execute(self, query: str, args=None, fetch=True, conn=None):
        c = conn or self._txn_conn
        if c:
            async with c.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, args)
                return await cur.fetchall() if fetch else cur.rowcount
        async with self._pool.acquire() as c:
            async with c.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, args)
                return await cur.fetchall() if fetch else cur.rowcount

    async def insert(self, table: str, data: dict) -> dict:
        cols = ", ".join(data.keys())
        phs = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({cols}) VALUES ({phs})"
        await self._execute(query, tuple(data.values()), fetch=False)
        rows = await self._execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 1")
        return rows[0] if rows else {}

    async def update(self, table: str, filters: dict, data: dict) -> dict:
        set_parts = [f"{k} = %s" for k in data.keys()]
        where_parts = [f"{k} = %s" for k in filters.keys()]
        args = tuple(data.values()) + tuple(filters.values())
        query = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        affected = await self._execute(query, args, fetch=False)
        return {"rows_affected": affected}

    async def delete(self, table: str, filters: dict) -> dict:
        where_parts = [f"{k} = %s" for k in filters.keys()]
        query = f"DELETE FROM {table} WHERE {' AND '.join(where_parts)}"
        affected = await self._execute(query, tuple(filters.values()), fetch=False)
        return {"deleted": affected}

    async def find(self, table: str, filters: dict) -> List[dict]:
        if filters:
            where_parts = [f"{k} = %s" for k in filters.keys()]
            query = f"SELECT * FROM {table} WHERE {' AND '.join(where_parts)}"
            return await self._execute(query, tuple(filters.values()))
        return await self._execute(f"SELECT * FROM {table}")

    async def raw_query(self, query: str, params: Optional[dict] = None) -> List[dict]:
        if params:
            for key, val in params.items():
                query = query.replace(f":{key}", "%s")
            return await self._execute(query, tuple(params.values()))
        return await self._execute(query)

    async def begin_transaction(self) -> Any:
        self._txn_conn = await self._pool.acquire()
        await self._txn_conn.begin()
        return self._txn_conn

    async def commit(self, txn: Any = None) -> None:
        if self._txn_conn:
            await self._txn_conn.commit()
            self._txn_conn.close()
            self._txn_conn = None

    async def rollback(self, txn: Any = None) -> None:
        if self._txn_conn:
            await self._txn_conn.rollback()
            self._txn_conn.close()
            self._txn_conn = None
