"""Архітектура перевіряється з вихідного коду: правило шарів, цикли, контракти портів."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("arch_diagrams", ROOT / "tools" / "arch_diagrams.py")
arch = importlib.util.module_from_spec(_spec)
sys.modules["arch_diagrams"] = arch   # потрібно для dataclass у Python 3.12
_spec.loader.exec_module(arch)
MODEL = arch.build_model(ROOT)


def test_no_layer_violations():
    assert arch.find_violations(MODEL) == []


def test_no_package_cycles():
    assert arch.find_cycles(MODEL) == []


def test_every_port_has_implementation_and_every_handler_a_port():
    assert arch.contract_problems(MODEL) == []


def test_diagrams_are_built_from_current_code():
    diagrams = arch.all_diagrams(MODEL, "01.01.2026")
    assert len(diagrams) == 6
    for name, dot in diagrams.items():
        assert dot.startswith("digraph"), name
        assert "01.01.2026" in dot, name        # дата стоїть на кожній схемі
