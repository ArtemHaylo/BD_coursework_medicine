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
з'єднання з БД не відкриваються. Очікуваний результат: `18 passed`.

Шість файлів тестів стежать за архітектурою автоматично:

| Тест | Що гарантує |
|---|---|
| `test_domain.py` | домен не імпортує жодного зовнішнього шару; сутності мають коректні значення за замовчуванням; порти абстрактні |
| `test_application.py` | `application` не імпортує `infrastructure`, `presentation`, `workers`; кожен обробник реалізує вхідний порт |
| `test_infrastructure.py` | кожен адаптер реалізує всі методи свого вихідного порту (інакше `TypeError` при створенні); адаптери не імпортують `application` і `presentation` |
| `test_presentation.py` | усі очікувані REST-маршрути зареєстровані; контролери не імпортують `infrastructure` |
| `test_workers.py` | воркери створюються з портів і не імпортують конкретні адаптери |
| `test_diagrams.py` | правило шарів виконується в усьому коді, між пакетами немає циклів, кожен порт має реалізацію, кожен вхідний порт має рівно один обробник; схеми будуються з поточного коду |

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
| `app/infrastructure` | адаптери БД, черги, логування, `settings.py` | `domain` |
| `app/infrastructure/config` | композиційний корінь (`Container`) | усі шари |
| `app/presentation` | REST-контролери, SSE | `application` (і доменні винятки) |
| `app/main.py` | точка входу API-процесу | усі шари |
| `workers` | окремі процеси: generator, ingest_worker | порти `domain` і `application`; `Container` лише в `main()` |
| `tests/unit` | модульні тести | |
| `tools` | генератор схем архітектури з коду | лише стандартна бібліотека |
| `docs/diagrams` | згенеровані схеми (DOT, PNG, SVG) і `summary.json` | |
| `tests/integration` | інтеграційні тести з реальними БД (на наступних етапах) | |
| `scripts` | підготовка датасету (Додаток А звіту) | |
| `prepared` | підготовлені файли для завантаження (не в git) | |

## Розміщення портів

Вихідні порти (`app/domain/ports/outbound/`) оголошені в доменному шарі:
без цього неможлива інверсія залежності від сховищ. Їх шість: `DocumentRepository`,
`SearchIndex`, `GraphRepository`, `CacheStore`, `MetricsSink`, `QueuePublisher`.

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
| Domain, порти | `DocumentRepository`, `SearchIndex`, `GraphRepository`, `CacheStore`, `MetricsSink`, `QueuePublisher` | контракти до сховищ |
| Application, команди | `IngestDocumentHandler`, `ConfigureRateHandler`, `CreateMedicineHandler`, `UpdateMedicineHandler`, `DeleteMedicineHandler` | шлях запису |
| Application, запити | `SearchMedicinesHandler`, `GetMedicineCardHandler`, `GetAnaloguesHandler`, `ListMedicinesHandler`, `GetStatsHandler` | шлях читання |
| Application, DTO | `SearchQuery`, `SearchResult`, `MedicineCard`, `MedicineCreateDto`, `MedicineUpdateDto`, `AnalogueDto`, `IngestBatchDto`, `RateConfigDto`, `StatsDto` та ін. (16) | межові об'єкти передачі даних |
| Infrastructure | `MongoDocumentAdapter`, `SearchIndexAdapter`, `Neo4jGraphAdapter`, `RedisCacheAdapter`, `MongoMetricsAdapter`, `QueueAdapter` | реалізації портів |
| Infrastructure, config | `Container`, `Settings` | композиційний корінь, налаштування |
| Presentation | `SearchController`, `MedicineController`, `AnaloguesController`, `RateController`, `StatsStreamController` | REST і SSE |
| Workers | `LoadGenerator`, `IngestWorker` | окремі процеси |

Стан на 10.10.2026: 60 модулів, 78 класів, 10 вхідних і 6 вихідних портів,
10 обробників, 17 реалізацій портів, 18 автоматичних тестів.

## Застосовані патерни

| Патерн | Де | Навіщо |
|---|---|---|
| Порти й адаптери | `domain/ports`, `application/ports`, `infrastructure` | заміна сховища без дотику до логіки |
| CRUD-репозиторій | `DocumentRepository` | єдиний контракт створення, читання, оновлення, видалення |
| CQRS | `application/commands`, `application/queries` | різні шляхи й моделі для запису та читання |
| DTO | `application/dto` | межові об'єкти, що не тягнуть доменні сутності |
| Відображення | `application/mappers.py` | перетворення Domain ↔ DTO в одному місці |
| Доменна служба | `domain/services` | правила, що не належать жодній сутності |
| Об'єкт-значення | `ShardKey` | незмінний складений ключ шардінгу |
| Композиційний корінь | `infrastructure/config/container.py` | єдине місце, що знає конкретні реалізації |
| Протокол (структурна типізація) | `BatchSource` у `workers/ingest_worker.py` | воркер не залежить від конкретного адаптера черги |
| Черга повідомлень | `QueueAdapter` | розв'язує різницю швидкостей генератора й запису |

## Схеми

```
python tools/arch_diagrams.py --out docs/diagrams --date 10.10.2026
python tools/arch_diagrams.py --check
```

Скрипт будує схеми безпосередньо з вихідного коду й ставить на кожній дату
(без `--date` бере сьогоднішню). PNG і SVG створюються, якщо встановлено
Graphviz (команда `dot`); без нього лишаються лише `.dot`. Параметр `--check`
нічого не малює, а перевіряє правило залежностей, цикли між пакетами та
контракти портів і завершується з кодом 1 при порушеннях.

| Файл | Вміст |
|---|---|
| `docs/diagrams/01_modules` | взаємодія модулів; порушення правила шарів позначаються червоним |
| `docs/diagrams/02_domain_model` | сутності, доменні служби, об'єкт-значення, винятки |
| `docs/diagrams/03_ports_inbound` | контролери, вхідні порти, обробники |
| `docs/diagrams/04_ports_outbound` | вихідні порти й адаптери |
| `docs/diagrams/05_search_slice` | зріз «Пошук препаратів» (шлях запитів) |
| `docs/diagrams/06_ingest_slice` | зріз «Запис документів» (шлях команд) |
| `docs/diagrams/summary.json` | кількісна зведенка та результати перевірок |

Після завершення проєкту схеми перегенеровують однією командою для
фінальної редакції звіту.

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
- [x] Схеми архітектури та перевірка залежностей (10.10.2026)
- [ ] Реалізація адаптерів і обробників
- [ ] Docker Compose (кластер БД)
- [ ] Навантажувальне тестування
