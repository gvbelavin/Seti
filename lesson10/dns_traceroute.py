import csv
import platform
import socket
import subprocess
from datetime import datetime


DOMAINS = [
    "google.com",
    "github.com",
    "ya.ru",
    "python.org",
]


def get_ips(domain):
    ips = []
    try:
        # Возвращает и IPv4, и IPv6, если есть
        info = socket.getaddrinfo(domain, None)
        for row in info:
            ip = row[4][0]
            if ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips


def run_traceroute(ip):
    system = platform.system().lower()

    if "windows" in system:
        if ":" in ip:
            cmd = ["tracert", "-6", "-d", ip]
        else:
            cmd = ["tracert", "-d", ip]
    else:
        if ":" in ip:
            cmd = ["traceroute", "-6", "-n", ip]
        else:
            cmd = ["traceroute", "-n", ip]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    text = (result.stdout or "") + (result.stderr or "")
    return text.strip()


def main():
    rows = []
    now = datetime.utcnow().isoformat()

    for domain in DOMAINS:
        print("Domain:", domain)
        ips = get_ips(domain)

        if not ips:
            rows.append(
                {
                    "timestamp_utc": now,
                    "domain": domain,
                    "ip": "",
                    "ip_version": "",
                    "traceroute": "DNS lookup failed",
                }
            )
            continue

        for ip in ips:
            version = "IPv6" if ":" in ip else "IPv4"
            print("  IP:", ip, version)
            trace = run_traceroute(ip)

            rows.append(
                {
                    "timestamp_utc": now,
                    "domain": domain,
                    "ip": ip,
                    "ip_version": version,
                    "traceroute": trace.replace("\n", " | ").replace("\r", " "),
                }
            )

    with open("dns_traceroute_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp_utc", "domain", "ip", "ip_version", "traceroute"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nDone. File saved: dns_traceroute_results.csv")


if __name__ == "__main__":
    main()
