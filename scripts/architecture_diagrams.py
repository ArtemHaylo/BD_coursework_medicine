"""Будує схеми архітектури з реального коду (AST) і перевіряє правила залежностей.

Схеми не малюються вручну: їх породжує цей скрипт, тому вони завжди збігаються з
репозиторієм. Для фінальної схеми проєкту достатньо запустити його ще раз.

Створює у docs/architecture/:
  modules.{dot,svg,png}   - залежності між модулями (імпорти між пакетами), зі шарами;
  usecases.{dot,svg,png}  - зв'язки між класами: контролер -> сценарій (порт + обробник)
                            -> вихідний порт -> адаптер -> сховище;
  checks.txt              - результат перевірок (порушення правил, сироти).

Запуск (з кореня проєкту; потрібен Graphviz `dot`):
    python scripts/architecture_diagrams.py [--date 10.10.2026]
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "architecture"
SOURCES = ("app", "workers")
FONT = "DejaVu Sans"

# Дозволені залежності між шарами (гексагональна архітектура, розділ 3 звіту).
ALLOWED = {
    "domain": set(),
    "application": {"domain"},
    "infrastructure": {"domain"},
    "infrastructure.config": {"domain", "application", "infrastructure", "presentation"},
    "presentation": {"application", "domain"},
    "workers": {"application", "domain"},
    "main": {"domain", "application", "infrastructure", "presentation"},
}

LAYER_STYLE = {
    "presentation": ("#e8f0fe", "Presentation"),
    "application": ("#e6f4ea", "Application"),
    "domain": ("#fff4e0", "Domain"),
    "infrastructure": ("#fce8e6", "Infrastructure"),
    "workers": ("#f1e8fb", "Workers (окремі процеси)"),
    "main": ("#eeeeee", "Точка входу"),
}

STORE_BY_PREFIX = (
    ("Mongo", "MongoDB"), ("Neo4j", "Neo4j"), ("Redis", "Redis"),
    ("SearchIndex", "Elasticsearch"), ("Queue", "RabbitMQ"),
)


# ---------------------------------------------------------------- розбір коду
@dataclass
class ClassInfo:
    name: str
    path: Path
    bases: list[str]
    init_types: set[str] = field(default_factory=set)

    @property
    def rel(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


def py_files() -> list[Path]:
    files = []
    for src in SOURCES:
        files += [p for p in (ROOT / src).rglob("*.py") if "__pycache__" not in p.parts]
    main = ROOT / "app" / "main.py"
    return sorted(set(files) | ({main} if main.exists() else set()))


def package_of(path: Path) -> str:
    """Файл -> вузол схеми модулів (підпакет верхнього рівня)."""
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[0] == "workers":
        return "workers." + parts[1] if len(parts) > 1 and parts[1] != "__init__" else "workers"
    if parts[:2] == ["app", "main"]:
        return "main"
    layer, rest = parts[1], parts[2:]
    if layer == "presentation":
        return "presentation." + (rest[0] if rest else "")
    if layer == "application":
        if rest[:1] == ["ports"]:
            return "application.ports.inbound"
        return "application." + (rest[0] if rest else "")
    if layer == "domain":
        if rest[:2] == ["ports", "outbound"]:
            return "domain.ports.outbound"
        return "domain." + (rest[0] if rest else "")
    if layer == "infrastructure":
        return "infrastructure." + (rest[0] if rest else "")
    return layer


def layer_of(package: str) -> str:
    if package == "main":
        return "main"
    if package.startswith("infrastructure.config"):
        return "infrastructure.config"
    return package.split(".")[0]


def module_to_package(module: str) -> str | None:
    """Ім'я імпортованого модуля -> вузол схеми (або None, якщо зовнішній)."""
    if module.startswith("workers"):
        return package_of(ROOT / (module.replace(".", "/") + ".py"))
    if not module.startswith("app"):
        return None
    if module == "app.main":
        return "main"
    return package_of(ROOT / (module.replace(".", "/") + ".py"))


def parse_all():
    classes: dict[str, ClassInfo] = {}
    imports: Counter = Counter()
    for path in py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        src = package_of(path)
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mods = [node.module]
            elif isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            for m in mods:
                dst = module_to_package(m)
                if dst and dst != src:
                    imports[(src, dst)] += 1
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b).split(".")[-1] for b in node.bases]
                info = ClassInfo(node.name, path, bases)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        for arg in item.args.args + item.args.kwonlyargs:
                            if arg.annotation is not None:
                                info.init_types |= set(
                                    re.findall(r"[A-Za-z_][A-Za-z0-9_]*", ast.unparse(arg.annotation)))
                classes[node.name] = info
    return classes, imports


# ------------------------------------------------------------ класифікація
def classify(classes):
    roles = defaultdict(dict)
    for name, c in classes.items():
        rel = c.rel
        if rel.startswith("app/domain/ports/outbound/"):
            roles["out_port"][name] = c
        elif rel.startswith("app/application/ports/inbound/"):
            roles["in_port"][name] = c
        elif rel.startswith(("app/application/commands/", "app/application/queries/")) \
                and name.endswith("Handler"):
            roles["handler"][name] = c
        elif rel.startswith("app/presentation/") and name.endswith("Controller"):
            roles["controller"][name] = c
        elif rel.startswith("app/domain/services/") and not name.startswith("_"):
            roles["service"][name] = c
        elif rel.startswith("app/infrastructure/") and "/config/" not in rel:
            roles["adapter"][name] = c
        elif rel.startswith("workers/"):
            roles["worker"][name] = c
    return roles


def store_of(adapter: str) -> str | None:
    for prefix, store in STORE_BY_PREFIX:
        if adapter.startswith(prefix):
            return store
    return None


# ------------------------------------------------------------ перевірки
def run_checks(classes, roles, imports) -> tuple[list[str], dict]:
    lines, facts = [], {}
    viol = []
    for (src, dst), n in sorted(imports.items()):
        ls, ld = layer_of(src), layer_of(dst)
        if ld == ls:
            continue
        # імпорти всередині infrastructure: config -> інші підпакети дозволені
        allowed = ALLOWED.get(ls, set())
        if ld.split(".")[0] not in allowed and ld not in allowed:
            viol.append(f"{src} -> {dst} ({n} імп.)")
    facts["violations"] = viol
    lines.append("1. Порушення правила залежностей (імпорти проти напрямку до домену)")
    lines += [f"   ! {v}" for v in viol] or ["   немає"]

    impl = defaultdict(list)   # вихідний порт -> адаптери
    for a, c in roles["adapter"].items():
        for b in c.bases:
            if b in roles["out_port"]:
                impl[b].append(a)
    no_adapter = [p for p in roles["out_port"] if p not in impl]
    lines.append("2. Вихідні порти без адаптера")
    lines += [f"   ! {p}" for p in no_adapter] or ["   немає"]
    facts["no_adapter"] = no_adapter

    handler_of = {}            # вхідний порт -> обробник
    for h, c in roles["handler"].items():
        for b in c.bases:
            if b in roles["in_port"]:
                handler_of[b] = h
    no_handler = [p for p in roles["in_port"] if p not in handler_of]
    lines.append("3. Вхідні порти без обробника")
    lines += [f"   ! {p}" for p in no_handler] or ["   немає"]
    facts["no_handler"] = no_handler

    used_out = {t for c in list(roles["handler"].values()) + list(roles["worker"].values())
                for t in c.init_types if t in roles["out_port"]}
    unused_out = [p for p in roles["out_port"] if p not in used_out]
    lines.append("4. Вихідні порти, які не використовує жоден обробник чи воркер")
    lines += [f"   ? {p}" for p in unused_out] or ["   немає"]
    facts["unused_out"] = unused_out

    used_in = {t for c in list(roles["controller"].values()) + list(roles["worker"].values())
               for t in c.init_types if t in roles["in_port"]}
    unused_in = [p for p in roles["in_port"] if p not in used_in]
    lines.append("5. Вхідні порти, які не викликає жоден контролер чи воркер")
    lines += [f"   ? {p}" for p in unused_in] or ["   немає"]
    facts["unused_in"] = unused_in

    app_imports_infra = [f"{s} -> {d}" for (s, d) in imports
                         if layer_of(s) in ("domain", "application") and layer_of(d).startswith("infrastructure")]
    lines.append("6. Domain/Application, що імпортують Infrastructure")
    lines += [f"   ! {x}" for x in app_imports_infra] or ["   немає"]

    cross = sorted(f"{s} -> {d}" for (s, d) in imports
                   if layer_of(s) == "workers" and layer_of(d) == "application"
                   and d != "application.ports.inbound")
    lines.append("7. Воркери залежать від application не лише через вхідні порти")
    lines += [f"   ? {x}" for x in cross] or ["   немає"]
    facts["worker_cross"] = cross
    return lines, facts


# ------------------------------------------------------------ DOT
def q(s: str) -> str:
    return '"' + s.replace('"', '\\"') + '"'


def dot_modules(imports, violations, date_label) -> str:
    packages = sorted({p for e in imports for p in e})
    by_layer = defaultdict(list)
    for p in packages:
        by_layer[layer_of(p).split(".")[0]].append(p)
    out = ["digraph modules {",
           f'  graph [rankdir=TB, fontname="{FONT}", fontsize=16, nodesep=0.3, ranksep=0.7, '
           f'label="Залежності між модулями (станом на {date_label})", labelloc=t, compound=true];',
           f'  node [shape=box, style="rounded,filled", fillcolor=white, fontname="{FONT}", fontsize=14];',
           f'  edge [fontname="{FONT}", fontsize=11, color="#555555"];']
    for layer, pkgs in by_layer.items():
        color, title = LAYER_STYLE[layer]
        out.append(f"  subgraph cluster_{layer} {{ label={q(title)}; style=filled; color={q(color)}; "
                   f"fontname={q(FONT)}; fontsize=14;")
        for p in pkgs:
            short = p.split(".", 1)[1] if "." in p else p
            out.append(f"    {q(p)} [label={q(short)}];")
        out.append("  }")
    bad = {tuple(v.split(" (")[0].split(" -> ")) for v in violations}
    for (s, d), n in sorted(imports.items()):
        if layer_of(s) == layer_of(d):
            continue
        attrs = f'label="{n}"'
        if (s, d) in bad:
            attrs += ', color="#d93025", fontcolor="#d93025", penwidth=2'
        out.append(f"  {q(s)} -> {q(d)} [{attrs}];")
    if "presentation.stream" in packages and "workers.ingest_worker" in packages:
        out.append('  "presentation.stream" -> "workers.ingest_worker" [style=invis];')
    out.append("}")
    return "\n".join(out)


def dot_usecases(classes, roles, date_label) -> str:
    """П'ять колонок зліва направо: вхід -> сценарій -> вихідний порт -> адаптер -> сховище."""
    out_ports, in_ports = roles["out_port"], roles["in_port"]
    handler_of = {}
    for h, c in roles["handler"].items():
        for b in c.bases:
            if b in in_ports:
                handler_of[b] = h
    workers = sorted(w for w in roles["worker"] if classes[w].bases != ["Protocol"])
    adapters = sorted(a for a, c in roles["adapter"].items() if any(b in out_ports for b in c.bases))
    stores = sorted({store_of(a) for a in adapters if store_of(a)})
    controllers = sorted(roles["controller"])

    out = ["digraph usecases {",
           f'  graph [rankdir=LR, fontname="{FONT}", fontsize=16, nodesep=0.2, ranksep=1.0, '
           f'label=<<B>Зв\'язки між класами (станом на {date_label})</B><BR/>'
           f'<FONT POINT-SIZE="12">Колонки зліва направо: Presentation і процеси → Application (вхідний порт ⇐ обробник) → '
           f'Domain (вихідні порти) → Infrastructure (адаптери) → сховища<BR/>'
           f'Червоний пунктир з порожнім трикутником: адаптер реалізує порт; '
           f'фіолетовий пунктир: процес напряму використовує вихідний порт</FONT>>, '
           f'labelloc=t, splines=spline];',
           f'  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=13, margin="0.10,0.05"];',
           f'  edge [fontname="{FONT}", fontsize=10, color="#666666", arrowsize=0.7];']

    def column(key, title, color, nodes):
        out.append("  { rank=same; " + "; ".join(q(n) for n, _ in nodes) + "; }")
        for n, label in nodes:
            attr = f"label={q(label)}, " if label else ""
            shape = ", shape=cylinder" if key == "db" else ""
            out.append(f"  {q(n)} [{attr}fillcolor={q(color)}{shape}];")

    column("in", "Presentation та процеси", "#e8f0fe",
           [(c, None) for c in controllers] + [(w, None) for w in workers])
    uc = []
    for p in sorted(in_ports):
        h = handler_of.get(p, "—")
        svc = sorted(t for t in classes[h].init_types if t in roles["service"]) if h in classes else []
        uc.append((p, f"{p}\\n⇐ {h}" + (f"\\nслужби: {', '.join(svc)}" if svc else "")))
    column("uc", "Application: вхідний порт ⇐ обробник", "#e6f4ea", uc)
    column("port", "Domain: вихідні порти", "#fff4e0", [(p, None) for p in sorted(out_ports)])
    column("ad", "Infrastructure: адаптери", "#fce8e6", [(a, None) for a in adapters])
    column("db", "Сховища", "#e8eaed", [(s, None) for s in stores])

    for c in controllers:
        for t in sorted(classes[c].init_types & set(in_ports)):
            out.append(f"  {q(c)} -> {q(t)};")
    for w in workers:
        for t in sorted(classes[w].init_types & set(in_ports)):
            out.append(f"  {q(w)} -> {q(t)};")
        for t in sorted(classes[w].init_types & set(out_ports)):
            out.append(f"  {q(w)} -> {q(t)} [style=dashed, color=\"#7b3fb5\"];")
    for p, h in sorted(handler_of.items()):
        for t in sorted(classes[h].init_types & set(out_ports)):
            out.append(f"  {q(p)} -> {q(t)};")
    for a in adapters:
        for b in classes[a].bases:
            if b in out_ports:     # реалізація: порожній трикутник біля інтерфейсу
                out.append(f"  {q(b)} -> {q(a)} [dir=back, arrowtail=empty, style=dashed, color=\"#b03a2e\"];")
        if store_of(a):
            out.append(f"  {q(a)} -> {q(store_of(a))};")
    out.append("}")
    return "\n".join(out)


def render(dot_src: str, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.dot").write_text(dot_src, encoding="utf-8")
    for fmt, extra in (("svg", []), ("png", ["-Gdpi=170"])):
        subprocess.run(["dot", f"-T{fmt}", *extra, str(OUT / f"{name}.dot"),
                        "-o", str(OUT / f"{name}.{fmt}")], check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().strftime("%d.%m.%Y"))
    args = ap.parse_args()
    if shutil.which("dot") is None:
        print("Потрібен Graphviz (команда `dot`).", file=sys.stderr)
        return 2
    classes, imports = parse_all()
    roles = classify(classes)
    lines, facts = run_checks(classes, roles, imports)
    render(dot_modules(imports, facts["violations"], args.date), "modules")
    render(dot_usecases(classes, roles, args.date), "usecases")
    summary = (f"Дата: {args.date}\nКлас: {len(classes)}; контролерів {len(roles['controller'])}, "
               f"вхідних портів {len(roles['in_port'])}, обробників {len(roles['handler'])}, "
               f"вихідних портів {len(roles['out_port'])}, адаптерів {len(roles['adapter'])}, "
               f"доменних служб {len(roles['service'])}\n\n")
    text = summary + "\n".join(lines) + "\n"
    (OUT / "checks.txt").write_text(text, encoding="utf-8")
    print(text)
    return 1 if facts["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
