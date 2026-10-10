"""Адаптери реалізують усі методи портів; infrastructure (крім config) знає лише Domain."""
import ast
from pathlib import Path

from app.domain.ports.outbound import (
    CacheStore, DiseaseRepository, DocumentRepository, GraphRepository, MetricsSink,
    QueuePublisher, SearchIndex, SymptomRepository,
)
from app.infrastructure.messaging import QueueAdapter
from app.infrastructure.observability import MongoMetricsAdapter
from app.infrastructure.persistence import (
    MongoDocumentAdapter, Neo4jDiseaseAdapter, Neo4jGraphAdapter, Neo4jSymptomAdapter,
    RedisCacheAdapter, SearchIndexAdapter,
)

INFRA = Path(__file__).resolve().parents[2] / "app" / "infrastructure"
FORBIDDEN = ("app.application", "app.presentation", "workers")


class _FakeClient(dict):
    def __getitem__(self, key):
        return _FakeClient()


def test_adapters_implement_ports():
    """Створення екземпляра падає з TypeError, якщо лишився нереалізований абстрактний метод."""
    MongoDocumentAdapter(_FakeClient())
    SearchIndexAdapter(None)
    Neo4jGraphAdapter(None)
    Neo4jDiseaseAdapter(None)
    Neo4jSymptomAdapter(None)
    RedisCacheAdapter(None)
    MongoMetricsAdapter(_FakeClient())
    QueueAdapter("amqp://x")


def test_adapter_types():
    assert issubclass(MongoDocumentAdapter, DocumentRepository)
    assert issubclass(SearchIndexAdapter, SearchIndex)
    assert issubclass(Neo4jGraphAdapter, GraphRepository)
    assert issubclass(Neo4jDiseaseAdapter, DiseaseRepository)
    assert issubclass(Neo4jSymptomAdapter, SymptomRepository)
    assert issubclass(RedisCacheAdapter, CacheStore)
    assert issubclass(MongoMetricsAdapter, MetricsSink)
    assert issubclass(QueueAdapter, QueuePublisher)


def test_adapters_do_not_import_application_or_presentation():
    for file in INFRA.rglob("*.py"):
        if "config" in file.relative_to(INFRA).parts:   # композиційний корінь знає все
            continue
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(FORBIDDEN), f"{file}: {node.module}"
