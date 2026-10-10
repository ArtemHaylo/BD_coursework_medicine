"""Вихідний порт: CRUD-репозиторій довідника «Симптом / Побічний ефект» (адаптер: Neo4j).

Симптоми живуть лише в графі (вузол :Symptom). Ребра ВИКЛИКАЄ створює
GraphRepository.upsert_many; цей порт керує самими вузлами.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.entities.symptom import Symptom


class SymptomRepository(ABC):
    # --- Create ---
    @abstractmethod
    async def create(self, symptom: Symptom) -> Symptom:
        """MERGE за symptom_id; повторний виклик не створює дубля."""

    # --- Read ---
    @abstractmethod
    async def get_by_id(self, symptom_id: UUID) -> Symptom | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Symptom | None:
        """Пошук за нормалізованою назвою (нижній регістр)."""

    @abstractmethod
    async def list_all(self, name_prefix: str | None = None, limit: int = 50,
                       offset: int = 0) -> list[Symptom]:
        """Сторінка довідника, за потреби відфільтрована за початком назви."""

    # --- Update / Delete ---
    @abstractmethod
    async def update(self, symptom_id: UUID, changes: dict[str, Any]) -> Symptom | None:
        """Часткове оновлення (name). drug_count не редагується: він обчислюється з ребер."""

    @abstractmethod
    async def delete(self, symptom_id: UUID) -> bool:
        """DETACH DELETE: видаляє вузол разом із ребрами ВИКЛИКАЄ."""
