"""Сценарій «Пошук препаратів» (рис. 3.5): нормалізація -> кеш -> ES -> MongoDB -> кеш -> метрика."""
from __future__ import annotations

from app.application.dto.search import SearchQuery, SearchResult
from app.application.ports.inbound.search_medicines import SearchMedicines
from app.domain.ports.outbound import CacheStore, DocumentRepository, MetricsSink, SearchIndex
from app.domain.services.query_normalizer import QueryNormalizer


class SearchMedicinesHandler(SearchMedicines):
    def __init__(self, search_index: SearchIndex, cache: CacheStore,
                 documents: DocumentRepository, metrics: MetricsSink,
                 normalizer: QueryNormalizer, cache_ttl_seconds: int = 60) -> None:
        self._search_index = search_index
        self._cache = cache
        self._documents = documents
        self._metrics = metrics
        self._normalizer = normalizer
        self._cache_ttl = cache_ttl_seconds

    async def handle(self, query: SearchQuery) -> SearchResult:
        raise NotImplementedError
