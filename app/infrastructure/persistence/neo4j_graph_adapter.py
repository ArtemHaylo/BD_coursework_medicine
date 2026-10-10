"""Адаптер Neo4j для GraphRepository (Cypher; ребра ЛІКУЄ, ВИКЛИКАЄ, МАЄ_АНАЛОГ)."""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.entities.medicine import Medicine
from app.domain.ports.outbound.graph_repository import GraphRepository

if TYPE_CHECKING:
    from neo4j import AsyncDriver


class Neo4jGraphAdapter(GraphRepository):
    def __init__(self, driver: AsyncDriver, database: str = "neo4j") -> None:
        self._driver = driver
        self._database = database

    async def ensure_constraints(self) -> None:
        """UNIQUE на medicine_id, disease_id, symptom_id (дають і індекси)."""
        raise NotImplementedError

    async def upsert_many(self, medicines: list[Medicine]) -> int:
        """UNWIND $batch + MERGE вузлів і ребер."""
        raise NotImplementedError

    async def find_analogues(self, medicine_id: UUID, depth: int = 1,
                             exclude_symptoms: list[str] | None = None) -> list[UUID]:
        raise NotImplementedError

    async def find_by_disease(self, disease_name: str, limit: int = 50) -> list[UUID]:
        raise NotImplementedError

    async def exclude_by_symptom(self, medicine_ids: list[UUID], symptom_name: str) -> list[UUID]:
        raise NotImplementedError

    async def delete_medicine(self, medicine_id: UUID) -> bool:
        """DETACH DELETE."""
        raise NotImplementedError
