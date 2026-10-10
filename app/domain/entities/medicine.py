"""Сутність «Препарат» (табл. 1.4 / 2.1).

Поле full_description тут навмисно відсутнє: воно існує лише в індексі
Elasticsearch (див. SearchDocument).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class Medicine:
    medicine_id: UUID               # UUID5 від name
    source_id: int                  # id у вихідному датасеті
    name: str
    therapeutic_class: str          # частина ключа шардінгу; "unknown", якщо порожнє
    is_habit_forming: bool
    is_prescription: bool           # генерується програмно
    manufacturer: str               # генерується програмно
    price: float                    # генерується програмно (50..1500)
    chemical_class: str | None = None
    action_class: str | None = None
    uses: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)
    substitutes: list[str] = field(default_factory=list)
