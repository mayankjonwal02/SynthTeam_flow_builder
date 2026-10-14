"""
Shared lookups for the management API that enforce ownership.

Each helper loads a resource by id and raises 404 if it doesn't exist *or*
belongs to another user, so callers can't probe for other users' ids.
"""

import uuid
from typing import Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.models import DatabaseConnection, File, Project


def parse_uuid(value: str, what: str = "Resource") -> uuid.UUID:
    """Parse an id from the URL; malformed ids are reported as not found."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail=f"{what} not found")


def require_fields(data: dict, *fields: str) -> None:
    """Raise 422 listing any missing or empty body fields."""
    missing = [f for f in fields if data.get(f) in (None, "")]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing field(s): {', '.join(missing)}")


async def get_owned_project(session: AsyncSession, project_id: str, user: dict) -> Project:
    pid = parse_uuid(project_id, "Project")
    res = await session.execute(
        select(Project).where(Project.id == pid, Project.user_id == user["sub"])
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def get_owned_file(
    session: AsyncSession, file_id: str, user: dict
) -> Tuple[File, Project]:
    fid = parse_uuid(file_id, "File")
    res = await session.execute(
        select(File, Project)
        .join(Project, File.project_id == Project.id)
        .where(File.id == fid, Project.user_id == user["sub"])
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return row[0], row[1]


async def get_owned_connection(
    session: AsyncSession, conn_id: str, user_id: Optional[str]
) -> DatabaseConnection:
    cid = parse_uuid(conn_id, "Connection")
    query = select(DatabaseConnection).where(DatabaseConnection.id == cid)
    if user_id is not None:
        query = query.where(DatabaseConnection.user_id == user_id)
    res = await session.execute(query)
    conn = res.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return conn
