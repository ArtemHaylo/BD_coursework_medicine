"""Доменна служба: обчислення ключа шардінгу MongoDB."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.medicine import Medicine


@dataclass(frozen=True)
class ShardKey:
    """Складений ключ { therapeutic_class: 1, medicine_id: 1 }."""
    therapeutic_class: str
    medicine_id: UUID


class ShardKeyService:
    def compute(self, medicine: Medicine) -> ShardKey:
        """Будує ShardKey; порожній therapeutic_class замінює на 'unknown'."""
        raise NotImplementedError
