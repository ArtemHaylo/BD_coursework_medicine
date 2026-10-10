"""Сутність «Хвороба» (табл. 2.2). Вузол графа Neo4j."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Disease:
    disease_id: UUID
    name: str
    drug_count: int = 0             # обчислюється з ребер ЛІКУЄ
