"""Вихідний порт: публікація пакетів у чергу (адаптер: RabbitMQ).

Черга передає «сирі» JSON-документи (dict), а не сутності: документ містить і поля
для MongoDB/Neo4j, і full_description для Elasticsearch, якого немає в Medicine.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class QueuePublisher(ABC):
    @abstractmethod
    async def publish_batch(self, documents: list[dict[str, Any]]) -> None:
        """Публікує пакет документів одним повідомленням."""
