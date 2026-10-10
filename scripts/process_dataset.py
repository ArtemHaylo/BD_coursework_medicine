"""Очищення та підготовка датасету «250k Medicines».

Перший етап конвеєра (розділ 2 звіту, Додаток А): читає medicine_dataset.csv,
нормалізує дані, будує вузли й ребра графа, генерує відсутні поля та тестові
пошукові запити, зберігає файли для кожного сховища (табл. 2.8) у каталог prepared/.

Запуск (з кореня проєкту):
    python scripts/process_dataset.py
"""
import json
import re
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

USE_COLS = [f"use{i}" for i in range(5)]
SIDE_COLS = [f"sideEffect{i}" for i in range(42)]
SUB_COLS = [f"substitute{i}" for i in range(5)]

MANUFACTURERS = [
    "Aurelia Pharma", "Nordvik Labs", "Medisolve", "Helvora Pharmaceuticals",
    "Zenthera", "Carbonex Health", "Lumira Biotech", "Vitalis Group",
    "Orbis Pharma", "Kestrel Medical", "Solvane Labs", "Pharmaxis Europe",
    "Bioclair", "Neurovia", "Tavira Pharma", "Elmora Health",
    "Quantis Pharma", "Raventa Labs", "Silvera Medical", "Dravon Biopharma",
]
UNKNOWN_CLASS = "unknown"


def norm(value) -> str | None:
    """Нормалізація тексту: trim + нижній регістр; порожнє -> None."""
    if pd.isna(value):
        return None
    value = str(value).strip().lower()
    return value or None


def collect(df: pd.DataFrame, cols: list[str]) -> list[list[str]]:
    """Збирає непорожні значення з набору колонок у масив (без дублів, з порядком)."""
    result = []
    for row in df[cols].itertuples(index=False, name=None):
        items = [norm(v) for v in row]
        result.append(list(dict.fromkeys(i for i in items if i)))
    return result


def audit(raw: pd.DataFrame, clean: pd.DataFrame) -> dict:
    """Статистика для розділу 2.1.1: усі цифри звіту беруться звідси."""
    names = set(clean["name"])
    subs = [s for lst in clean["substitutes"] for s in lst]
    raw_subs = raw[SUB_COLS].stack().str.strip()
    return {
        "rows_raw": len(raw),
        "columns": raw.shape[1],
        "name_nulls": int(raw["name"].isna().sum()),
        "duplicates_by_name": len(raw) - raw["name"].map(norm).nunique(),
        "rows_clean": len(clean),
        "chemical_class_filled_%": round(raw["Chemical Class"].notna().mean() * 100, 1),
        "action_class_filled_%": round(raw["Action Class"].notna().mean() * 100, 1),
        "substitute_match_raw_%": round(raw_subs.isin(set(raw["name"])).mean() * 100, 1),
        "substitute_match_normalized_%": round(
            sum(s in names for s in subs) / len(subs) * 100, 1
        ),
        "avg_full_description_chars": round(clean["full_description"].str.len().mean()),
    }


def process_medical_dataset(file_path: str) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(file_path, low_memory=False)
    df = raw.dropna(subset=["name"]).copy()
    df["name"] = df["name"].map(norm)
    df = (df.dropna(subset=["name"])
            .drop_duplicates(subset="name")
            .reset_index(drop=True))

    df["uses"] = collect(df, USE_COLS)
    df["side_effects"] = collect(df, SIDE_COLS)
    df["substitutes"] = collect(df, SUB_COLS)

    df["chemical_class"] = df["Chemical Class"].map(norm)
    df["therapeutic_class"] = df["Therapeutic Class"].map(norm)
    df["action_class"] = df["Action Class"].map(norm)
    df["is_habit_forming"] = df["Habit Forming"].map(norm).eq("yes")
    df["medicine_id"] = df["name"].map(lambda n: str(uuid.uuid5(NAMESPACE, n)))
    df["source_id"] = df["id"]

    def build_description(action, uses, effects):
        parts = []
        if pd.notna(action) and action:
            parts.append(f"Action: {action}.")
        if uses:
            parts.append(f"Uses: {', '.join(uses)}.")
        if effects:
            parts.append(f"Side effects: {', '.join(effects)}.")
        return " ".join(parts)

    df["full_description"] = [
        build_description(a, u, e)
        for a, u, e in zip(df["action_class"], df["uses"], df["side_effects"])
    ]

    # Комерційних даних у датасеті немає: генеруємо відтворювано (seed = 42).
    rng = np.random.default_rng(SEED)
    df["price"] = rng.uniform(50.0, 1500.0, len(df)).round(2)
    df["manufacturer"] = rng.choice(MANUFACTURERS, len(df))
    df["is_prescription"] = df["is_habit_forming"] | (rng.random(len(df)) < 0.5)

    columns = [
        "medicine_id", "source_id", "name", "chemical_class", "therapeutic_class",
        "action_class", "is_habit_forming", "is_prescription", "manufacturer",
        "substitutes", "uses", "side_effects", "full_description", "price",
    ]
    clean = df[columns].copy()
    for col in ("chemical_class", "action_class"):
        clean[col] = clean[col].astype(object).where(clean[col].notna(), None)
    clean["therapeutic_class"] = clean["therapeutic_class"].fillna(UNKNOWN_CLASS)
    return clean, audit(raw, clean)


def normalize_disease(use: str) -> str:
    """'treatment of bacterial infections' -> 'bacterial infections'.

    Прибираємо лише 'treatment of': у даних 'bacterial infections' зустрічається
    і з префіксом, і без, це одна й та сама хвороба. 'prevention of ...' лишається,
    бо профілактика та лікування - різні показання.
    """
    return re.sub(r"^treatment of (the )?", "", use).strip()


def entity_id(kind: str, name: str) -> str:
    """Детермінований UUID вузла: однакова назва -> однаковий id при кожному запуску."""
    return str(uuid.uuid5(NAMESPACE, f"{kind}:{name}"))


def build_graph_tables(clean: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Будує вузли (Disease, Symptom) і ребра для Neo4j з масивів препарату.

    severity не генерується: у датасеті немає джерела, а вигадані медичні дані
    шкідливі. Замість нього - обчислюване поле drug_count (кількість препаратів),
    яке рахується з ребер.
    """
    treats, causes, analogs = [], [], []
    known = set(clean["name"])
    id_by_name = dict(zip(clean["name"], clean["medicine_id"]))

    for mid, name, uses, effects, subs in zip(
        clean["medicine_id"], clean["name"], clean["uses"],
        clean["side_effects"], clean["substitutes"],
    ):
        for d in {normalize_disease(u) for u in uses}:
            treats.append((mid, entity_id("disease", d), d))
        for e in effects:
            causes.append((mid, entity_id("symptom", e), e))
        for sub in subs:
            if sub in known and sub != name:
                analogs.append((mid, id_by_name[sub]))

    treats = pd.DataFrame(treats, columns=["medicine_id", "disease_id", "disease_name"])
    causes = pd.DataFrame(causes, columns=["medicine_id", "symptom_id", "symptom_name"])
    analogs = pd.DataFrame(analogs, columns=["medicine_id", "substitute_id"])

    diseases = (treats.groupby(["disease_id", "disease_name"]).size()
                .reset_index(name="drug_count")
                .rename(columns={"disease_name": "name"}))
    symptoms = (causes.groupby(["symptom_id", "symptom_name"]).size()
                .reset_index(name="drug_count")
                .rename(columns={"symptom_name": "name"}))

    return {
        "diseases": diseases, "symptoms": symptoms,
        "treats": treats[["medicine_id", "disease_id"]],
        "causes": causes[["medicine_id", "symptom_id"]],
        "analogs": analogs,
    }


def normalize_query(raw: str) -> str:
    """Та сама логіка, що й QueryNormalizer: нижній регістр + відсортовані слова."""
    return " ".join(sorted(raw.lower().split()))


def generate_search_queries(clean: pd.DataFrame, graph: dict, n: int = 10_000,
                            seed: int = SEED) -> pd.DataFrame:
    """Генерує тестові пошукові запити.

    - словник береться з реальних даних (хвороби, побічні ефекти, назви);
    - вибір за Zipf-розподілом: кілька запитів дуже популярні -> з'являються
      влучання в кеш, як у реальних користувачів;
    - 20% запитів мають переставлені слова та змінений регістр
      (перевірка нормалізації кеш-ключа);
    - 10% містять неіснуюче слово (перевірка статусу «Пусто»).
    """
    rng = np.random.default_rng(seed)
    sample_size = min(2000, len(clean))
    pool = (graph["diseases"]["name"].tolist() + graph["symptoms"]["name"].tolist()
            + clean["name"].sample(sample_size, random_state=seed).tolist())
    ranks = rng.zipf(1.3, n)
    base = [pool[(r - 1) % len(pool)] for r in ranks]

    rows = []
    for text in base:
        raw = text
        if rng.random() < 0.20:
            words = raw.split()
            rng.shuffle(words)
            raw = " ".join(words).upper() if rng.random() < 0.5 else " ".join(words).title()
        if rng.random() < 0.10:
            raw = f"{raw} xqzvk{rng.integers(1000, 9999)}"
        rows.append((raw, normalize_query(raw)))
    return pd.DataFrame(rows, columns=["raw_query", "normalized_query"])


def save_prepared(clean: pd.DataFrame, graph: dict, queries: pd.DataFrame,
                  out_dir: str = "prepared") -> dict[str, int]:
    """Записує готові до завантаження файли; повертає кількість рядків у кожному."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    mongo_cols = [c for c in clean.columns if c != "full_description"]
    with open(out / "medicines.jsonl", "w", encoding="utf-8") as f:
        for rec in clean[mongo_cols].to_dict("records"):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with open(out / "search_docs.jsonl", "w", encoding="utf-8") as f:
        for rec in clean[["medicine_id", "name", "full_description"]].to_dict("records"):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    for name, table in graph.items():
        table.to_csv(out / f"{name}.csv", index=False)
    queries.to_csv(out / "search_queries.csv", index=False)

    counts = {"medicines.jsonl": len(clean), "search_docs.jsonl": len(clean),
              "search_queries.csv": len(queries)}
    counts.update({f"{name}.csv": len(table) for name, table in graph.items()})
    return counts


if __name__ == "__main__":
    cleaned_df, stats = process_medical_dataset("medicine_dataset.csv")
    print("=== Аудит ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

    graph = build_graph_tables(cleaned_df)
    print("\n=== Граф ===")
    for key, table in graph.items():
        print(f"{key}: {len(table)}")

    queries = generate_search_queries(cleaned_df, graph)
    print("\n=== Запити ===")
    print(queries.head())
    print("унікальних raw:", queries.raw_query.nunique(),
          "| унікальних normalized:", queries.normalized_query.nunique())

    print("\n=== Збережено ===")
    for fname, rows in save_prepared(cleaned_df, graph, queries).items():
        print(f"{fname}: {rows}")
