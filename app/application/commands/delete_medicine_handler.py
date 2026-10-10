"""CRUD Delete: видалення з MongoDB, Elasticsearch і Neo4j, інвалідація кешу."""
from __future__ import annotations

from uuid import UUID

from app.application.ports.inbound.delete_medicine import DeleteMedicine
from app.domain.ports.outbound import CacheStore, DocumentRepository, GraphRepository, SearchIndex


class DeleteMedicineHandler(DeleteMedicine):
    def __init__(self, documents: DocumentRepository, search_index: SearchIndex,
                 graph: GraphRepository, cache: CacheStore) -> None:
        self._documents = documents
        self._search_index = search_index
        self._graph = graph
        self._cache = cache

    async def handle(self, medicine_id: UUID) -> bool:
        raise NotImplementedError
