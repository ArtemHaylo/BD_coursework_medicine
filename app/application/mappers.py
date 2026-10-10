"""Перетворення Domain <-> DTO. Єдине місце, що знає про обидва формати."""
from __future__ import annotations

from app.application.dto.ingest import IngestDocumentDto
from app.application.dto.medicine import MedicineCard, MedicineCreateDto
from app.domain.entities.medicine import Medicine
from app.domain.entities.search_document import SearchDocument


def medicine_to_card(medicine: Medicine) -> MedicineCard:
    raise NotImplementedError


def create_dto_to_medicine(dto: MedicineCreateDto) -> Medicine:
    """Генерує medicine_id як UUID5 від name (детерміновано, як у конвеєрі даних)."""
    raise NotImplementedError


def ingest_dto_to_medicine(dto: IngestDocumentDto) -> Medicine:
    raise NotImplementedError


def ingest_dto_to_search_document(dto: IngestDocumentDto) -> SearchDocument:
    raise NotImplementedError
