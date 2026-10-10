"""DTO керування швидкістю та моніторингу."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RateConfigDto(BaseModel):
    rate: int = Field(ge=10, le=5000, description="Цільова швидкість, док/с")


class SearchLogDto(BaseModel):
    query_id: UUID
    raw_query: str
    status: str            # «Знайдено» / «Пусто»
    cache_hit: bool
    latency_ms: int
    created_at: datetime


class StatsDto(BaseModel):
    """Знімок статистики для UI (SSE)."""
    current_rate: int
    total_ingested: int
    total_searches: int = 0
    cache_hit_ratio: float = 0.0
    recent_queries: list[SearchLogDto] = Field(default_factory=list)
