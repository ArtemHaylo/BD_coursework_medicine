"""Об'єкти пошукового індексу Elasticsearch."""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class SearchDocument:
    """Документ для індексації: лише medicine_id, name, full_description."""
    medicine_id: UUID
    name: str
    full_description: str


@dataclass
class SearchHit:
    """Один результат пошуку: id + релевантність + підсвічені фрагменти."""
    medicine_id: UUID
    score: float
    snippets: list[str] = field(default_factory=list)
