# Medicine Polyglot High-Load

Курсова робота з дисципліни «Бази даних та інформаційні системи».
Тема: проєктування та розробка розподіленої високонавантаженої системи збору,
збереження, повнотекстового пошуку та моніторингу інформації.
Варіант №17: «Медичні симптоми та Ліки».

КПІ ім. Ігоря Сікорського, ФПМ, група КМ-42.
Автори: Запорожець А. А., Коваль Д. С., Бойко Д. А., Хайло А. Р.

## Скелет застосунку

Класи за архітектурою розділу 3 звіту: шари, порти й адаптери, CQRS.
Тіла методів поки оголошені як `NotImplementedError`: фіксуються структура
та контракти. Реалізація (адаптери баз даних, обробники, генератор) буде
додана на наступних етапах. Запуск у контейнерах (Docker Compose) теж
буде на одному з наступних етапів.

Поліглотне сховище: MongoDB (3 шарди), Elasticsearch, Neo4j, Redis.
Черга повідомлень: RabbitMQ. Стек: Python 3.11+, asyncio, FastAPI, Pydantic.

## Перевірка

Усі команди виконуються в корені проєкту.

```
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests/unit -q
```

Тести проходять без піднятих баз даних: адаптери в них лише створюються,
з'єднання з БД не відкриваються. Очікуваний результат: `15 passed`.

П'ять файлів тестів стежать за архітектурою автоматично:

| Тест | Що гарантує |
|---|---|
| `test_domain.py` | домен не імпортує жодного зовнішнього шару; сутності мають коректні значення за замовчуванням; порти абстрактні |
| `test_application.py` | `application` не імпортує `infrastructure`, `presentation`, `workers`; кожен обробник реалізує вхідний порт |
| `test_infrastructure.py` | кожен адаптер реалізує всі методи свого вихідного порту (інакше `TypeError` при створенні); адаптери не імпортують `application` і `presentation` |
| `test_presentation.py` | усі очікувані REST-маршрути зареєстровані; контролери не імпортують `infrastructure` |
| `test_workers.py` | воркери створюються з портів і не імпортують конкретні адаптери |

## Схема шарів

```
presentation ──> application ──> domain <── infrastructure
   (REST, SSE)     (порти in,      (сутності,   (адаптери БД,
                    обробники,      сервіси,     черга, логування)
                    DTO)            порти out)
                                        ^
workers ── через порти ─────────────────┘      config/container.py
                                               збирає все разом
```

Правило: залежності спрямовані до домену. Домен не імпортує нічого.

## Розкладка

| Каталог | Шар | Залежить від |
|---|---|---|
| `app/domain` | предметна область | нічого |
| `app/application` | сценарії, вхідні порти, DTO | `domain` |
| `app/infrastructure` | адаптери БД, черги, логування | `domain` |
| `app/infrastructure/config` | композиційний корінь, налаштування | усі шари |
| `app/presentation` | REST-контролери, SSE | `application` (і доменні винятки) |
| `app/main.py` | точка входу API-процесу | усі шари |
| `workers` | окремі процеси: generator, ingest_worker | порти `domain` і `application`; `Container` лише в `main()` |
| `tests/unit` | модульні тести | |
| `tests/integration` | інтеграційні тести з реальними БД (на наступних етапах) | |
| `scripts` | підготовка датасету (Додаток А звіту) | |
| `prepared` | підготовлені файли для завантаження (не в git) | |

## Розміщення портів

Вихідні порти (`app/domain/ports/outbound/`) оголошені в доменному шарі:
без цього неможлива інверсія залежності від сховищ. Їх вісім: `DocumentRepository`,
`SearchIndex`, `GraphRepository`, `CacheStore`, `MetricsSink`, `QueuePublisher`,
`DiseaseRepository`, `SymptomRepository`.

CRUD-репозиторії: `DocumentRepository` (препарати, MongoDB), `DiseaseRepository` і
`SymptomRepository` (довідники, вузли Neo4j). Для довідників CRUD охоплює лише самі
вузли; ребра `ЛІКУЄ` та `ВИКЛИКАЄ` створює `GraphRepository.upsert_many`, а лічильник
`drug_count` обчислюється з ребер і напряму не редагується.

Вхідні порти (`app/application/ports/inbound/`) оголошені в шарі сценаріїв,
бо їхній контракт оперує DTO, а не доменними сутностями. Їх десять:
`SearchMedicines`, `GetMedicineCard`, `GetAnalogues`, `ListMedicines`,
`IngestDocument`, `ConfigureRate`, `GetStats`, `CreateMedicine`,
`UpdateMedicine`, `DeleteMedicine`.

Назви обробників (`SearchMedicinesHandler` тощо) збережено з розділу 3 звіту;
це application-сервіси.

## Класи за шарами

| Шар | Класи | Роль |
|---|---|---|
| Domain, сутності | `Medicine`, `Disease`, `Symptom`, `SearchLogEntry`, `SearchDocument`, `SearchHit` | предметна модель |
| Domain, служби | `QueryNormalizer`, `DocumentValidator`, `ShardKeyService`, `ShardKey` | правила, що не належать жодній сутності |
| Domain, порти | `DocumentRepository`, `SearchIndex`, `GraphRepository`, `CacheStore`, `MetricsSink`, `QueuePublisher`, `DiseaseRepository`, `SymptomRepository` | контракти до сховищ |
| Application, команди | `IngestDocumentHandler`, `ConfigureRateHandler`, `CreateMedicineHandler`, `UpdateMedicineHandler`, `DeleteMedicineHandler` | шлях запису |
| Application, запити | `SearchMedicinesHandler`, `GetMedicineCardHandler`, `GetAnaloguesHandler`, `ListMedicinesHandler`, `GetStatsHandler` | шлях читання |
| Application, DTO | `SearchQuery`, `SearchResult`, `MedicineCard`, `MedicineCreateDto`, `MedicineUpdateDto`, `AnalogueDto`, `IngestBatchDto`, `RateConfigDto`, `StatsDto` та ін. (16) | межові об'єкти передачі даних |
| Infrastructure | `MongoDocumentAdapter`, `SearchIndexAdapter`, `Neo4jGraphAdapter`, `Neo4jDiseaseAdapter`, `Neo4jSymptomAdapter`, `RedisCacheAdapter`, `MongoMetricsAdapter`, `QueueAdapter` | реалізації портів |
| Infrastructure, config | `Container`, `Settings` | композиційний корінь, налаштування |
| Presentation | `SearchController`, `MedicineController`, `AnaloguesController`, `RateController`, `StatsStreamController` | REST і SSE |
| Workers | `LoadGenerator`, `IngestWorker` | окремі процеси |

Стан на 10.10.2026: 63 модулі, 82 класи, 10 вхідних і 8 вихідних портів,
10 обробників, 15 автоматичних тестів.

## Відповідність назв: звіт і код

| У звіті | У коді | Примітка |
|---|---|---|
| «Препарат» | `Medicine` (domain); `MedicineCard`, `MedicineCreateDto`, `MedicineUpdateDto` (DTO) | колекція `medicines` у MongoDB, вузол `:Medicine` у Neo4j |
| «Хвороба» | `Disease` | лише вузол `:Disease` у Neo4j |
| «Симптом / Побічний ефект» | `Symptom` | лише вузол `:Symptom` у Neo4j |
| «Пошуковий запит» (табл. 2.4) | `SearchLogEntry` | запис журналу, колекція `search_log` у MongoDB |
| вхідний запит користувача | `SearchQuery` (DTO) | не сутність і не зберігається |
| результат пошуку | `SearchResult`, `SearchItem` (DTO) | відповідь API |
| «Аналог» | ребро `МАЄ_АНАЛОГ`; `AnalogueDto` | окремої сутності немає: самозв'язок «багато до багатьох» |

## Схеми архітектури

Схеми зв'язків між модулями та класами генеруються з коду (не малюються вручну):

```
python scripts/architecture_diagrams.py
```

Потрібен Graphviz (`dot`). Результат і огляд архітектури (станом на 10.10.2026):
[`docs/architecture/`](docs/architecture/README.md). Для звіту підготовлено розділ
3.11 у `docs/architecture/report_section_3_11.docx`.

## Застосовані патерни

| Патерн | Де | Навіщо |
|---|---|---|
| Порти й адаптери | `domain/ports`, `application/ports`, `infrastructure` | заміна сховища без дотику до логіки |
| CRUD-репозиторій | `DocumentRepository`, `DiseaseRepository`, `SymptomRepository` | єдиний контракт створення, читання, оновлення, видалення |
| CQRS | `application/commands`, `application/queries` | різні шляхи й моделі для запису та читання |
| DTO | `application/dto` | межові об'єкти, що не тягнуть доменні сутності |
| Відображення | `application/mappers.py` | перетворення Domain ↔ DTO в одному місці |
| Доменна служба | `domain/services` | правила, що не належать жодній сутності |
| Об'єкт-значення | `ShardKey` | незмінний складений ключ шардінгу |
| Композиційний корінь | `infrastructure/config/container.py` | єдине місце, що знає конкретні реалізації |
| Протокол (структурна типізація) | `BatchSource` у `workers/ingest_worker.py` | воркер не залежить від конкретного адаптера черги |
| Черга повідомлень | `QueueAdapter` | розв'язує різницю швидкостей генератора й запису |

## Підготовка даних

Датасет «250k Medicines Usage, Side Effects and Substitutes» (Kaggle) у
репозиторій не комітиться (див. `.gitignore`). Файл `medicine_dataset.csv`
кладуть у корінь проєкту, після чого запускають скрипт підготовки
(Додаток А звіту):

```
python scripts/process_dataset.py
```

Скрипт виводить аудит датасету (цифри розділу 2.1.1) і створює в `prepared/`
файли для кожного сховища (табл. 2.8): `medicines.jsonl`, `search_docs.jsonl`,
`diseases.csv`, `symptoms.csv`, `treats.csv`, `causes.csv`, `analogs.csv`,
`search_queries.csv`. Генерація відсутніх полів відтворювана (`seed = 42`).

## Статус

- [x] Скелет каталогів
- [x] Domain
- [x] Application
- [x] Infrastructure
- [x] Presentation
- [x] Workers
- [ ] Реалізація адаптерів і обробників
- [ ] Docker Compose (кластер БД)
- [ ] Навантажувальне тестування
