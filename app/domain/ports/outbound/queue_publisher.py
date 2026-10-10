"""Вихідний порт: публікація пакетів у чергу (адаптер: RabbitMQ)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.medicine import Medicine


class QueuePublisher(ABC):
    @abstractmethod
    async def publish_batch(self, medicines: list[Medicine]) -> None:
        """Публікує пакет препаратів у чергу."""
