"""DTO шляху команд: документ і пакет від генератора."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.medicine import MedicineCreateDto


class IngestDocumentDto(MedicineCreateDto):
    """Документ з генератора: як створення, плюс id із датасету і текст для ES."""
    medicine_id: UUID
    source_id: int
    full_description: str = ""  # потрапляє лише в Elasticsearch


class IngestBatchDto(BaseModel):
    documents: list[IngestDocumentDto]


class IngestResultDto(BaseModel):
    accepted: int
    rejected: int
    errors: list[str] = Field(default_factory=list)
