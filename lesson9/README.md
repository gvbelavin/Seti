# lesson9

Python-скрипт для IPv4/IPv6 сравнения через Docker.

## Что делает

- Создает сеть и контейнеры `lesson9-a`, `lesson9-b`.
- Запускает `tcpdump` в фоне в контейнере A.
- Генерирует смешанный трафик:
  - IPv4 ping
  - IPv6 ping
  - TCP через `netcat` (IPv4 + IPv6)
- Копирует `pcap` файл на вашу машину в `results/lesson9_mix.pcap`.
- Пытается автоматически открыть дамп в Wireshark.
- Дополнительные `.txt` файлы не создает.

## Запуск (Windows)

```bash
python ipv4_ipv6_compare.py
```

## Файлы результата

- `results/lesson9_mix.pcap`
- `results/ping_ipv4.txt`
- `results/ping_ipv6.txt`
- `results/comparison_report.txt`
