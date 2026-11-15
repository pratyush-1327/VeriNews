from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
from app.api.deps import get_db, get_redis
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Health check for API, Database and Redis")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    db_status = "unhealthy"
    redis_status = "unhealthy"

    # Check Database
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check Redis
    try:
        pong = await redis.ping()
        if pong:
            redis_status = "healthy"
    except Exception as e:
        redis_status = f"error: {str(e)}"

    is_ok = db_status == "healthy" and redis_status == "healthy"
    return {
        "status": "ok" if is_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "redis": redis_status,
    }
