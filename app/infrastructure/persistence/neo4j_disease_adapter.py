"""Адаптер Neo4j для DiseaseRepository (вузол :Disease)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.domain.entities.disease import Disease
from app.domain.ports.outbound.disease_repository import DiseaseRepository

if TYPE_CHECKING:
    from neo4j import AsyncDriver


class Neo4jDiseaseAdapter(DiseaseRepository):
    def __init__(self, driver: AsyncDriver, database: str = "neo4j") -> None:
        self._driver = driver
        self._database = database

    @staticmethod
    def _from_record(record: dict[str, Any]) -> Disease:
        """{disease_id, name, drug_count} -> Disease."""
        raise NotImplementedError

    async def create(self, disease: Disease) -> Disease:
        """MERGE (d:Disease {disease_id: $id}) SET d.name = $name."""
        raise NotImplementedError

    async def get_by_id(self, disease_id: UUID) -> Disease | None:
        raise NotImplementedError

    async def get_by_name(self, name: str) -> Disease | None:
        raise NotImplementedError

    async def list_all(self, name_prefix: str | None = None, limit: int = 50,
                       offset: int = 0) -> list[Disease]:
        """MATCH ... WHERE d.name STARTS WITH $prefix ORDER BY d.name SKIP/LIMIT."""
        raise NotImplementedError

    async def update(self, disease_id: UUID, changes: dict[str, Any]) -> Disease | None:
        raise NotImplementedError

    async def delete(self, disease_id: UUID) -> bool:
        """DETACH DELETE."""
        raise NotImplementedError
