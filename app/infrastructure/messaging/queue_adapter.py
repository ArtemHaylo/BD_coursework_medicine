"""Адаптер RabbitMQ (aio-pika): публікація пакетів і споживання з ack після успішного запису."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.domain.ports.outbound.queue_publisher import QueuePublisher

BatchCallback = Callable[[list[dict[str, Any]]], Awaitable[None]]


class QueueAdapter(QueuePublisher):
    def __init__(self, url: str, queue: str = "medicine.ingest",
                 prefetch: int = 10, max_length: int = 1000) -> None:
        self._url = url
        self._queue = queue
        self._prefetch = prefetch
        self._max_length = max_length

    async def connect(self) -> None:
        """Підключення, durable-черга з x-max-length, QoS(prefetch)."""
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError

    async def publish_batch(self, documents: list[dict[str, Any]]) -> None:
        raise NotImplementedError

    async def consume(self, callback: BatchCallback) -> None:
        """Споживає пакети; ack після успішного callback, nack(requeue=True) при винятку."""
        raise NotImplementedError
