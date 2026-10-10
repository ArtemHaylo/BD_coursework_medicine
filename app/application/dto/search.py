"""DTO пошуку: SearchQuery (вхід) і SearchResult (вихід)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    raw: str = Field(min_length=1, description="Текст запиту користувача")
    filters: dict[str, Any] = Field(default_factory=dict)  # is_prescription, price_max, ...
    limit: int = Field(default=20, ge=1, le=100)


class SearchItem(BaseModel):
    medicine_id: UUID
    name: str
    therapeutic_class: str
    is_prescription: bool
    price: float
    score: float | None = None
    snippets: list[str] = Field(default_factory=list)  # підсвічені фрагменти


class SearchResult(BaseModel):
    items: list[SearchItem] = Field(default_factory=list)
    total: int = 0
    cache_hit: bool = False
    latency_ms: int = 0
