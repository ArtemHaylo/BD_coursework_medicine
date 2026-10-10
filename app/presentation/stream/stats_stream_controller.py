"""Статистика в реальному часі: SSE-потік (раз на секунду) і разовий знімок."""
from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.application.dto.monitoring import StatsDto
from app.application.ports.inbound.get_stats import GetStats


class StatsStreamController:
    def __init__(self, get_stats: GetStats, interval_seconds: float = 1.0) -> None:
        self._get_stats = get_stats
        self._interval = interval_seconds
        self.router = APIRouter(prefix="/api", tags=["stats"])
        self.router.add_api_route("/stats", self.snapshot, methods=["GET"], response_model=StatsDto)
        self.router.add_api_route("/stream/stats", self.stream, methods=["GET"])

    async def snapshot(self) -> StatsDto:
        raise NotImplementedError

    async def _events(self) -> AsyncIterator[str]:
        """Кожну секунду: 'data: <StatsDto як JSON>\\n\\n' (формат Server-Sent Events)."""
        raise NotImplementedError
        yield ""  # робить метод асинхронним генератором

    async def stream(self) -> StreamingResponse:
        """GET /api/stream/stats, media_type='text/event-stream'."""
        raise NotImplementedError
