"""Аналоги препарату: кеш -> Neo4j (id) -> MongoDB (дані для відображення)."""
from __future__ import annotations

from app.application.dto.analogue import AnalogueDto, AnalogueQuery
from app.application.ports.inbound.get_analogues import GetAnalogues
from app.domain.ports.outbound import CacheStore, DocumentRepository, GraphRepository


class GetAnaloguesHandler(GetAnalogues):
    def __init__(self, graph: GraphRepository, documents: DocumentRepository,
                 cache: CacheStore) -> None:
        self._graph = graph
        self._documents = documents  # потрібен, щоб отримати name/price за id із графа
        self._cache = cache

    async def handle(self, query: AnalogueQuery) -> list[AnalogueDto]:
        """Препарати з chemical_class = null не показуються в «Рекомендованих аналогах» (п. 2.5)."""
        raise NotImplementedError
