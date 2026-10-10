"""DTO препарату: картка, створення, оновлення, список."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class MedicineCard(BaseModel):
    """Повна картка препарату (читання за ключем)."""
    medicine_id: UUID
    name: str
    chemical_class: str | None = None
    therapeutic_class: str
    action_class: str | None = None
    is_habit_forming: bool
    is_prescription: bool
    manufacturer: str
    price: float
    uses: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
    substitutes: list[str] = Field(default_factory=list)


class MedicineCreateDto(BaseModel):
    name: str = Field(min_length=1)
    therapeutic_class: str = "unknown"
    chemical_class: str | None = None
    action_class: str | None = None
    is_habit_forming: bool = False
    is_prescription: bool = False
    manufacturer: str
    price: float = Field(ge=50.0, le=1500.0)
    uses: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
    substitutes: list[str] = Field(default_factory=list)


class MedicineUpdateDto(BaseModel):
    """Часткове оновлення: всі поля необов'язкові."""
    therapeutic_class: str | None = None
    chemical_class: str | None = None
    action_class: str | None = None
    is_prescription: bool | None = None
    manufacturer: str | None = None
    price: float | None = Field(default=None, ge=50.0, le=1500.0)
    uses: list[str] | None = None
    side_effects: list[str] | None = None
    substitutes: list[str] | None = None


class MedicineListQuery(BaseModel):
    """Фільтрація за параметрами (запит №2)."""
    is_prescription: bool | None = None
    price_max: float | None = None
    therapeutic_class: str | None = None
    chemical_class: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MedicineListResult(BaseModel):
    items: list[MedicineCard] = Field(default_factory=list)
    total: int = 0
