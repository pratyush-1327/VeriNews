import time
import uuid
import logging
from typing import Callable
from fastapi import Request, HTTPException, status, Depends
import redis.asyncio as aioredis
from app.api.deps import get_redis
from app.core.config import settings

logger = logging.getLogger("verinews.ratelimit")


class RateLimiter:
    """
    Sliding-window rate limiter powered by Redis sorted sets (ZSET).
    Enforces maximum requests per time window per client IP.
    """

    def __init__(self, max_requests: int = 30, window_seconds: int = 60, action: str = "general"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.action = action

    async def __call__(
        self,
        request: Request,
        redis: aioredis.Redis = Depends(get_redis),
    ):
        # Extract client IP (respecting X-Forwarded-For if behind a proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        key = f"ratelimit:{client_ip}:{self.action}"
        now = time.time()
        window_start = now - self.window_seconds

        try:
            pipeline = redis.pipeline()
            # 1. Purge requests older than window_start
            pipeline.zremrangebyscore(key, 0, window_start)
            # 2. Add current request with timestamp score
            member_id = f"{now}:{uuid.uuid4().hex[:8]}"
            pipeline.zadd(key, {member_id: now})
            # 3. Count remaining elements in current window
            pipeline.zcard(key)
            # 4. Set expiry slightly larger than window
            pipeline.expire(key, self.window_seconds + 10)

            results = await pipeline.execute()
            current_count = results[2]

            if current_count > self.max_requests:
                logger.warning(
                    f"Rate limit exceeded for IP {client_ip} on action '{self.action}': "
                    f"{current_count}/{self.max_requests} requests"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: maximum {self.max_requests} requests per {self.window_seconds} seconds. Please slow down.",
                    headers={"Retry-After": str(self.window_seconds)},
                )
        except HTTPException:
            raise
        except Exception as e:
            # If Redis is temporarily degraded, fail open so legitimate traffic is not blocked
            logger.error(f"Redis rate limiter error: {e}")
            return


# Standard rate limiters
verify_rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
    action="verify",
)

feed_rate_limiter = RateLimiter(
    max_requests=120,
    window_seconds=60,
    action="feed",
)
