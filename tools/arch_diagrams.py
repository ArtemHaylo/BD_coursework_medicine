#!/usr/bin/env python3
"""Будує схеми архітектури безпосередньо з вихідного коду та перевіряє правило залежностей.

Використання (з кореня проєкту):
    python tools/arch_diagrams.py --out docs/diagrams            # DOT + PNG + SVG + summary.json
    python tools/arch_diagrams.py --out docs/diagrams --no-render  # лише DOT і summary.json
    python tools/arch_diagrams.py --check                        # лише перевірка; код 1 при порушеннях

PNG/SVG потребують Graphviz (команда `dot`). Без нього створюються лише .dot і summary.json.
Лише стандартна бібліотека Python. На кожній схемі стоїть дата (параметр --date, інакше сьогодні).
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

SOURCE_DIRS = ("app", "workers")

# шар -> (назва, колір заливки, колір рамки)
LAYERS = {
    "presentation": ("Presentation", "#E3ECFB", "#2F5DA8"),
    "application": ("Application", "#E2F3E4", "#2E7D32"),
    "domain": ("Domain", "#FFF3D6", "#B8860B"),
    "infrastructure": ("Infrastructure", "#FBE3E3", "#B23A3A"),
    "config": ("Композиційний корінь", "#F7D9D9", "#8E2B2B"),
    "workers": ("Workers", "#EBE3F7", "#6A4BA3"),
    "entry": ("Точка входу", "#EEEEEE", "#666666"),
}

# дозволені залежності між шарами (всередині шару дозволено все)
ALLOWED = {
    "domain": set(),
    "application": {"domain"},
    "infrastructure": {"domain"},
    "presentation": {"application", "domain"},
    "workers": {"domain", "application", "config"},
    "config": {"domain", "application", "infrastructure"},
    "entry": {"domain", "application", "infrastructure", "config", "presentation"},
}

STEREO = {
    "entity": "entity", "value": "value object", "service": "domain service", "exception": "exception",
    "outbound_port": "outbound port", "inbound_port": "inbound port",
    "handler": "handler", "dto": "DTO", "adapter": "adapter",
    "controller": "controller", "worker": "process", "protocol": "protocol",
    "container": "composition root", "settings": "settings", "other": "class",
}


# --------------------------------------------------------------------------- модель
@dataclass
class ClassInfo:
    name: str
    module: str
    layer: str
    kind: str
    bases: list[str] = field(default_factory=list)
    fields: list[tuple[str, str]] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    ctor: list[str] = field(default_factory=list)
    sig: list[str] = field(default_factory=list)
    annotated: list[str] = field(default_factory=list)  # усі імена в анотаціях (для Container)
    inherits: list[str] = field(default_factory=list)   # лише відомі класи проєкту


@dataclass
class Model:
    classes: dict[str, ClassInfo] = field(default_factory=dict)
    nodes: set[str] = field(default_factory=set)
    edges: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    modules: int = 0


def layer_of(module: str) -> str:
    p = module.split(".")
    if p[0] == "workers":
        return "workers"
    if len(p) < 2:
        return "entry"
    sub = p[1]
    if sub == "infrastructure" and len(p) > 2 and p[2] == "config":
        return "config"
    return sub if sub in ("domain", "application", "infrastructure", "presentation") else "entry"


def node_of(module: str) -> str:
    p = module.split(".")
    if p[0] == "workers":
        return ".".join(p[:2])
    return ".".join(p[:3]) if len(p) > 2 else module


def classify(module: str, cls: ast.ClassDef, bases: list[str]) -> str:
    if "Protocol" in bases:
        return "protocol"
    if module.startswith("app.domain.entities"):
        return "entity"
    if module.startswith("app.domain.services"):
        has_logic = any(isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef)) for i in cls.body)
        return "service" if has_logic else "value"
    if module.startswith("app.domain.errors"):
        return "exception"
    if module.startswith("app.domain.ports"):
        return "outbound_port"
    if module.startswith("app.application.ports"):
        return "inbound_port"
    if module.startswith(("app.application.commands", "app.application.queries")):
        return "handler"
    if module.startswith("app.application.dto"):
        return "dto"
    if module.startswith("app.infrastructure.config.container"):
        return "container"
    if module.endswith("settings"):
        return "settings"
    if module.startswith("app.infrastructure"):
        return "adapter" if cls.name.endswith("Adapter") else "other"
    if module.startswith("app.presentation"):
        return "controller"
    if module.startswith("workers"):
        return "worker"
    return "other"


def names_in(node: ast.AST | None) -> list[str]:
    if node is None:
        return []
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.append(n.id)
        elif isinstance(n, ast.Attribute):
            out.append(n.attr)
    return out


def module_name(root: Path, path: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def parse_class(module: str, cls: ast.ClassDef) -> ClassInfo:
    bases = []
    for b in cls.bases:
        bases += names_in(b)
    info = ClassInfo(cls.name, module, layer_of(module), classify(module, cls, bases), bases=bases)
    for item in cls.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            info.fields.append((item.target.id, ast.unparse(item.annotation)))
        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name == "__init__":
                for a in item.args.args[1:] + item.args.kwonlyargs:
                    info.ctor += names_in(a.annotation)
                for n in ast.walk(item):
                    if isinstance(n, ast.AnnAssign):
                        info.annotated += names_in(n.annotation)
            elif not item.name.startswith("_"):
                info.methods.append(item.name)
                for a in item.args.args[1:] + item.args.kwonlyargs:
                    info.sig += names_in(a.annotation)
                info.sig += names_in(item.returns)
                info.annotated += names_in(item.returns)
    return info


def build_model(root: Path) -> Model:
    model = Model()
    trees: dict[str, ast.Module] = {}
    for d in SOURCE_DIRS:
        for path in sorted((root / d).rglob("*.py")):
            mod = module_name(root, path)
            trees[mod] = ast.parse(path.read_text(encoding="utf-8"))
            model.nodes.add(node_of(mod))
            if path.name != "__init__.py":
                model.modules += 1
    for mod, tree in trees.items():
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef):
                model.classes.setdefault(stmt.name, parse_class(mod, stmt))
        for n in ast.walk(tree):
            targets = []
            if isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                targets.append(n.module)
            elif isinstance(n, ast.Import):
                targets += [a.name for a in n.names]
            for t in targets:
                if t.split(".")[0] in SOURCE_DIRS:
                    a, b = node_of(mod), node_of(t)
                    if a != b:
                        model.edges[(a, b)] += 1
    known = set(model.classes)
    for c in model.classes.values():
        c.inherits = [b for b in c.bases if b in known and b != c.name]
        c.ctor = [n for n in dict.fromkeys(c.ctor) if n in known and n != c.name]
        c.sig = [n for n in dict.fromkeys(c.sig) if n in known and n != c.name]
        c.annotated = [n for n in dict.fromkeys(c.annotated) if n in known and n != c.name]
    return model


# --------------------------------------------------------------------------- перевірки
def find_violations(model: Model) -> list[str]:
    out = []
    for (a, b), n in sorted(model.edges.items()):
        la, lb = layer_of(a), layer_of(b)
        if la != lb and lb not in ALLOWED[la]:
            out.append(f"{a} ({la}) -> {b} ({lb}): імпортів {n}")
    return out


def find_cycles(model: Model) -> list[list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for (a, b) in model.edges:
        graph[a].add(b)
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on: set[str] = set()
    result: list[list[str]] = []
    counter = [0]

    def visit(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in graph[v]:
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                result.append(sorted(comp))

    for v in sorted(graph):
        if v not in index:
            visit(v)
    return result


def implementers(model: Model, port: str) -> list[str]:
    """Класи, що реалізують порт: явне успадкування або структурно (для Protocol)."""
    p = model.classes[port]
    out = [c.name for c in model.classes.values() if port in c.inherits]
    if p.kind == "protocol" and p.methods:
        need = set(p.methods)
        out += [c.name for c in model.classes.values()
                if c.kind == "adapter" and need <= set(c.methods)]
    return sorted(set(out))


def contract_problems(model: Model) -> list[str]:
    out = []
    for c in model.classes.values():
        if c.kind == "outbound_port" and not [i for i in implementers(model, c.name)]:
            out.append(f"вихідний порт {c.name} не має адаптера")
        if c.kind == "inbound_port":
            handlers = [i for i in implementers(model, c.name) if model.classes[i].kind == "handler"]
            if len(handlers) != 1:
                out.append(f"вхідний порт {c.name}: обробників {len(handlers)} (має бути 1)")
        if c.kind == "handler" and not any(model.classes[b].kind == "inbound_port" for b in c.inherits):
            out.append(f"обробник {c.name} не реалізує вхідний порт")
    return out


def summary(model: Model, today: str) -> dict:
    kinds = defaultdict(int)
    for c in model.classes.values():
        kinds[c.kind] += 1
    impl = sum(len(implementers(model, c.name)) for c in model.classes.values()
               if c.kind in ("inbound_port", "outbound_port", "protocol"))
    return {
        "date": today,
        "modules": model.modules,
        "classes": len(model.classes),
        "by_kind": dict(sorted(kinds.items())),
        "port_implementations": impl,
        "package_edges": len(model.edges),
        "violations": find_violations(model),
        "cycles": find_cycles(model),
        "contract_problems": contract_problems(model),
    }


# --------------------------------------------------------------------------- DOT
def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


HEAD = ('  graph [fontname="DejaVu Sans", fontsize=11, labelloc=t, pad=0.3, nodesep=0.35, ranksep=0.7];\n'
        '  node [fontname="DejaVu Sans", fontsize=10];\n'
        '  edge [fontname="DejaVu Sans", fontsize=9, color="#555555"];\n')

LEGEND = ("суцільна стрілка: залежність через конструктор; пунктир із порожнім трикутником: "
          "реалізація порту; крапки: використання DTO / створення в Container")


def graph_label(title: str, today: str, legend: bool = False) -> str:
    extra = f'<BR/><FONT POINT-SIZE="9">{esc(LEGEND)}</FONT>' if legend else ""
    return (f'  label=<<B>{esc(title)}</B><BR/>'
            f'<FONT POINT-SIZE="10">схему згенеровано з коду: {esc(today)}</FONT>{extra}>;\n')


def class_node(c: ClassInfo, fields: bool = True, methods: bool = True) -> str:
    fill = LAYERS[c.layer][1]
    border = LAYERS[c.layer][2]
    rows = [f'<TR><TD><FONT POINT-SIZE="9"><I>«{esc(STEREO[c.kind])}»</I></FONT></TD></TR>',
            f'<TR><TD><B>{esc(c.name)}</B></TD></TR>']
    if fields and c.fields:
        shown = c.fields[:14]
        lines = "<BR ALIGN=\"LEFT\"/>".join(esc(f"{n}: {t}") for n, t in shown)
        if len(c.fields) > 14:
            lines += "<BR ALIGN=\"LEFT\"/>…"
        rows += ['<HR/>', f'<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="9">{lines}'
                          f'<BR ALIGN="LEFT"/></FONT></TD></TR>']
    if methods and c.methods and c.kind != "container":
        lines = "<BR ALIGN=\"LEFT\"/>".join(esc(m + "()") for m in c.methods[:10])
        rows += ['<HR/>', f'<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="9">{lines}'
                          f'<BR ALIGN="LEFT"/></FONT></TD></TR>']
    return (f'    "{c.name}" [shape=plaintext, label=<<TABLE BORDER="1" CELLBORDER="0" '
            f'CELLSPACING="0" CELLPADDING="3" BGCOLOR="{fill}" COLOR="{border}">'
            f'{"".join(rows)}</TABLE>>];\n')


def clusters(model: Model, names: set[str], fields: bool, methods: bool) -> str:
    out = ""
    for layer in LAYERS:
        members = sorted(n for n in names if model.classes[n].layer == layer)
        if not members:
            continue
        title, fill, border = LAYERS[layer]
        out += (f'  subgraph "cluster_{layer}" {{\n    label="{title}"; style="rounded,filled"; '
                f'fillcolor="{fill}40"; color="{border}"; fontname="DejaVu Sans";\n')
        out += "".join(class_node(model.classes[n], fields, methods) for n in members)
        out += "  }\n"
    return out


def class_edges(model: Model, names: set[str], handler_ctor: bool = True) -> str:
    out, seen = "", set()

    def add(a: str, b: str, attrs: str) -> None:
        if (a, b, attrs) not in seen and a in names and b in names:
            seen.add((a, b, attrs))
            out_list.append(f'  "{a}" -> "{b}" [{attrs}];\n')

    out_list: list[str] = []
    for n in sorted(names):
        c = model.classes[n]
        for b in c.inherits:
            add(n, b, 'style=dashed, arrowhead=empty')
        for d in c.ctor:
            if c.kind != "container" and (handler_ctor or c.kind != "handler"):
                add(n, d, 'arrowhead=vee')
        if c.kind in ("handler", "controller", "inbound_port"):
            for d in c.sig:
                if model.classes[d].kind == "dto":
                    add(n, d, 'style=dotted, arrowhead=open, color="#999999"')
        if c.kind == "service":
            for d in c.sig:
                add(n, d, 'style=dotted, arrowhead=open, color="#999999"')
        if c.kind == "container":
            for d in c.annotated:
                if model.classes[d].kind in ("handler", "adapter"):
                    add(n, d, 'style=dotted, arrowhead=open, color="#B23A3A", label="створює"')
    for p in names:
        if model.classes[p].kind == "protocol":
            for impl in implementers(model, p):
                add(impl, p, 'style=dashed, arrowhead=empty, label="структурно"')
    return "".join(out_list)


def diagram_modules(model: Model, today: str) -> str:
    out = f'digraph modules {{\n  rankdir=LR;\n{HEAD}'
    out += graph_label("Взаємодія модулів коду та правило залежностей", today)
    out += '  node [shape=box, style="rounded,filled"];\n'
    active = {n for e in model.edges for n in e} | {"app.main"}   # без порожніх кореневих пакетів
    by_layer: dict[str, list[str]] = defaultdict(list)
    for n in sorted(model.nodes & active):
        by_layer[layer_of(n)].append(n)
    for layer, members in by_layer.items():
        title, fill, border = LAYERS[layer]
        out += (f'  subgraph "cluster_{layer}" {{ label="{title}"; style="rounded,filled"; '
                f'fillcolor="{fill}55"; color="{border}";\n')
        for n in members:
            out += f'    "{n}" [fillcolor="{fill}", color="{border}", label="{n.replace("app.", "")}"];\n'
        out += "  }\n"
    bad = {(a, b) for (a, b) in model.edges
           if layer_of(a) != layer_of(b) and layer_of(b) not in ALLOWED[layer_of(a)]}
    for (a, b), cnt in sorted(model.edges.items()):
        if (a, b) in bad:
            out += f'  "{a}" -> "{b}" [color="#D50000", penwidth=2.2, label="порушення"];\n'
        else:
            out += f'  "{a}" -> "{b}" [penwidth={1 + min(cnt, 6) * 0.15:.2f}];\n'
    return out + "}\n"


def diagram_domain(model: Model, today: str) -> str:
    names = {c.name for c in model.classes.values()
             if c.kind in ("entity", "value", "service", "exception")}
    out = f'digraph domain {{\n  rankdir=LR;\n{HEAD}  graph [nodesep=0.25, ranksep=0.9];\n'
    out += graph_label("Доменна модель: сутності, служби, винятки", today)
    out += clusters(model, names, True, True) + class_edges(model, names)
    return out + "}\n"


def diagram_ports(model: Model, today: str, side: str) -> str:
    """side='in': контролери -> вхідні порти <- обробники; side='out': вихідні порти <- адаптери."""
    if side == "in":
        kinds = ("controller", "inbound_port", "handler")
        title = "Вхідні порти: контролери та обробники"
    else:
        kinds = ("worker", "outbound_port", "protocol", "adapter")
        title = "Вихідні порти: адаптери баз даних і черги"
    names = {c.name for c in model.classes.values() if c.kind in kinds}
    if side == "in":   # процес-споживач теж користується вхідним портом
        names |= {c.name for c in model.classes.values()
                  if c.kind == "worker" and any(model.classes[d].kind == "inbound_port" for d in c.ctor)}
    out = f'digraph ports_{side} {{\n  rankdir=LR;\n{HEAD}  graph [nodesep=0.12, ranksep=1.0];\n'
    out += graph_label(title, today, True)
    out += "".join(class_node(model.classes[n], False, False) for n in sorted(names))
    out += class_edges(model, names, handler_ctor=False)
    return out + "}\n"


def slice_names(model: Model, seeds: list[str], container: bool = True) -> set[str]:
    selected, queue = set(seeds), list(seeds)
    while queue:
        c = model.classes[queue.pop()]
        nxt = set(c.inherits) | set(c.ctor)
        if c.kind in ("handler", "controller", "inbound_port"):
            nxt |= {d for d in c.sig if model.classes[d].kind == "dto"}
        if c.kind in ("inbound_port", "outbound_port", "protocol"):
            nxt |= set(implementers(model, c.name))
        for n in nxt - selected:
            selected.add(n)
            queue.append(n)
    if container and "Container" in model.classes:
        selected.add("Container")
    return selected


def diagram_slice(model: Model, seeds: list[str], title: str, today: str, name: str,
                  container: bool = True) -> str:
    names = slice_names(model, seeds, container)
    out = f'digraph {name} {{\n  rankdir=LR;\n{HEAD}'
    out += graph_label(title, today, True)
    out += clusters(model, names, False, False) + class_edges(model, names)
    return out + "}\n"


def all_diagrams(model: Model, today: str) -> dict[str, str]:
    return {
        "01_modules": diagram_modules(model, today),
        "02_domain_model": diagram_domain(model, today),
        "03_ports_inbound": diagram_ports(model, today, "in"),
        "04_ports_outbound": diagram_ports(model, today, "out"),
        "05_search_slice": diagram_slice(model, ["SearchController"],
                                         "Зріз «Пошук препаратів» (шлях запитів)", today, "search"),
        "06_ingest_slice": diagram_slice(model, ["IngestWorker", "LoadGenerator"],
                                         "Зріз «Запис документів» (шлях команд)", today, "ingest", container=False),
    }


# --------------------------------------------------------------------------- CLI
def render(dot_file: Path) -> bool:
    if not shutil.which("dot"):
        return False
    for fmt, extra in (("png", ["-Gdpi=200"]), ("svg", [])):
        subprocess.run(["dot", f"-T{fmt}", *extra, str(dot_file),
                        "-o", str(dot_file.with_suffix("." + fmt))], check=True)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="docs/diagrams")
    ap.add_argument("--date", default=date.today().strftime("%d.%m.%Y"))
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--check", action="store_true", help="лише перевірка, без файлів")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    model = build_model(root)
    info = summary(model, args.date)
    problems = info["violations"] + [" ↔ ".join(c) for c in info["cycles"]] + info["contract_problems"]

    print(f"Модулів: {info['modules']}, класів: {info['classes']}, "
          f"реалізацій портів: {info['port_implementations']}")
    for kind, n in info["by_kind"].items():
        print(f"  {kind}: {n}")
    for v in info["violations"]:
        print("ПОРУШЕННЯ ШАРІВ:", v)
    for c in info["cycles"]:
        print("ЦИКЛ МІЖ ПАКЕТАМИ:", " <-> ".join(c))
    for p in info["contract_problems"]:
        print("КОНТРАКТ:", p)
    if args.check:
        print("OK" if not problems else f"Знайдено проблем: {len(problems)}")
        return 1 if problems else 0

    out = (root / args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, dot in all_diagrams(model, args.date).items():
        path = out / f"{name}.dot"
        path.write_text(dot, encoding="utf-8")
        if not args.no_render and not render(path):
            print("Graphviz (dot) не знайдено: створено лише .dot")
            args.no_render = True
    (out / "summary.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Схеми збережено в {out}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
