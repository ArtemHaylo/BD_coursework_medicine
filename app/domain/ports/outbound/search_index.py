"""Вихідний порт: повнотекстовий пошук (адаптер: Elasticsearch)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.entities.search_document import SearchDocument, SearchHit


class SearchIndex(ABC):
    @abstractmethod
    async def search(self, query: str, filters: dict[str, Any] | None = None, limit: int = 20) -> list[SearchHit]:
        """Пошук по full_description з підсвічуванням (snippets)."""

    @abstractmethod
    async def index_many(self, documents: list[SearchDocument]) -> int:
        """Bulk-індексація. Повертає кількість проіндексованих."""

    @abstractmethod
    async def delete(self, medicine_id: UUID) -> bool: ...
