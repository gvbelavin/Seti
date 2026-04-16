# lesson6

Проксирование настроено так, что запросы на `80` порт идут в приложение в контейнере.

Контейнеры:
- `lesson6-db` (Postgres)
- `lesson6-api` (FastAPI + Selenium, работает внутри на `8010`)
- `lesson6-proxy` (Nginx, слушает `80` и проксирует в `lesson6-api:8010`)

## 1) Собрать образ приложения

```bash
docker build -t lesson6-app .
```

## 2) Создать сеть

```bash
docker network create lesson6-net
```

## 3) Запустить Postgres

```bash
docker run -d --name lesson6-db ^
  --network lesson6-net ^
  -e POSTGRES_DB=lesson6_db ^
  -e POSTGRES_USER=postgres ^
  -e POSTGRES_PASSWORD=postgres ^
  -p 56432:5432 ^
  postgres:16
```

## 4) Запустить API

```bash
docker run -d --name lesson6-api ^
  --network lesson6-net ^
  -e DATABASE_URL=postgresql+psycopg2://postgres:postgres@lesson6-db:5432/lesson6_db ^
  lesson6-app
```

## 5) Запустить Nginx-прокси на 80 порту

```bash
docker run -d --name lesson6-proxy ^
  --network lesson6-net ^
  -p 80:80 ^
  -v "C:\Users\ironm\seti\lesson6\nginx.conf:/etc/nginx/conf.d/default.conf:ro" ^
  nginx:alpine
```

## 6) Проверка (через 80 порт)

```bash
curl "http://127.0.0.1/"
curl "http://127.0.0.1/parse?url=http://quotes.toscrape.com"
curl "http://127.0.0.1/quotes?limit=5"
```

## Очистка

```bash
docker stop lesson6-proxy lesson6-api lesson6-db
docker rm lesson6-proxy lesson6-api lesson6-db
docker network rm lesson6-net
```
