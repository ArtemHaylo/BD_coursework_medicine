"""Контрольний запуск контейнеризації (крок 6).

Скрипт працює всередині контейнера `app` і перевіряє зв'язок із контейнером `mongo`:
1) чекає, поки MongoDB прийме з'єднання;
2) записує документ (сутність Medicine з коду проєкту);
3) читає його назад і порівнює з записаним;
4) рахує, скільки записів уже є в базі (зростає між запусками, поки живе том mongo_data).

Усе, що відбувається, пишеться і в консоль (docker logs), і у файл на хості
(каталог ./logs монтується в контейнер), тож логи переживають видалення контейнера.

Код виходу: 0 - запис і читання збігаються, 1 - помилка.
"""
from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.domain.entities.medicine import Medicine

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
LOG_PATH = Path(os.getenv("LOG_PATH", "/app/logs/smoke.log"))
DB_NAME = "smoke"
COLLECTION = "checks"
CONNECT_ATTEMPTS = 30


def setup_logging() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
    logger = logging.getLogger("smoke")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    for handler in (logging.StreamHandler(sys.stdout),
                    logging.FileHandler(LOG_PATH, encoding="utf-8")):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


def wait_for_mongo(client: MongoClient, log: logging.Logger) -> None:
    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        try:
            client.admin.command("ping")
            log.info("MongoDB відповідає (спроба %d, uri=%s)", attempt, MONGO_URI)
            return
        except PyMongoError as exc:
            log.warning("MongoDB ще не готова (спроба %d/%d): %s",
                        attempt, CONNECT_ATTEMPTS, type(exc).__name__)
            time.sleep(1)
    raise RuntimeError("MongoDB не відповіла за відведений час")


def build_medicine() -> Medicine:
    """Тестовий препарат: показує, що в образі є код проєкту (app.domain)."""
    return Medicine(
        medicine_id=uuid.uuid4(), source_id=0, name="smoke-test medicine",
        therapeutic_class="unknown", is_habit_forming=False, is_prescription=False,
        manufacturer="Aurelia Pharma", price=100.0,
        uses=["bacterial infections"], side_effects=["nausea"],
    )


def main() -> int:
    log = setup_logging()
    log.info("Старт контрольного запуску, лог-файл: %s", LOG_PATH)
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    try:
        wait_for_mongo(client, log)
        collection = client[DB_NAME][COLLECTION]

        medicine = build_medicine()
        document = asdict(medicine)
        document["_id"] = str(medicine.medicine_id)
        document["medicine_id"] = str(medicine.medicine_id)
        document["written_at"] = datetime.now(timezone.utc).isoformat()

        collection.insert_one(document)
        log.info("ЗАПИС: id=%s name=%r", document["_id"], document["name"])

        stored = collection.find_one({"_id": document["_id"]})
        if stored is None:
            log.error("ЧИТАННЯ: документ %s не знайдено", document["_id"])
            return 1
        log.info("ЧИТАННЯ: id=%s name=%r price=%s", stored["_id"], stored["name"], stored["price"])

        if stored != document:
            log.error("ПОРІВНЯННЯ: записане і прочитане відрізняються")
            return 1
        log.info("ПОРІВНЯННЯ: записане і прочитане збігаються")

        total = collection.count_documents({})
        log.info("У колекції %s.%s тепер %d запис(ів)", DB_NAME, COLLECTION, total)
        return 0
    except (PyMongoError, RuntimeError) as exc:
        log.error("ПОМИЛКА: %s: %s", type(exc).__name__, exc)
        return 1
    finally:
        client.close()
        log.info("Завершено")


if __name__ == "__main__":
    sys.exit(main())
