"""Сутність «Симптом / Побічний ефект» (табл. 2.3). Вузол графа Neo4j."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Symptom:
    symptom_id: UUID
    name: str
    drug_count: int = 0             # обчислюється з ребер ВИКЛИКАЄ
