# lesson5

2 контейнера без `docker-compose`:
- контейнер приложения (FastAPI + Selenium) на порту `8010`
- контейнер Postgres

## 1) Собрать образ приложения

```bash
docker build -t lesson5-app .
```

## 2) Создать сеть

```bash
docker network create lesson5-net
```

## 3) Запустить контейнер БД

```bash
docker run -d --name lesson5-db ^
  --network lesson5-net ^
  -e POSTGRES_DB=lesson5_db ^
  -e POSTGRES_USER=postgres ^
  -e POSTGRES_PASSWORD=postgres ^
  -p 55432:5432 ^
  postgres:16
```

## 4) Запустить контейнер приложения

```bash
docker run -d --name lesson5-api ^
  --network lesson5-net ^
  -e DATABASE_URL=postgresql+psycopg2://postgres:postgres@lesson5-db:5432/lesson5_db ^
  -p 8010:8010 ^
  lesson5-app
```

## 5) Проверка

```bash
curl "http://127.0.0.1:8010/"
curl "http://127.0.0.1:8010/parse?url=http://quotes.toscrape.com"
curl "http://127.0.0.1:8010/quotes?limit=5"
```

## Полезные команды

```bash
docker logs -f lesson5-api
docker logs -f lesson5-db
docker stop lesson5-api lesson5-db
docker rm lesson5-api lesson5-db
docker network rm lesson5-net
```
