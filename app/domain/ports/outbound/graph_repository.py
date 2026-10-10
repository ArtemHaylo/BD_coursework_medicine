"""Вихідний порт: граф зв'язків (адаптер: Neo4j)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.medicine import Medicine


class GraphRepository(ABC):
    @abstractmethod
    async def upsert_many(self, medicines: list[Medicine]) -> int:
        """Створює вузли Medicine/Disease/Symptom і ребра ЛІКУЄ, ВИКЛИКАЄ, МАЄ_АНАЛОГ."""

    @abstractmethod
    async def find_analogues(self, medicine_id: UUID, depth: int = 1,
                             exclude_symptoms: list[str] | None = None) -> list[UUID]:
        """Аналоги на глибину 1-2, за потреби без указаних побічних ефектів."""

    @abstractmethod
    async def find_by_disease(self, disease_name: str, limit: int = 50) -> list[UUID]:
        """Усі препарати, що лікують хворобу."""

    @abstractmethod
    async def exclude_by_symptom(self, medicine_ids: list[UUID], symptom_name: str) -> list[UUID]:
        """Лишає лише ті препарати, що НЕ викликають указаний симптом."""

    @abstractmethod
    async def delete_medicine(self, medicine_id: UUID) -> bool: ...
