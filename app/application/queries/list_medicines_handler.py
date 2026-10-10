"""Фільтрація каталогу за атрибутами (MongoDB)."""
from __future__ import annotations

from app.application.dto.medicine import MedicineListQuery, MedicineListResult
from app.application.ports.inbound.list_medicines import ListMedicines
from app.domain.ports.outbound import DocumentRepository


class ListMedicinesHandler(ListMedicines):
    def __init__(self, documents: DocumentRepository) -> None:
        self._documents = documents

    async def handle(self, query: MedicineListQuery) -> MedicineListResult:
        raise NotImplementedError
