"""
Abstract base class for all database connectors.

Every connector must implement the full CRUD interface plus
transaction support and raw query execution.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseConnector(ABC):

    @abstractmethod
    async def connect(self, credentials: dict) -> None:
        """Establish a connection / pool using the provided credentials."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection / pool gracefully."""
        ...

    @abstractmethod
    async def insert(self, table: str, data: dict) -> dict:
        """Insert a row and return the inserted record."""
        ...

    @abstractmethod
    async def update(self, table: str, filters: dict, data: dict) -> dict:
        """Update rows matching filters and return result summary."""
        ...

    @abstractmethod
    async def delete(self, table: str, filters: dict) -> dict:
        """Delete rows matching filters and return result summary."""
        ...

    @abstractmethod
    async def find(self, table: str, filters: dict) -> List[dict]:
        """Query rows matching filters."""
        ...

    @abstractmethod
    async def raw_query(self, query: str, params: Optional[Any] = None) -> List[dict]:
        """
        Execute a raw query. SQL connectors take a list of positional
        parameters matching the placeholders already in `query`
        (see sql_safety.build_bound_query); MongoDB takes a pipeline.
        """
        ...

    @abstractmethod
    async def begin_transaction(self) -> Any:
        """Start a transaction and return a transaction handle."""
        ...

    @abstractmethod
    async def commit(self, txn: Any = None) -> None:
        """Commit the active or given transaction."""
        ...

    @abstractmethod
    async def rollback(self, txn: Any = None) -> None:
        """Roll back the active or given transaction."""
        ...
