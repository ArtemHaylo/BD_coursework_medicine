"""Перевіряє правило залежностей: domain не імпортує інші шари."""
import ast
from pathlib import Path
from uuid import uuid4

from app.domain.entities import Medicine, SearchLogEntry
from app.domain.ports.outbound import DiseaseRepository, DocumentRepository, SymptomRepository

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
    for port in (DocumentRepository, DiseaseRepository, SymptomRepository):
        try:
            port()
        except TypeError:
            continue
        raise AssertionError(f"порт {port.__name__} має бути абстрактним")


def test_reference_repositories_have_crud():
    """Довідники Хвороба/Симптом мають повний набір CRUD-операцій."""
    crud = {"create", "get_by_id", "get_by_name", "list_all", "update", "delete"}
    for port in (DiseaseRepository, SymptomRepository):
        assert crud <= set(port.__abstractmethods__), port.__name__
