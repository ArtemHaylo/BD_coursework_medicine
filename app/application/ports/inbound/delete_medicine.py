"""Вхідний порт: видалення препарату (CRUD: Delete)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class DeleteMedicine(ABC):
    @abstractmethod
    async def handle(self, medicine_id: UUID) -> bool: ...
