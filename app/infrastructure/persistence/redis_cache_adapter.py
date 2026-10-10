"""Адаптер Redis для CacheStore (кеш search:<ключ> і конфігурація config:rate)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.ports.outbound.cache_store import CacheStore

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisCacheAdapter(CacheStore):
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        raise NotImplementedError

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError
