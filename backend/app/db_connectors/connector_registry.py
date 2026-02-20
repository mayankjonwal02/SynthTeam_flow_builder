"""
Connector registry -- maps db_type names to connector classes.

Usage:
    @register_connector("postgres")
    class PostgresConnector(BaseConnector): ...

    cls = get_connector_class("postgres")
    connector = cls()
    await connector.connect(creds)
"""

import logging
from typing import Dict, Type

from app.db_connectors.base import BaseConnector

logger = logging.getLogger("uvicorn.error")

CONNECTOR_REGISTRY: Dict[str, Type[BaseConnector]] = {}


def register_connector(name: str):
    """Decorator that registers a connector class by db_type name."""
    def decorator(cls):
        CONNECTOR_REGISTRY[name] = cls
        logger.info(f"Registered DB connector: {name}")
        return cls
    return decorator


def get_connector_class(db_type: str) -> Type[BaseConnector]:
    """Return the connector class for the given db_type."""
    cls = CONNECTOR_REGISTRY.get(db_type)
    if cls is None:
        raise ValueError(f"No connector registered for db_type '{db_type}'. Available: {list(CONNECTOR_REGISTRY.keys())}")
    return cls


def list_connectors() -> list:
    return list(CONNECTOR_REGISTRY.keys())
