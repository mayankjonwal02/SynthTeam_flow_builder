"""
Auth Node Component — validates API keys from request headers.

Config:
    {
        "type": "api_key",
        "header_name": "x-api-key"
    }

Reads the API key from request_data["__headers__"], validates it
against the ApiKey table in the database. Raises HTTPException(401)
if the key is invalid. On success, passes merged upstream data through.
"""

from typing import Any, Dict

from fastapi import HTTPException

from app.components.base import BaseComponent
from app.components.component_registry import register_component
from app.db.session import AsyncSessionLocal


@register_component("auth_node")
class AuthNodeComponent(BaseComponent):
    """Validates an API key and gates downstream execution."""

    async def execute(
        self,
        request_data: dict,
        inputs: Dict[str, Any],
        config: dict,
    ) -> dict:
        merged: dict = {}
        for output in inputs.values():
            if isinstance(output, dict):
                merged.update(output)

        auth_type   = config.get("type", "api_key")
        header_name = config.get("header_name", "x-api-key")

        headers = request_data.get("__headers__", {})
        provided_key = headers.get(header_name.lower()) or headers.get(header_name)

        if not provided_key:
            raise HTTPException(
                status_code=401,
                detail=f"Missing required header: {header_name}",
            )

        if auth_type == "api_key":
            is_valid = await self._validate_api_key(provided_key)
            if not is_valid:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key",
                )

        merged["__auth__"] = {"type": auth_type, "authenticated": True}
        return merged

    @staticmethod
    async def _validate_api_key(key: str) -> bool:
        """Check the API key against the database."""
        try:
            from sqlalchemy.future import select
            from app.models.models import ApiKey

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ApiKey).where(
                        ApiKey.key == key,
                        ApiKey.is_active == True,  # noqa: E712
                    )
                )
                return result.scalar() is not None
        except Exception:
            return False
