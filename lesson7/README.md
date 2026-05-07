# lesson7

Здесь Nginx работает на хосте (вне Docker), а не в контейнере.

Схема:
- Docker контейнер БД: `lesson7-db`
- Docker контейнер API: `lesson7-api` (порт `8011`)
- Хостовый Nginx на `80` порту проксирует в `127.0.0.1:8011`
- Для RU IP/prefix на уровне Nginx срабатывает редирект на `/stub` с текстом `ВАМ СЮДА НЕЛЬЗЯ`

## 1) Собрать образ приложения

```bash
docker build -t lesson7-app .
```

## 2) Создать сеть Docker

```bash
docker network create lesson7-net
```

## 3) Запустить БД в Docker

```bash
docker run -d --name lesson7-db ^
  --network lesson7-net ^
  -e POSTGRES_DB=lesson7_db ^
  -e POSTGRES_USER=postgres ^
  -e POSTGRES_PASSWORD=postgres ^
  postgres:16
```

## 4) Запустить API в Docker (порт 8011 на хост)

```bash
docker run -d --name lesson7-api ^
  --network lesson7-net ^
  -e DATABASE_URL=postgresql+psycopg2://postgres:postgres@lesson7-db:5432/lesson7_db ^
  -p 8011:8010 ^
  lesson7-app
```

Если контейнер уже создан неудачно:

```bash
docker rm -f lesson7-api
```

## 5) Настроить хостовый Nginx

Скопируйте `nginx/lesson7.conf` в конфиги Nginx:
- Linux: `/etc/nginx/conf.d/lesson7.conf`
- Windows (пример): `C:\nginx\conf\conf.d\lesson7.conf`

Проверьте конфиг и перезапустите Nginx:

```bash
nginx -t
nginx -s reload
```

## 6) Проверка

```bash
curl "http://127.0.0.1/"
curl "http://127.0.0.1/parse?url=http://quotes.toscrape.com"
curl "http://127.0.0.1/quotes?limit=5"
curl "http://127.0.0.1/stub"
```

Если IP клиента попадает в RU prefix список в `lesson7.conf`, любой путь будет редиректить на `/stub`.

## Очистка Docker

```bash
docker stop lesson7-api lesson7-db
docker rm lesson7-api lesson7-db
docker network rm lesson7-net
```
