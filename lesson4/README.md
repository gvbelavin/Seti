# lesson4

Простой API-парсер на Selenium + Postgres.

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
docker compose up -d
uvicorn app.main:app --reload
```

Postgres в этом проекте на порту `55432` (чтобы не конфликтовать с локальными Postgres-сервисами).

## Запросы

Запустить парсер:

```bash
curl "http://127.0.0.1:8000/parse?url=http://quotes.toscrape.com"
```

Получить данные из БД:

```bash
curl "http://127.0.0.1:8000/quotes?limit=20"
```

История запусков:

```bash
curl "http://127.0.0.1:8000/runs?limit=10"
```

