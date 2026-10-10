# Medicine Polyglot High-Load

Курсова робота з дисципліни «Бази даних та інформаційні системи».
Тема: проєктування та розробка розподіленої високонавантаженої системи збору,
збереження, повнотекстового пошуку та моніторингу інформації.
Варіант №17: «Медичні симптоми та Ліки».

КПІ ім. Ігоря Сікорського, ФПМ, група КМ-42.
Автори: Запорожець А. А., Коваль Д. С., Бойко Д. А., Хайло А. Р.

## Про проєкт

Довідник лікарських препаратів (датасет Kaggle, 222 825 препаратів після очищення) з
повнотекстовим пошуком за інструкціями, фільтрацією, пошуком аналогів і панеллю моніторингу.
Дані зберігаються в поліглотному сховищі, кожна БД обслуговує свій тип запитів:

| Сховище | Що зберігає | Для яких запитів |
|---|---|---|
| MongoDB (3 шарди) | картки препаратів, журнал пошуку | картка за id, фільтрація, агрегація |
| Elasticsearch | `full_description` (показання, побічні ефекти, механізм дії) | повнотекстовий пошук |
| Neo4j | вузли Medicine, Disease, Symptom і ребра між ними | аналоги, «аналог без побічного ефекту X» |
| Redis | результати пошуку, ключ `config:rate` | кеш, керування швидкістю генератора |

Між генератором і записом у БД стоїть черга RabbitMQ.
Стек: Python 3.11+, asyncio, FastAPI, Pydantic, Docker.

**Поточний стан (10.10.2026).** Архітектура, класи й контракти готові. Тіла методів поки
`NotImplementedError`. Реалізовано: підготовку датасету, автоматичні тести архітектури,
генератор схем із коду та Docker-стенд (власний образ + MongoDB).

## Архітектура

Шарова + гексагональна архітектура (порти й адаптери) + CQRS. Три незалежні процеси:
**API** (читання), **generator** (публікує пакети в чергу), **ingest_worker** (пише з черги в БД).

```
presentation ──> application ──> domain <── infrastructure
   (REST, SSE)     (вхідні порти,   (сутності,   (адаптери БД,
                    обробники,       служби,      черга, логування)
                    DTO)             вихідні порти)
                                        ^
workers ── через порти ─────────────────┘      infrastructure/config/container.py
                                               збирає все разом
```

Правило: залежності спрямовані до домену, домен не імпортує нічого. Правило перевіряють
тести та скрипт `tools/arch_diagrams.py --check`.

Схеми згенеровано з коду (дата стоїть на кожній), каталог `docs/diagrams/`:

| Файл | Що показує | У звіті |
|---|---|---|
| `01_modules.png` | залежності між модулями | рис. 3.8 |
| `02_domain_model.png` | доменна модель | — |
| `03_ports_inbound.png`, `04_ports_outbound.png` | вхідні та вихідні порти | — |
| `05_search_slice.png` | зріз «Пошук препаратів» | рис. 3.4 |
| `06_ingest_slice.png` | зріз «Запис документів» | рис. 3.7 |
| `07_card_slice.png` | зріз «Картка препарату» (ланцюжок п. 4) | рис. 3.5 |

### Ланцюжок Controller → Facade → Service → Repository

| Роль | Приклад із завдання | У проєкті |
|---|---|---|
| Контролер | `MovieController` | `MedicineController`, `SearchController`, `AnaloguesController`, `RateController` |
| Фасад | `MovieFacade` | вхідні порти `ListMedicines`, `GetMedicineCard`, `CreateMedicine`, `UpdateMedicine`, `DeleteMedicine`… |
| Сервіси | `MovieInformationService`, `MoviePictureService` | обробники `*Handler` + доменні служби `QueryNormalizer`, `DocumentValidator`, `ShardKeyService` |
| Репозиторії | `MovieInformationRepository`, `MoviePictureRepository` | `DocumentRepository` (CRUD), `GraphRepository`, `SearchIndex`, `CacheStore`: окремий для кожного сховища |
| Реалізації | — | `MongoDocumentAdapter`, `Neo4jGraphAdapter`, `SearchIndexAdapter`, `RedisCacheAdapter` |

Окремого класу-фасаду немає: його роль виконують вхідні порти (детальніше: звіт, п. 3.6.2).

### Цифри (з `docs/diagrams/summary.json`)

61 модуль, 78 класів: 6 сутностей, 3 доменні служби, 10 вхідних і 6 вихідних портів,
10 обробників, 16 DTO, 6 адаптерів, 5 контролерів, 2 процеси; 17 реалізацій портів;
порушень правила залежностей і циклів немає.

## Структура репозиторію

```
app/
  domain/           сутності, доменні служби, вихідні порти, винятки
  application/      вхідні порти, commands/ і queries/ (CQRS), DTO, mappers.py
  infrastructure/   адаптери persistence/, messaging/, observability/; config/ = Container
  presentation/     rest/ (контролери), stream/ (SSE)
  main.py           точка входу API
workers/            generator.py, ingest_worker.py: окремі процеси
scripts/            process_dataset.py: підготовка датасету (Додаток А звіту)
tools/              arch_diagrams.py: схеми з коду + перевірка архітектури
tests/unit/         автоматичні тести архітектури (18)
docker/             Dockerfile, docker-compose.smoke.yml, smoke_check.py
docs/diagrams/      згенеровані схеми
prepared/           підготовлені файли для БД (не в git)
```

## Як запустити й перевірити

Потрібно: **Git**, **Docker Desktop** (на Windows працює через WSL 2), за бажанням **Python 3.11+**.
Усі команди виконуються в корені проєкту.

```
git clone https://github.com/ArtemHaylo/BD_coursework_medicine.git
cd BD_coursework_medicine
```

### 1. Docker-стенд: власний образ + MongoDB (п. 6 завдання)

Контейнер `app` (образ `medicine-app:0.1` з кодом проєкту) підключається до контейнера `mongo`,
записує препарат, читає його назад і порівнює. Логи пишуться в консоль і у файл `logs/smoke.log`
на вашому комп'ютері (bind mount), тому лишаються після видалення контейнерів.

```
docker compose -f docker/docker-compose.smoke.yml up --build --attach app --exit-code-from app
```

- `--build` збирає образ (перший раз кілька хвилин, далі можна без цього прапорця);
- `--attach app` показує лише логи нашого контейнера (MongoDB пише багато службових рядків);
- `--exit-code-from app` зупиняє все, коли `app` завершився, і повертає його код виходу.

Очікуваний вивід:

```
smoke-app  | ... | INFO    | MongoDB відповідає (спроба 1, uri=mongodb://mongo:27017)
smoke-app  | ... | INFO    | ЗАПИС: id=... name='smoke-test medicine'
smoke-app  | ... | INFO    | ЧИТАННЯ: id=... name='smoke-test medicine' price=100.0
smoke-app  | ... | INFO    | ПОРІВНЯННЯ: записане і прочитане збігаються
smoke-app  | ... | INFO    | У колекції smoke.checks тепер 1 запис(ів)
smoke-app exited with code 0
```

Перевірити, що логи пережили видалення контейнерів:

```
docker compose -f docker/docker-compose.smoke.yml down
Get-Content logs\smoke.log -Encoding UTF8      # Windows PowerShell
cat logs/smoke.log                             # Linux / macOS / Git Bash
```

Без `-Encoding UTF8` старий PowerShell показує кирилицю «кракозябрами»: файл при цьому правильний.
Час у логах за UTC. Під час повторного запуску лічильник записів зростає (2, 3, …): дані MongoDB
лежать в іменованому томі `mongo_data`. Прибрати все разом із даними:

```
docker compose -f docker/docker-compose.smoke.yml down -v
```

### 2. Тести

Варіант без встановлення Python, у тому самому образі (код проєкту монтується в контейнер):

```
docker run --rm -v "${PWD}:/app" medicine-app:0.1 python -m pytest tests/unit -q
```

`${PWD}` працює в PowerShell і bash; у `cmd` замініть на `%cd%`.

Варіант з локальним Python:

```
python -m venv .venv
.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/unit -q
```

Очікуваний результат: `18 passed`. Тести не потребують запущених БД.

| Тест | Що гарантує |
|---|---|
| `test_domain.py` | домен не імпортує жодного зовнішнього шару; сутності й порти коректні |
| `test_application.py` | `application` не імпортує `infrastructure`, `presentation`, `workers`; кожен обробник реалізує вхідний порт |
| `test_infrastructure.py` | кожен адаптер реалізує всі методи свого порту; адаптери не імпортують `application` і `presentation` |
| `test_presentation.py` | усі REST-маршрути зареєстровані; контролери не імпортують `infrastructure` |
| `test_workers.py` | воркери створюються з портів і не залежать від конкретних адаптерів |
| `test_diagrams.py` | немає порушень шарів і циклів; кожен порт має реалізацію; схеми будуються з коду з датою |

### 3. Схеми архітектури з коду

```
python tools/arch_diagrams.py --check                          # лише перевірка, код 1 при порушеннях
python tools/arch_diagrams.py --out docs/diagrams --date 10.10.2026
```

Потрібен лише Python; для PNG/SVG ще Graphviz (`dot`), без нього створюються `.dot` і `summary.json`.

### 4. Підготовка датасету

Датасет «250k Medicines Usage, Side Effects and Substitutes» (Kaggle) у git не зберігається.
Покладіть `medicine_dataset.csv` у корінь проєкту і запустіть:

```
python scripts/process_dataset.py
```

Скрипт виводить аудит (цифри розділу 2.1.1 звіту) і створює в `prepared/` файли для кожного
сховища: `medicines.jsonl`, `search_docs.jsonl`, `diseases.csv`, `symptoms.csv`, `treats.csv`,
`causes.csv`, `analogs.csv`, `search_queries.csv`. Генерація відсутніх полів відтворювана (`seed = 42`).

## Контейнеризація

Docker + Docker Compose дають однакове середовище для всієї команди і дозволяють підняти
шардований кластер MongoDB разом з іншими БД на одному комп'ютері. Обґрунтування, схема
розгортання і результати стенда наведено в звіті, п. 3.10. Цільовий склад кластера:
`api`, `generator`, `ingest-worker` (один образ `medicine-app`), `mongos`, `configsvr`,
`shard1–3`, `elasticsearch`, `neo4j`, `redis`, `rabbitmq`. Кожна БД має іменований том, а логи
застосунку пишуться в `./logs`. Повний `docker-compose.yml` з'явиться разом із реалізацією адаптерів.

## Статус

- [x] Скелет каталогів і класи всіх шарів (domain, application, infrastructure, presentation, workers)
- [x] Підготовка датасету
- [x] Автоматичні тести архітектури та генератор схем з датою
- [x] Docker: власний образ і стенд app + MongoDB (запис, читання, логи на хості)
- [ ] Реалізація адаптерів і обробників
- [ ] Повний `docker-compose.yml` (3 шарди MongoDB, Elasticsearch, Neo4j, Redis, RabbitMQ)
- [ ] Веб-інтерфейс і генератор з керуванням швидкістю
- [ ] Навантажувальне тестування
- [ ] Фінальна схема взаємодії елементів
