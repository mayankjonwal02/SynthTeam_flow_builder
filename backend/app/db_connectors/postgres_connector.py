"""PostgreSQL connector using asyncpg."""

import asyncpg
from typing import Any, Dict, List, Optional

from app.db_connectors.base import BaseConnector
from app.db_connectors.connector_registry import register_connector


@register_connector("postgres")
class PostgresConnector(BaseConnector):

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._txn_conn: Optional[asyncpg.Connection] = None
        self._txn: Optional[asyncpg.connection.transaction.Transaction] = None

    async def connect(self, credentials: dict) -> None:
        if self._pool:
            return
        uri = credentials.get("uri")
        if uri:
            self._pool = await asyncpg.create_pool(uri, min_size=1, max_size=10)
        else:
            self._pool = await asyncpg.create_pool(
                host=credentials.get("host", "localhost"),
                port=int(credentials.get("port", 5432)),
                user=credentials.get("username", ""),
                password=credentials.get("password", ""),
                database=credentials.get("database", ""),
                min_size=1,
                max_size=10,
            )

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def insert(self, table: str, data: dict) -> dict:
        cols = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
        returning = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING *"
        conn = self._txn_conn or self._pool
        row = await conn.fetchrow(returning, *data.values())
        return dict(row) if row else {}

    async def update(self, table: str, filters: dict, data: dict) -> dict:
        set_parts = [f"{k} = ${i+1}" for i, k in enumerate(data.keys())]
        vals = list(data.values())
        where_parts = [f"{k} = ${len(vals)+i+1}" for i, k in enumerate(filters.keys())]
        vals.extend(filters.values())
        query = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)} RETURNING *"
        conn = self._txn_conn or self._pool
        row = await conn.fetchrow(query, *vals)
        return dict(row) if row else {"rows_affected": 0}

    async def delete(self, table: str, filters: dict) -> dict:
        where_parts = [f"{k} = ${i+1}" for i, k in enumerate(filters.keys())]
        query = f"DELETE FROM {table} WHERE {' AND '.join(where_parts)} RETURNING *"
        conn = self._txn_conn or self._pool
        rows = await conn.fetch(query, *filters.values())
        return {"deleted": len(rows), "rows": [dict(r) for r in rows]}

    async def find(self, table: str, filters: dict) -> List[dict]:
        if filters:
            where_parts = [f"{k} = ${i+1}" for i, k in enumerate(filters.keys())]
            query = f"SELECT * FROM {table} WHERE {' AND '.join(where_parts)}"
            rows = await self._pool.fetch(query, *filters.values())
        else:
            rows = await self._pool.fetch(f"SELECT * FROM {table}")
        return [dict(r) for r in rows]

    async def raw_query(self, query: str, params: Optional[dict] = None) -> List[dict]:
        if params:
            ordered = list(params.values())
            for i, key in enumerate(params.keys()):
                query = query.replace(f":{key}", f"${i+1}")
            rows = await self._pool.fetch(query, *ordered)
        else:
            rows = await self._pool.fetch(query)
        return [dict(r) for r in rows]

    async def begin_transaction(self) -> Any:
        self._txn_conn = await self._pool.acquire()
        self._txn = self._txn_conn.transaction()
        await self._txn.start()
        return self._txn

    async def commit(self, txn: Any = None) -> None:
        if self._txn:
            await self._txn.commit()
        if self._txn_conn:
            await self._pool.release(self._txn_conn)
        self._txn = None
        self._txn_conn = None

    async def rollback(self, txn: Any = None) -> None:
        if self._txn:
            await self._txn.rollback()
        if self._txn_conn:
            await self._pool.release(self._txn_conn)
        self._txn = None
        self._txn_conn = None
