"""Адаптер Neo4j для SymptomRepository (вузол :Symptom)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.domain.entities.symptom import Symptom
from app.domain.ports.outbound.symptom_repository import SymptomRepository

if TYPE_CHECKING:
    from neo4j import AsyncDriver


class Neo4jSymptomAdapter(SymptomRepository):
    def __init__(self, driver: AsyncDriver, database: str = "neo4j") -> None:
        self._driver = driver
        self._database = database

    @staticmethod
    def _from_record(record: dict[str, Any]) -> Symptom:
        """{symptom_id, name, drug_count} -> Symptom."""
        raise NotImplementedError

    async def create(self, symptom: Symptom) -> Symptom:
        """MERGE (s:Symptom {symptom_id: $id}) SET s.name = $name."""
        raise NotImplementedError

    async def get_by_id(self, symptom_id: UUID) -> Symptom | None:
        raise NotImplementedError

    async def get_by_name(self, name: str) -> Symptom | None:
        raise NotImplementedError

    async def list_all(self, name_prefix: str | None = None, limit: int = 50,
                       offset: int = 0) -> list[Symptom]:
        """MATCH ... WHERE s.name STARTS WITH $prefix ORDER BY s.name SKIP/LIMIT."""
        raise NotImplementedError

    async def update(self, symptom_id: UUID, changes: dict[str, Any]) -> Symptom | None:
        raise NotImplementedError

    async def delete(self, symptom_id: UUID) -> bool:
        """DETACH DELETE."""
        raise NotImplementedError
