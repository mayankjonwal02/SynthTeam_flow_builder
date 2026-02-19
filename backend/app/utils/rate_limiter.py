"""
Redis-backed sliding-window rate limiter.

Uses a sorted set per key. Each request adds a timestamp; expired
entries are pruned on every check. If the count exceeds the limit
within the window, an HTTPException(429) is raised.
"""

import time
from fastapi import HTTPException


async def check_rate_limit(
    redis_client,
    key: str,
    limit: int,
    window: int,
):
    """
    Enforce a sliding-window rate limit.

    Args:
        redis_client: An async Redis client (redis.asyncio).
        key:          Unique key (e.g. "ratelimit:{api_key}:{path}").
        limit:        Max requests allowed in the window.
        window:       Window size in seconds.

    Raises:
        HTTPException(429) when the limit is exceeded.
    """
    now = time.time()
    cutoff = now - window

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, cutoff)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window)
    results = await pipe.execute()

    current_count = results[2]
    if current_count > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} requests per {window}s",
        )
