"""Вхідний порт: знімок статистики для UI (запит №7)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.monitoring import StatsDto


class GetStats(ABC):
    @abstractmethod
    async def handle(self) -> StatsDto: ...
