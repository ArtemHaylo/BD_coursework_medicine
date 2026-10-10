"""Адаптер MongoDB для DocumentRepository (колекція medicines, шардована)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.domain.entities.medicine import Medicine
from app.domain.ports.outbound.document_repository import DocumentRepository

if TYPE_CHECKING:
    from pymongo import AsyncMongoClient


class MongoDocumentAdapter(DocumentRepository):
    def __init__(self, client: AsyncMongoClient, database: str = "medicine",
                 collection: str = "medicines") -> None:
        self._client = client
        self._collection = client[database][collection]

    # --- адміністрування кластера ---
    async def ensure_indexes(self) -> None:
        """Індекси: is_prescription, price, chemical_class, name."""
        raise NotImplementedError

    async def ensure_sharding(self) -> None:
        """enableSharding + shardCollection за ключем {therapeutic_class: 1, medicine_id: 1}."""
        raise NotImplementedError

    # --- мапінг ---
    @staticmethod
    def _to_document(medicine: Medicine) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def _from_document(doc: dict[str, Any]) -> Medicine:
        raise NotImplementedError

    # --- DocumentRepository ---
    async def create(self, medicine: Medicine) -> Medicine:
        raise NotImplementedError

    async def create_many(self, medicines: list[Medicine]) -> int:
        """insert_many(ordered=False)."""
        raise NotImplementedError

    async def get_by_id(self, medicine_id: UUID) -> Medicine | None:
        raise NotImplementedError

    async def by_ids(self, ids: list[UUID]) -> list[Medicine]:
        """Один запит $in; порядок результату відповідає порядку ids."""
        raise NotImplementedError

    async def find(self, filters: dict[str, Any], limit: int = 20, offset: int = 0) -> list[Medicine]:
        raise NotImplementedError

    async def count(self, filters: dict[str, Any]) -> int:
        raise NotImplementedError

    async def top_side_effects(self, chemical_class: str, limit: int = 10) -> list[tuple[str, int]]:
        """Aggregation: $match -> $unwind side_effects -> $group -> $sort -> $limit."""
        raise NotImplementedError

    async def update(self, medicine_id: UUID, changes: dict[str, Any]) -> Medicine | None:
        raise NotImplementedError

    async def delete(self, medicine_id: UUID) -> bool:
        raise NotImplementedError
