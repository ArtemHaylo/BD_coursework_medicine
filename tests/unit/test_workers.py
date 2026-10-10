"""Воркери залежать від портів; адаптери вони отримують лише через Container у main()."""
import ast
from pathlib import Path

from workers.generator import LoadGenerator
from workers.ingest_worker import IngestWorker

WORKERS = Path(__file__).resolve().parents[2] / "workers"
FORBIDDEN = ("app.infrastructure.persistence", "app.infrastructure.messaging",
             "app.infrastructure.observability", "app.presentation")


def test_workers_construct_with_ports():
    LoadGenerator(publisher=None, cache=None)
    IngestWorker(ingest=None, source=None)


def test_workers_do_not_import_concrete_adapters():
    for file in WORKERS.glob("*.py"):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(FORBIDDEN), f"{file}: {node.module}"
