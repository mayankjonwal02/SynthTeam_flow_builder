"""
API routes for managing database connections.

Endpoints:
  POST   /api/db-connections        -- create a connection (encrypts credentials)
  GET    /api/db-connections        -- list user's connections (no credentials returned)
  GET    /api/db-connections/{id}   -- get single connection metadata
  DELETE /api/db-connections/{id}   -- delete a connection
  POST   /api/db-connections/{id}/test -- test a connection
"""

import uuid as _uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select

from app.db.session import AsyncSessionLocal
from app.models.models import DatabaseConnection
from app.core.auth import verify_token
from app.utils.encryption import encrypt_json, decrypt_json, encryption_key_is_valid
from app.db_connectors.connector_registry import get_connector_class, list_connectors
from app.api.deps import get_owned_connection, require_fields
from app.db_connectors.pool_manager import remove_pool

router = APIRouter(prefix="/api/db-connections", tags=["db-connections"])


@router.post("")
async def create_connection(data: dict, user=Depends(verify_token)):
    """Create a new database connection with encrypted credentials."""
    require_fields(data, "name", "db_type", "credentials")
    if data["db_type"] not in list_connectors():
        raise HTTPException(status_code=422, detail=f"Unsupported db_type: {data['db_type']}")
    if not encryption_key_is_valid():
        raise HTTPException(status_code=500, detail="Server ENCRYPTION_KEY is not configured")

    encrypted = encrypt_json(data["credentials"])

    async with AsyncSessionLocal() as session:
        conn = DatabaseConnection(
            id=_uuid.uuid4(),
            user_id=user["sub"],
            name=data["name"],
            db_type=data["db_type"],
            encrypted_credentials=encrypted,
        )
        session.add(conn)
        await session.commit()
        return {
            "id": str(conn.id),
            "name": conn.name,
            "db_type": conn.db_type,
        }


@router.get("")
async def list_connections(user=Depends(verify_token)):
    """List all connections for the authenticated user (no credentials)."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(DatabaseConnection).where(
                DatabaseConnection.user_id == user["sub"]
            )
        )
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "db_type": c.db_type,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in res.scalars().all()
        ]


@router.get("/{conn_id}")
async def get_connection(conn_id: str, user=Depends(verify_token)):
    """Get metadata for a single connection."""
    async with AsyncSessionLocal() as session:
        c = await get_owned_connection(session, conn_id, user["sub"])
        return {
            "id": str(c.id),
            "name": c.name,
            "db_type": c.db_type,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }


@router.delete("/{conn_id}")
async def delete_connection(conn_id: str, user=Depends(verify_token)):
    """Delete a connection and its cached pool."""
    async with AsyncSessionLocal() as session:
        c = await get_owned_connection(session, conn_id, user["sub"])
        await session.delete(c)
        await session.commit()

    await remove_pool(str(c.id))
    return {"success": True}


@router.post("/{conn_id}/test")
async def test_connection(conn_id: str, user=Depends(verify_token)):
    """Decrypt credentials and attempt a connection to validate."""
    async with AsyncSessionLocal() as session:
        c = await get_owned_connection(session, conn_id, user["sub"])

    try:
        creds = decrypt_json(c.encrypted_credentials)
        cls = get_connector_class(c.db_type)
        connector = cls()
        await connector.connect(creds)
        await connector.disconnect()
        return {"success": True, "message": f"Successfully connected to {c.db_type}"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Connection failed: {exc}")


async def get_connection_credentials(conn_id: str, owner_id: Optional[str] = None) -> dict:
    """
    Helper used by DB node components to fetch and decrypt credentials.

    When owner_id is given (always, for deployed workflows) the connection
    must belong to that user.
    """
    async with AsyncSessionLocal() as session:
        try:
            c = await get_owned_connection(session, conn_id, owner_id)
        except HTTPException:
            raise ValueError(f"DB connection '{conn_id}' not found")
        creds = decrypt_json(c.encrypted_credentials)
        creds["db_type"] = c.db_type
        return creds
