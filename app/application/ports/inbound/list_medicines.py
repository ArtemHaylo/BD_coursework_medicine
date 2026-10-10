"""Вхідний порт: фільтрація каталогу (запит №2)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.medicine import MedicineListQuery, MedicineListResult


class ListMedicines(ABC):
    @abstractmethod
    async def handle(self, query: MedicineListQuery) -> MedicineListResult: ...
