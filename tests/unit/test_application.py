"""Application залежить лише від Domain; кожен обробник реалізує свій вхідний порт."""
import ast
from pathlib import Path

from app.application import commands, queries
from app.application.ports import inbound

APP = Path(__file__).resolve().parents[2] / "app" / "application"
FORBIDDEN = ("app.infrastructure", "app.presentation", "workers")


def test_application_has_no_infrastructure_imports():
    for file in APP.rglob("*.py"):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(FORBIDDEN), f"{file}: {node.module}"


def test_every_handler_implements_an_inbound_port():
    ports = tuple(getattr(inbound, n) for n in inbound.__all__)
    for pkg in (commands, queries):
        for name in pkg.__all__:
            obj = getattr(pkg, name)
            if name.endswith("Handler"):
                assert issubclass(obj, ports), name


def test_handlers_are_stubs():
    import asyncio
    h = commands.ConfigureRateHandler(cache=None)
    try:
        from app.application.dto import RateConfigDto
        asyncio.run(h.handle(RateConfigDto(rate=10)))
    except NotImplementedError:
        return
    raise AssertionError("очікувалась заглушка")
