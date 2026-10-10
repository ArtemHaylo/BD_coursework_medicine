"""Вхідний порт: аналоги препарату (запити №4, №5)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.analogue import AnalogueDto, AnalogueQuery


class GetAnalogues(ABC):
    @abstractmethod
    async def handle(self, query: AnalogueQuery) -> list[AnalogueDto]: ...
