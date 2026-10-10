"""DTO аналогів (обхід графа)."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AnalogueQuery(BaseModel):
    medicine_id: UUID
    depth: int = Field(default=1, ge=1, le=2)
    exclude_symptoms: list[str] = Field(default_factory=list)  # напр. ["nausea"]


class AnalogueDto(BaseModel):
    medicine_id: UUID
    name: str
    therapeutic_class: str
    price: float
