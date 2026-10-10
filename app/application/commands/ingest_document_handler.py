"""Шлях команд: валідація -> ключ розподілу -> паралельний bulk-запис у 3 сховища -> метрика."""
from __future__ import annotations

from app.application.dto.ingest import IngestBatchDto, IngestResultDto
from app.application.ports.inbound.ingest_document import IngestDocument
from app.domain.ports.outbound import DocumentRepository, GraphRepository, MetricsSink, SearchIndex
from app.domain.services.document_validator import DocumentValidator
from app.domain.services.shard_key_service import ShardKeyService


class IngestDocumentHandler(IngestDocument):
    def __init__(self, documents: DocumentRepository, search_index: SearchIndex,
                 graph: GraphRepository, metrics: MetricsSink,
                 validator: DocumentValidator, shard_keys: ShardKeyService) -> None:
        self._documents = documents
        self._search_index = search_index
        self._graph = graph
        self._metrics = metrics
        self._validator = validator
        self._shard_keys = shard_keys

    async def handle(self, batch: IngestBatchDto) -> IngestResultDto:
        """Записує в усі три сховища (asyncio.gather). Якщо хоч одне впало, кидає виняток,
        щоб ingest_worker не підтвердив (ack) повідомлення."""
        raise NotImplementedError
