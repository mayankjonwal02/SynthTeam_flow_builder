"""
Shared mixin for all specialized DB node components.

Provides common helpers for merging inputs, getting connectors,
and interpolating template variables. Each subclass sets DB_TYPE
and calls these helpers.

Supports two connection modes:
  - UUID: fetches encrypted credentials from the database_connections table
  - Direct URI: uses the connection string directly (e.g. mongodb+srv://..., postgresql://...)
"""

import hashlib
from urllib.parse import urlparse
from typing import Any, Dict, List
from app.db_connectors.pool_manager import get_or_create_pool, ACTIVE_POOLS
from app.db_connectors.interpolation import interpolate, resolve_filter_mappings


def _is_uri(value: str) -> bool:
    """Check if a value looks like a connection URI rather than a UUID."""
    return "://" in value or value.startswith("/") or value == ":memory:"


def _uri_to_credentials(uri: str, db_type: str, database: str = "") -> dict:
    """Convert a raw connection URI into a credentials dict with a 'uri' key."""
    creds = {"uri": uri, "db_type": db_type}
    if database:
        creds["database"] = database
    return creds


def _pool_key_for_uri(uri: str) -> str:
    """Generate a stable cache key from a URI (avoids storing full URI as dict key)."""
    return f"uri_{hashlib.md5(uri.encode()).hexdigest()}"


def _reject_platform_database(uri: str) -> None:
    """Stop flows from connecting to SynthTeam's own application database."""
    from app.core.config import settings

    target = urlparse(uri)
    platform = urlparse(settings.DATABASE_URL.replace("+asyncpg", ""))
    if (
        target.hostname
        and platform.hostname
        and target.hostname == platform.hostname
        and (target.port or 5432) == (platform.port or 5432)
        and target.scheme.startswith(("postgres", "supabase"))
    ):
        raise ValueError("Connecting to the SynthTeam application database is not allowed")


class DBNodeMixin:
    DB_TYPE: str = ""

    def _merge_inputs(self, inputs: Dict[str, Any]) -> dict:
        merged: dict = {}
        for o in inputs.values():
            if isinstance(o, dict):
                merged.update(o)
        return merged

    async def _get_connector(self, config: dict):
        conn_value = config.get("connection_id", "")
        database = config.get("database", "")
        # Set by the executor from the deployed workflow's owner
        owner_id = config.get("__owner_id__")

        if _is_uri(conn_value):
            _reject_platform_database(conn_value)
            pool_key = _pool_key_for_uri(conn_value + database)
            creds = _uri_to_credentials(conn_value, self.DB_TYPE, database)
            return await get_or_create_pool(pool_key, self.DB_TYPE, creds)
        else:
            from app.api.db_connections import get_connection_credentials
            creds = await get_connection_credentials(conn_value, owner_id=owner_id)
            if database:
                creds["database"] = database
            return await get_or_create_pool(conn_value, self.DB_TYPE or creds["db_type"], creds)

    def _interpolate(self, template, context: dict):
        return interpolate(template, context)

    def _resolve_filters(self, config: dict, context: dict) -> dict:
        """
        Resolve filters from config using either new filter_mappings format
        or legacy filter/filters format.
        """
        filter_mappings = config.get("filter_mappings")
        if filter_mappings:
            return resolve_filter_mappings(filter_mappings, context)
        legacy_filter = config.get("filter") or config.get("filters") or {}
        return self._interpolate(legacy_filter, context)

    def _clean_data(self, merged: dict) -> dict:
        return {k: v for k, v in merged.items() if not k.startswith("__")}
