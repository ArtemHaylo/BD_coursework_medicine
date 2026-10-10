"""Композиційний корінь: єдине місце, що знає і порти, і їхні реалізації.

Створює клієнти БД, адаптери та підставляє їх у обробники (інверсія залежностей).
Решта коду працює лише з інтерфейсами.
"""
from __future__ import annotations

from app.application.commands import (
    ConfigureRateHandler, CreateMedicineHandler, DeleteMedicineHandler,
    IngestDocumentHandler, UpdateMedicineHandler,
)
from app.application.queries import (
    GetAnaloguesHandler, GetMedicineCardHandler, GetStatsHandler,
    ListMedicinesHandler, SearchMedicinesHandler,
)
from app.infrastructure.settings import Settings
from app.infrastructure.messaging import QueueAdapter
from app.infrastructure.observability import MongoMetricsAdapter
from app.infrastructure.persistence import (
    MongoDocumentAdapter, Neo4jGraphAdapter, RedisCacheAdapter, SearchIndexAdapter,
)


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.documents: MongoDocumentAdapter | None = None
        self.search_index: SearchIndexAdapter | None = None
        self.graph: Neo4jGraphAdapter | None = None
        self.cache: RedisCacheAdapter | None = None
        self.metrics: MongoMetricsAdapter | None = None
        self.queue: QueueAdapter | None = None

    async def start(self) -> None:
        """Створює клієнти (Mongo, ES, Neo4j, Redis, RabbitMQ) та адаптери; ensure_* для індексів."""
        raise NotImplementedError

    async def close(self) -> None:
        """Закриває всі з'єднання."""
        raise NotImplementedError

    # --- фабрики обробників (шлях запитів) ---
    def search_medicines_handler(self) -> SearchMedicinesHandler:
        raise NotImplementedError

    def get_medicine_card_handler(self) -> GetMedicineCardHandler:
        raise NotImplementedError

    def get_analogues_handler(self) -> GetAnaloguesHandler:
        raise NotImplementedError

    def list_medicines_handler(self) -> ListMedicinesHandler:
        raise NotImplementedError

    def get_stats_handler(self) -> GetStatsHandler:
        raise NotImplementedError

    # --- фабрики обробників (шлях команд) ---
    def ingest_document_handler(self) -> IngestDocumentHandler:
        raise NotImplementedError

    def configure_rate_handler(self) -> ConfigureRateHandler:
        raise NotImplementedError

    def create_medicine_handler(self) -> CreateMedicineHandler:
        raise NotImplementedError

    def update_medicine_handler(self) -> UpdateMedicineHandler:
        raise NotImplementedError

    def delete_medicine_handler(self) -> DeleteMedicineHandler:
        raise NotImplementedError
