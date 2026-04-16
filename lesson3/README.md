# Selenium Parser Demo

Скрипт парсит `quotes.toscrape.com` с:

- авторизацией (опционально),
- пагинацией,
- сохранением данных в CSV (6 полей),
- сбором сетевого трафика и сравнением HTTP vs HTTPS.

## Что сохраняется

1. `output/quotes.csv`
  Поля: `quote`, `author`, `tags`, `author_url`, `page`, `scraped_at_utc`
2. `output/traffic.csv`
  Поля: `method`, `url`, `scheme`, `status_code`, `is_secure`, `content_type`, `response_size_bytes`, `redirect_location`
3. `output/http_https_analysis.txt`
  Краткий отчёт с подсчётами и выводами про HTTP/HTTPS.

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск

```bash
python parser.py
```

Параметры:

- `--base-url` (по умолчанию `http://quotes.toscrape.com`)
- `--username` / `--password` (по умолчанию `admin/admin`)
- `--headed` (запуск с видимым окном браузера)
- `--out-dir` (папка результатов)

Пример:

```bash
python parser.py --base-url "http://quotes.toscrape.com" --username "admin" --password "admin" --out-dir "output"
```

## Как сделан анализ HTTP и HTTPS

Скрипт собирает реальные запросы/ответы браузера (через Selenium Wire) и:

- считает, сколько запросов ушло по `http` и `https`,
- считает ответы `2xx` и `3xx`,
- отдельно считает редиректы `HTTP -> HTTPS`,
- сравнивает средний размер ответов.

Отличия:

- HTTP: данные передаются открытым текстом.
- HTTPS: данные шифруются (TLS), есть проверка подлинности сервера.
- Даже при HTTPS часть метаданных соединения остаётся видимой (домен, IP, объём трафика).

