"""Сутність «Пошуковий запит» (табл. 2.4). Службова, для моніторингу."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class SearchLogEntry:
    query_id: UUID
    raw_query: str
    normalized_query: str           
    results_count: int              
    cache_hit: bool
    latency_ms: int
    created_at: datetime

    @property
    def status(self) -> str:
        return "Знайдено" if self.results_count > 0 else "Пусто"
