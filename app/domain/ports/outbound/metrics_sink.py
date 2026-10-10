"""Вихідний порт: журнал запитів і метрики (адаптер: MongoDB, колекція search_log)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.search_log_entry import SearchLogEntry


class MetricsSink(ABC):
    @abstractmethod
    async def record_query(self, raw_query: str, normalized_query: str,
                           results_count: int, cache_hit: bool, latency_ms: int) -> None: ...

    @abstractmethod
    async def recent_queries(self, limit: int = 20) -> list[SearchLogEntry]:
        """Останні пошукові запити для панелі моніторингу."""

    @abstractmethod
    async def record_ingest(self, batch_size: int, duration_ms: int) -> None:
        """Фіксує записаний пакет (для графіка швидкості запису)."""

    @abstractmethod
    async def total_ingested(self) -> int:
        """Кількість успішно збережених документів."""
