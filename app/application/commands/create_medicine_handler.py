"""CRUD Create: валідація -> MongoDB + Elasticsearch + Neo4j."""
from __future__ import annotations

from app.application.dto.medicine import MedicineCard, MedicineCreateDto
from app.application.ports.inbound.create_medicine import CreateMedicine
from app.domain.ports.outbound import DocumentRepository, GraphRepository, SearchIndex
from app.domain.services.document_validator import DocumentValidator


class CreateMedicineHandler(CreateMedicine):
    def __init__(self, documents: DocumentRepository, search_index: SearchIndex,
                 graph: GraphRepository, validator: DocumentValidator) -> None:
        self._documents = documents
        self._search_index = search_index
        self._graph = graph
        self._validator = validator

    async def handle(self, dto: MedicineCreateDto) -> MedicineCard:
        raise NotImplementedError
