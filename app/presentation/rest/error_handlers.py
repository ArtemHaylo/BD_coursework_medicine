"""Перетворення доменних винятків у HTTP-відповіді."""
from __future__ import annotations

from fastapi import FastAPI


def register_exception_handlers(app: FastAPI) -> None:
    """MedicineNotFoundError -> 404, ValidationError -> 422, решта -> 500 з логуванням."""
    raise NotImplementedError
