"""Вхідний порт: створення препарату (CRUD: Create)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.medicine import MedicineCard, MedicineCreateDto


class CreateMedicine(ABC):
    @abstractmethod
    async def handle(self, dto: MedicineCreateDto) -> MedicineCard: ...
