from typing import AsyncGenerator
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
        await client.close()
