"""Доменна служба: валідація документа перед записом."""
from __future__ import annotations

from app.domain.entities.medicine import Medicine


class DocumentValidator:
    def validate(self, medicine: Medicine) -> list[str]:
        """Повертає список помилок (порожній = валідно).

        Перевірки: непорожнє name, therapeutic_class не порожній (ключ шардінгу),
        price у межах 50..1500, medicine_id є UUID.
        """
        raise NotImplementedError

    def ensure_valid(self, medicine: Medicine) -> None:
        """Кидає ValidationError, якщо validate() повернув помилки."""
        raise NotImplementedError
