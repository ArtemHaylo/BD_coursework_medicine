"""Контролери збираються з фейкових портів, мають очікувані маршрути й не імпортують infrastructure."""
import ast
from pathlib import Path

from app.presentation.rest import (
    AnaloguesController, MedicineController, RateController, SearchController,
)
from app.presentation.stream import StatsStreamController

PRES = Path(__file__).resolve().parents[2] / "app" / "presentation"
FORBIDDEN = ("app.infrastructure", "workers")


def _paths(controller) -> set[str]:
    return {route.path for route in controller.router.routes}


def test_routes_exist():
    assert "/api/search" in _paths(SearchController(None))
    med = _paths(MedicineController(None, None, None, None, None))
    assert {"/api/medicines", "/api/medicines/{medicine_id}"} <= med
    assert "/api/medicines/{medicine_id}/analogues" in _paths(AnaloguesController(None))
    assert "/api/rate" in _paths(RateController(None))
    assert {"/api/stats", "/api/stream/stats"} <= _paths(StatsStreamController(None))


def test_presentation_has_no_infrastructure_imports():
    for file in PRES.rglob("*.py"):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(FORBIDDEN), f"{file}: {node.module}"
