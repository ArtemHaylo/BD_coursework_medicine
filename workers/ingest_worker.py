"""Окремий процес: споживач черги -> пакетний запис у MongoDB, Elasticsearch, Neo4j.

Запуск: python -m workers.ingest_worker
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from app.application.ports.inbound.ingest_document import IngestDocument


class BatchSource(Protocol):
    """Джерело пакетів (QueueAdapter задовольняє цей протокол структурно)."""

    async def consume(self, callback: Callable[[list[dict[str, Any]]], Awaitable[None]]) -> None: ...


class IngestWorker:
    def __init__(self, ingest: IngestDocument, source: BatchSource) -> None:
        self._ingest = ingest
        self._source = source

    async def on_batch(self, documents: list[dict[str, Any]]) -> None:
        """dict -> IngestBatchDto -> IngestDocument.handle(). При помилці кидає виняток,
        щоб адаптер черги не підтвердив (ack) повідомлення."""
        raise NotImplementedError

    async def run(self) -> None:
        """source.consume(self.on_batch)"""
        raise NotImplementedError


async def main() -> None:
    """Збирає IngestWorker із Container і запускає run()."""
    raise NotImplementedError


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
