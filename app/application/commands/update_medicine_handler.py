"""CRUD Update: оновлення в MongoDB, перебудова запису в ES, інвалідація кешу картки."""
from __future__ import annotations

from uuid import UUID

from app.application.dto.medicine import MedicineCard, MedicineUpdateDto
from app.application.ports.inbound.update_medicine import UpdateMedicine
from app.domain.ports.outbound import CacheStore, DocumentRepository, SearchIndex


class UpdateMedicineHandler(UpdateMedicine):
    def __init__(self, documents: DocumentRepository, search_index: SearchIndex,
                 cache: CacheStore) -> None:
        self._documents = documents
        self._search_index = search_index
        self._cache = cache

    async def handle(self, medicine_id: UUID, dto: MedicineUpdateDto) -> MedicineCard:
        """Кидає MedicineNotFoundError, якщо препарату немає."""
        raise NotImplementedError
