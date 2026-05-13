# lesson7

FastAPI + Postgres в Docker, Nginx на хосте (вне Docker).

## Запуск

```bash
docker compose up -d --build
```

Приложение слушает только локальный интерфейс хоста: `127.0.0.1:8010`.

## Nginx (на хосте)

Скопируйте `nginx/lesson7.conf`:
- Linux: `/etc/nginx/conf.d/lesson7.conf`
- Windows (пример): `C:\nginx\conf\conf.d\lesson7.conf`

Примените:

```bash
nginx -t
nginx -s reload
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
- Nginx должен быть установлен на сервере хоста, не в контейнере.

## Остановка

```bash
docker compose down
```
