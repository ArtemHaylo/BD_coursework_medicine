"""Окремий процес: генератор навантаження.

Читає підготовлені файли (prepared/medicines.jsonl + search_docs.jsonl), формує пакети
з потрібною швидкістю і публікує їх у чергу. Перед кожним пакетом зчитує config:rate з Redis.
Запуск: python -m workers.generator
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from app.application.commands.configure_rate_handler import RATE_KEY
from app.domain.ports.outbound import CacheStore, QueuePublisher


class LoadGenerator:
    def __init__(self, publisher: QueuePublisher, cache: CacheStore,
                 prepared_dir: Path = Path("prepared"), batch_size: int = 100,
                 default_rate: int = 100, rate_key: str = RATE_KEY) -> None:
        self._publisher = publisher
        self._cache = cache
        self._prepared_dir = prepared_dir
        self._batch_size = batch_size
        self._default_rate = default_rate
        self._rate_key = rate_key
        self._running = False

    def iter_batches(self) -> Iterator[list[dict[str, Any]]]:
        """Читає medicines.jsonl і search_docs.jsonl (однаковий порядок), додає full_description
        до кожного документа й віддає пакети по batch_size."""
        raise NotImplementedError

    async def read_rate(self) -> int:
        """Поточна швидкість із Redis (10..5000 док/с); якщо ключа немає, default_rate."""
        raise NotImplementedError

    @staticmethod
    def compute_delay(rate: int, batch_size: int) -> float:
        """Пауза між пакетами (с), щоб тримати rate док/с."""
        raise NotImplementedError

    async def run(self) -> None:
        """Цикл: read_rate -> publish_batch -> sleep(delay) до кінця файлу або stop()."""
        raise NotImplementedError

    def stop(self) -> None:
        self._running = False


async def main() -> None:
    """Збирає LoadGenerator із Container і запускає run()."""
    raise NotImplementedError


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
