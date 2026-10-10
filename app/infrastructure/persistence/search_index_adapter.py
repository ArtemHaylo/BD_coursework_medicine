"""Адаптер Elasticsearch для SearchIndex (індекс medicines: medicine_id, name, full_description)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.domain.entities.search_document import SearchDocument, SearchHit
from app.domain.ports.outbound.search_index import SearchIndex

if TYPE_CHECKING:
    from elasticsearch import AsyncElasticsearch


class SearchIndexAdapter(SearchIndex):
    def __init__(self, client: AsyncElasticsearch, index: str = "medicines") -> None:
        self._client = client
        self._index = index

    async def ensure_index(self) -> None:
        """Створює індекс з mapping (full_description: text, medicine_id: keyword)."""
        raise NotImplementedError

    async def search(self, query: str, filters: dict[str, Any] | None = None,
                     limit: int = 20) -> list[SearchHit]:
        """match по full_description з fuzziness та highlight (snippets)."""
        raise NotImplementedError

    async def index_many(self, documents: list[SearchDocument]) -> int:
        """helpers.async_bulk."""
        raise NotImplementedError

    async def delete(self, medicine_id: UUID) -> bool:
        raise NotImplementedError
