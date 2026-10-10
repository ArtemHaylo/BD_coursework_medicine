"""Зміна цільової швидкості: запис ключа config:rate в Redis."""
from __future__ import annotations

from app.application.dto.monitoring import RateConfigDto
from app.application.constants import RATE_KEY  # noqa: F401
from app.application.ports.inbound.configure_rate import ConfigureRate
from app.domain.ports.outbound import CacheStore


class ConfigureRateHandler(ConfigureRate):
    def __init__(self, cache: CacheStore) -> None:
        self._cache = cache

    async def handle(self, config: RateConfigDto) -> RateConfigDto:
        raise NotImplementedError
