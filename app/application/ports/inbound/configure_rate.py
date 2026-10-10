"""Вхідний порт: зміна цільової швидкості генератора."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.monitoring import RateConfigDto


class ConfigureRate(ABC):
    @abstractmethod
    async def handle(self, config: RateConfigDto) -> RateConfigDto: ...
