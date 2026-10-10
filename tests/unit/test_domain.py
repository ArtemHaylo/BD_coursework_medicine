"""Перевіряє правило залежностей: domain не імпортує інші шари."""
import ast
from pathlib import Path
from uuid import uuid4

from app.domain.entities import Medicine, SearchLogEntry
from app.domain.ports.outbound import DocumentRepository

DOMAIN = Path(__file__).resolve().parents[2] / "app" / "domain"
FORBIDDEN = ("app.application", "app.infrastructure", "app.presentation", "workers")


def _imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_domain_has_no_outward_imports():
    for file in DOMAIN.rglob("*.py"):
        for module in _imports(file):
            assert not module.startswith(FORBIDDEN), f"{file}: {module}"


def test_medicine_defaults():
    m = Medicine(uuid4(), 1, "x", "unknown", False, False, "Acme", 100.0)
    assert m.uses == [] and m.chemical_class is None


def test_search_log_status():
    from datetime import datetime
    e = SearchLogEntry(uuid4(), "A", "a", 0, False, 5, datetime.now())
    assert e.status == "Пусто"


def test_ports_are_abstract():
    try:
        DocumentRepository()
    except TypeError:
        return
    raise AssertionError("порт має бути абстрактним")
