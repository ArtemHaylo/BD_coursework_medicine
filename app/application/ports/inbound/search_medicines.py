"""Вхідний порт: пошук препаратів (запит №1)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.search import SearchQuery, SearchResult


class SearchMedicines(ABC):
    @abstractmethod
    async def handle(self, query: SearchQuery) -> SearchResult: ...
