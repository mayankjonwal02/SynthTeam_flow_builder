"""SQLite connector using aiosqlite (for local dev / testing)."""

import aiosqlite
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.db_connectors.base import BaseConnector
from app.db_connectors.connector_registry import register_connector
from app.db_connectors.sql_safety import safe_ident


def resolve_sqlite_path(path: str) -> str:
    """
    Confine SQLite files to settings.SQLITE_BASE_DIR.

    Relative paths are resolved inside the base directory; absolute paths
    must already point inside it. Anything else raises ValueError so a flow
    can't open arbitrary files on the server.
    """
    if not path or path == ":memory:":
        return ":memory:"
    from app.core.config import settings

    base = Path(settings.SQLITE_BASE_DIR).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = base / target
    target = target.resolve()
    if target != base and base not in target.parents:
        raise ValueError(
            f"SQLite database must be inside SQLITE_BASE_DIR ({base}); got {path!r}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target)


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
        self._conn = await aiosqlite.connect(resolve_sqlite_path(path))
        self._conn.row_factory = aiosqlite.Row

    async def disconnect(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def insert(self, table: str, data: dict) -> dict:
        cols = ", ".join(safe_ident(k) for k in data.keys())
        phs = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {safe_ident(table)} ({cols}) VALUES ({phs})"
        cursor = await self._conn.execute(query, tuple(data.values()))
        await self._conn.commit()
        return {**data, "rowid": cursor.lastrowid}

    async def update(self, table: str, filters: dict, data: dict) -> dict:
        if not filters:
            raise ValueError("Refusing to UPDATE without filters")
        set_parts = [f"{safe_ident(k)} = ?" for k in data.keys()]
        where_parts = [f"{safe_ident(k)} = ?" for k in filters.keys()]
        args = tuple(data.values()) + tuple(filters.values())
        query = f"UPDATE {safe_ident(table)} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        cursor = await self._conn.execute(query, args)
        await self._conn.commit()
        return {"rows_affected": cursor.rowcount}

    async def delete(self, table: str, filters: dict) -> dict:
        if not filters:
            raise ValueError("Refusing to DELETE without filters")
        where_parts = [f"{safe_ident(k)} = ?" for k in filters.keys()]
        query = f"DELETE FROM {safe_ident(table)} WHERE {' AND '.join(where_parts)}"
        cursor = await self._conn.execute(query, tuple(filters.values()))
        await self._conn.commit()
        return {"deleted": cursor.rowcount}

    async def find(self, table: str, filters: dict) -> List[dict]:
        if filters:
            where_parts = [f"{safe_ident(k)} = ?" for k in filters.keys()]
            query = f"SELECT * FROM {safe_ident(table)} WHERE {' AND '.join(where_parts)}"
            cursor = await self._conn.execute(query, tuple(filters.values()))
        else:
            cursor = await self._conn.execute(f"SELECT * FROM {safe_ident(table)}")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def raw_query(self, query: str, params: Optional[list] = None) -> List[dict]:
        """Run SQL that already uses ? placeholders (see sql_safety.build_bound_query)."""
        cursor = await self._conn.execute(query, list(params or []))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def begin_transaction(self) -> Any:
        await self._conn.execute("BEGIN")
        return self._conn

    async def commit(self, txn: Any = None) -> None:
        await self._conn.commit()

    async def rollback(self, txn: Any = None) -> None:
        await self._conn.rollback()
