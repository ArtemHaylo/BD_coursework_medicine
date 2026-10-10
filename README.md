# Medicine Polyglot High-Load

Курсова робота з дисципліни «Бази даних та інформаційні системи».
Тема: проєктування та розробка розподіленої високонавантаженої системи збору,
збереження, повнотекстового пошуку та моніторингу інформації.
Варіант №17: «Медичні симптоми та Ліки».

**КПІ ім. Ігоря Сікорського, ФПМ, група КМ-42**

Автори: Запорожець А. А., Коваль Д. С., Бойко Д. А., Хайло А. Р.

## Архітектура
Шарова + гексагональна (порти й адаптери) + CQRS.
Поліглотне сховище: MongoDB (3 шарди), Elasticsearch, Neo4j, Redis. Черга: RabbitMQ.

## Структура
```
app/
  domain/          сутності, доменні сервіси, вихідні порти
  application/     вхідні порти, обробники (commands/queries), DTO
  infrastructure/  адаптери БД, черга, логування, композиційний корінь
  presentation/    REST-контролери, SSE
workers/           generator.py, ingest_worker.py
tests/             unit та integration
prepared/          підготовлені файли (не в git)
```

Правило залежностей: `domain` нічого не імпортує з інших шарів.

## Запуск
```
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Статус
- [x] Скелет каталогів
- [x] Domain
- [x] Application
- [x] Infrastructure
- [x] Presentation
- [x] Workers
