"""Вхідний порт: картка препарату за id (запит №3)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.application.dto.medicine import MedicineCard


class GetMedicineCard(ABC):
    @abstractmethod
    async def handle(self, medicine_id: UUID) -> MedicineCard: ...
