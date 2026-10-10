"""Читання картки препарату за ключем (кеш -> MongoDB)."""
from __future__ import annotations

from uuid import UUID

from app.application.dto.medicine import MedicineCard
from app.application.ports.inbound.get_medicine_card import GetMedicineCard
from app.domain.ports.outbound import CacheStore, DocumentRepository


class GetMedicineCardHandler(GetMedicineCard):
    def __init__(self, documents: DocumentRepository, cache: CacheStore) -> None:
        self._documents = documents
        self._cache = cache

    async def handle(self, medicine_id: UUID) -> MedicineCard:
        """Кидає MedicineNotFoundError, якщо препарату немає."""
        raise NotImplementedError
