"""Вихідний порт: кеш і конфігурація (адаптер: Redis)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class CacheStore(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...
