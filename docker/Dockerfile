# Образ із кодом проєкту. Той самий образ далі використають api, generator та ingest_worker,
# різниця лише в команді запуску (CMD / command у compose).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Спершу залежності: цей шар кешується, поки requirements.txt не змінився.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY workers ./workers
COPY config.yaml .
COPY docker/smoke_check.py ./smoke_check.py

# Контрольний запуск (крок 6). Для API: uvicorn app.main:create_app --factory
CMD ["python", "smoke_check.py"]
