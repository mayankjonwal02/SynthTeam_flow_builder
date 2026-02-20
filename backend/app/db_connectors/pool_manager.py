"""
Connection pool manager -- caches active connector instances so pools
are reused across workflow executions rather than reconnecting per node.
"""

import logging
from typing import Dict

from app.db_connectors.base import BaseConnector
from app.db_connectors.connector_registry import get_connector_class

logger = logging.getLogger("uvicorn.error")

ACTIVE_POOLS: Dict[str, BaseConnector] = {}


async def get_or_create_pool(
    connection_id: str,
    db_type: str,
    credentials: dict,
) -> BaseConnector:
    """
    Return an existing pooled connector or create and cache a new one.

    Args:
        connection_id: UUID string identifying the stored connection.
        db_type:       One of the registered connector types.
        credentials:   Decrypted connection credentials dict.
    """
    if connection_id in ACTIVE_POOLS:
        return ACTIVE_POOLS[connection_id]

    cls = get_connector_class(db_type)
    connector = cls()
    await connector.connect(credentials)

    ACTIVE_POOLS[connection_id] = connector
    logger.info(f"Created DB pool for connection {connection_id} ({db_type})")
    return connector


async def remove_pool(connection_id: str) -> None:
    """Disconnect and remove a cached pool."""
    connector = ACTIVE_POOLS.pop(connection_id, None)
    if connector:
        try:
            await connector.disconnect()
        except Exception as exc:
            logger.warning(f"Error disconnecting pool {connection_id}: {exc}")


async def shutdown_all_pools() -> None:
    """Disconnect all active pools (called on app shutdown)."""
    for cid in list(ACTIVE_POOLS.keys()):
        await remove_pool(cid)
