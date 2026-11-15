from typing import AsyncGenerator, Optional
from fastapi import Header, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db as _get_db
import redis.asyncio as aioredis
from app.core.config import settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.aclose()


async def verify_admin_key(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    admin_key: Optional[str] = Query(None),
) -> str:
    """Verifies that the caller possesses the valid admin secret key."""
    provided_key = x_admin_key or admin_key
    if not provided_key or provided_key.strip() != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or missing administrator secret key",
        )
    return provided_key
