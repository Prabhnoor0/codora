"""Redis async client."""
import redis.asyncio as aioredis
from typing import Optional
import structlog

from config import settings

log = structlog.get_logger()

_redis: Optional[aioredis.Redis] = None


async def init_redis():
    global _redis
    _redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    await _redis.ping()
    log.info("Redis connected ✓")


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized")
    return _redis


async def cache_get(key: str) -> Optional[str]:
    return await get_redis().get(key)


async def cache_set(key: str, value: str, ttl: int = 3600):
    await get_redis().setex(key, ttl, value)


async def cache_delete(key: str):
    await get_redis().delete(key)
