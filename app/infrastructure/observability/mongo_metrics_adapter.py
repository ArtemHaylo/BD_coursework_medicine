"""Адаптер MongoDB для MetricsSink (колекції search_log та ingest_log, без шардінгу)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.entities.search_log_entry import SearchLogEntry
from app.domain.ports.outbound.metrics_sink import MetricsSink

if TYPE_CHECKING:
    from pymongo import AsyncMongoClient


class MongoMetricsAdapter(MetricsSink):
    def __init__(self, client: AsyncMongoClient, database: str = "medicine") -> None:
        self._search_log = client[database]["search_log"]
        self._ingest_log = client[database]["ingest_log"]

    async def record_query(self, raw_query: str, normalized_query: str,
                           results_count: int, cache_hit: bool, latency_ms: int) -> None:
        raise NotImplementedError

    async def recent_queries(self, limit: int = 20) -> list[SearchLogEntry]:
        raise NotImplementedError

    async def record_ingest(self, batch_size: int, duration_ms: int) -> None:
        raise NotImplementedError

    async def total_ingested(self) -> int:
        raise NotImplementedError
