"""Знімок статистики для UI: поточна швидкість (Redis) + лічильники та журнал (MongoDB)."""
from __future__ import annotations

from app.application.dto.monitoring import StatsDto
from app.application.ports.inbound.get_stats import GetStats
from app.domain.ports.outbound import CacheStore, MetricsSink


class GetStatsHandler(GetStats):
    def __init__(self, metrics: MetricsSink, cache: CacheStore) -> None:
        self._metrics = metrics
        self._cache = cache

    async def handle(self) -> StatsDto:
        raise NotImplementedError
