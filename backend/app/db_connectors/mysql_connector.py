"""MySQL connector using aiomysql."""

import aiomysql
from typing import Any, Dict, List, Optional

from app.db_connectors.base import BaseConnector
from app.db_connectors.connector_registry import register_connector
from app.db_connectors.sql_safety import safe_ident


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
            return await self._run(c, query, args, fetch)
        async with self._pool.acquire() as c:
            return await self._run(c, query, args, fetch)

    @staticmethod
    async def _run(conn, query: str, args, fetch):
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, args)
            if fetch == "lastrowid":
                return cur.lastrowid
            return await cur.fetchall() if fetch else cur.rowcount

    async def insert(self, table: str, data: dict) -> dict:
        table = safe_ident(table)
        cols = ", ".join(safe_ident(k) for k in data.keys())
        phs = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({cols}) VALUES ({phs})"
        last_id = await self._execute(query, tuple(data.values()), fetch="lastrowid")
        if last_id:
            try:
                rows = await self._execute(f"SELECT * FROM {table} WHERE id = %s", (last_id,))
                if rows:
                    return rows[0]
            except Exception:
                pass  # auto-increment column isn't called "id"
        return {**data, "id": last_id} if last_id else dict(data)

    async def update(self, table: str, filters: dict, data: dict) -> dict:
        if not filters:
            raise ValueError("Refusing to UPDATE without filters")
        set_parts = [f"{safe_ident(k)} = %s" for k in data.keys()]
        where_parts = [f"{safe_ident(k)} = %s" for k in filters.keys()]
        args = tuple(data.values()) + tuple(filters.values())
        query = f"UPDATE {safe_ident(table)} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        affected = await self._execute(query, args, fetch=False)
        return {"rows_affected": affected}

    async def delete(self, table: str, filters: dict) -> dict:
        if not filters:
            raise ValueError("Refusing to DELETE without filters")
        where_parts = [f"{safe_ident(k)} = %s" for k in filters.keys()]
        query = f"DELETE FROM {safe_ident(table)} WHERE {' AND '.join(where_parts)}"
        affected = await self._execute(query, tuple(filters.values()), fetch=False)
        return {"deleted": affected}

    async def find(self, table: str, filters: dict) -> List[dict]:
        if filters:
            where_parts = [f"{safe_ident(k)} = %s" for k in filters.keys()]
            query = f"SELECT * FROM {safe_ident(table)} WHERE {' AND '.join(where_parts)}"
            return await self._execute(query, tuple(filters.values()))
        return await self._execute(f"SELECT * FROM {safe_ident(table)}")

    async def raw_query(self, query: str, params: Optional[list] = None) -> List[dict]:
        """Run SQL that already uses %s placeholders (see sql_safety.build_bound_query)."""
        return await self._execute(query, tuple(params) if params else None)

    async def begin_transaction(self) -> Any:
        self._txn_conn = await self._pool.acquire()
        await self._txn_conn.begin()
        return self._txn_conn

    async def commit(self, txn: Any = None) -> None:
        if self._txn_conn:
            try:
                await self._txn_conn.commit()
            finally:
                self._pool.release(self._txn_conn)
                self._txn_conn = None

    async def rollback(self, txn: Any = None) -> None:
        if self._txn_conn:
            try:
                await self._txn_conn.rollback()
            finally:
                self._pool.release(self._txn_conn)
                self._txn_conn = None
