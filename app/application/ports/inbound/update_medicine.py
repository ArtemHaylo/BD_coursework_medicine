"""Вхідний порт: оновлення препарату (CRUD: Update)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.application.dto.medicine import MedicineCard, MedicineUpdateDto


class UpdateMedicine(ABC):
    @abstractmethod
    async def handle(self, medicine_id: UUID, dto: MedicineUpdateDto) -> MedicineCard: ...
