"""Вихідний порт: CRUD-репозиторій довідника «Хвороба» (адаптер: Neo4j).

Хвороби живуть лише в графі (вузол :Disease), окремої колекції в MongoDB немає.
Ребра ЛІКУЄ створює GraphRepository.upsert_many; цей порт керує самими вузлами.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.entities.disease import Disease


class DiseaseRepository(ABC):
    # --- Create ---
    @abstractmethod
    async def create(self, disease: Disease) -> Disease:
        """MERGE за disease_id; повторний виклик не створює дубля."""

    # --- Read ---
    @abstractmethod
    async def get_by_id(self, disease_id: UUID) -> Disease | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Disease | None:
        """Пошук за нормалізованою назвою (нижній регістр)."""

    @abstractmethod
    async def list_all(self, name_prefix: str | None = None, limit: int = 50,
                       offset: int = 0) -> list[Disease]:
        """Сторінка довідника, за потреби відфільтрована за початком назви."""

    # --- Update / Delete ---
    @abstractmethod
    async def update(self, disease_id: UUID, changes: dict[str, Any]) -> Disease | None:
        """Часткове оновлення (name). drug_count не редагується: він обчислюється з ребер."""

    @abstractmethod
    async def delete(self, disease_id: UUID) -> bool:
        """DETACH DELETE: видаляє вузол разом із ребрами ЛІКУЄ."""
