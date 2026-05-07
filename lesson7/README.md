# lesson7

FastAPI + Postgres + Nginx (редирект RU IP на заглушку).

## Запуск

```bash
docker compose up -d --build
```

## Проверка

```bash
curl "http://127.0.0.1/"
curl "http://127.0.0.1/parse?url=http://quotes.toscrape.com"
curl "http://127.0.0.1/quotes?limit=5"
curl "http://127.0.0.1/stub"
```

## Важно

- Правило RU IP находится в `nginx/lesson7.conf`.
- Локально (`127.0.0.1`) редирект на заглушку может не срабатывать, потому что Nginx видит IP шлюза Docker, а не ваш внешний IP.

## Остановка

```bash
docker compose down
```
