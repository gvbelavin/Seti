import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://quotes.toscrape.com")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--out-dir", default="output")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chrome_options = Options()
    if not args.headed:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1400,900")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )

    wait = WebDriverWait(driver, 15)
    quotes_data = []
    traffic_data = []
    login_ok = False

    try:
        # 1) Пытаемся авторизоваться
        driver.get(args.base_url + "/login")
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(args.username)
        driver.find_element(By.NAME, "password").send_keys(args.password)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        if "logout" in page_text:
            login_ok = True

        # 2) Парсим страницы с пагинацией
        driver.get(args.base_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".quote")))

        page_number = 1
        while True:
            cards = driver.find_elements(By.CSS_SELECTOR, ".quote")
            for card in cards:
                quote_text = card.find_element(By.CSS_SELECTOR, ".text").text
                author = card.find_element(By.CSS_SELECTOR, ".author").text
                tags = ", ".join([x.text for x in card.find_elements(By.CSS_SELECTOR, ".tag")])
                author_url = card.find_element(By.CSS_SELECTOR, "span a").get_attribute("href")

                # 6 полей (минимум 4 требуется по заданию)
                quotes_data.append(
                    {
                        "quote": quote_text,
                        "author": author,
                        "tags": tags,
                        "author_url": author_url,
                        "page": page_number,
                        "scraped_at": datetime.now().isoformat(),
                    }
                )

            next_button = driver.find_elements(By.CSS_SELECTOR, "li.next > a")
            if not next_button:
                break

            next_button[0].click()
            page_number += 1
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".quote")))

        # 3) Собираем сетевой трафик из performance логов Chrome
        perf_logs = driver.get_log("performance")

        request_map = {}
        size_map = {}

        for item in perf_logs:
            msg = json.loads(item["message"])["message"]
            method = msg.get("method", "")
            params = msg.get("params", {})

            if method == "Network.requestWillBeSent":
                req_id = params.get("requestId", "")
                req = params.get("request", {})
                request_map[req_id] = {
                    "url": req.get("url", ""),
                    "method": req.get("method", ""),
                }

            if method == "Network.loadingFinished":
                req_id = params.get("requestId", "")
                size_map[req_id] = int(params.get("encodedDataLength", 0))

            if method == "Network.responseReceived":
                req_id = params.get("requestId", "")
                response = params.get("response", {})
                url = response.get("url", request_map.get(req_id, {}).get("url", ""))
                scheme = urlparse(url).scheme.lower()

                headers = response.get("headers", {})
                location = headers.get("Location", headers.get("location", ""))
                content_type = headers.get("Content-Type", headers.get("content-type", ""))

                traffic_data.append(
                    {
                        "method": request_map.get(req_id, {}).get("method", ""),
                        "url": url,
                        "scheme": scheme,
                        "status_code": int(response.get("status", 0)),
                        "is_secure": "yes" if scheme == "https" else "no",
                        "content_type": content_type,
                        "response_size_bytes": size_map.get(req_id, 0),
                        "redirect_location": location,
                    }
                )

    finally:
        driver.quit()

    # 4) Сохраняем quotes в CSV
    quotes_fields = ["quote", "author", "tags", "author_url", "page", "scraped_at"]
    with open(out_dir / "quotes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=quotes_fields)
        writer.writeheader()
        writer.writerows(quotes_data)

    # 5) Сохраняем трафик в CSV
    traffic_fields = [
        "method",
        "url",
        "scheme",
        "status_code",
        "is_secure",
        "content_type",
        "response_size_bytes",
        "redirect_location",
    ]
    with open(out_dir / "traffic.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=traffic_fields)
        writer.writeheader()
        writer.writerows(traffic_data)

    # 6) Делаем простой анализ HTTP vs HTTPS
    http_count = sum(1 for x in traffic_data if x["scheme"] == "http")
    https_count = sum(1 for x in traffic_data if x["scheme"] == "https")
    redirects_to_https = sum(
        1
        for x in traffic_data
        if x["scheme"] == "http" and str(x["redirect_location"]).startswith("https://")
    )
    ok_2xx = sum(1 for x in traffic_data if str(x["status_code"]).startswith("2"))
    redirect_3xx = sum(1 for x in traffic_data if str(x["status_code"]).startswith("3"))

    if http_count > 0:
        avg_http = sum(x["response_size_bytes"] for x in traffic_data if x["scheme"] == "http") / http_count
    else:
        avg_http = 0

    if https_count > 0:
        avg_https = sum(x["response_size_bytes"] for x in traffic_data if x["scheme"] == "https") / https_count
    else:
        avg_https = 0

    analysis_text = (
        "Анализ HTTP и HTTPS\n"
        "===================\n"
        f"Авторизация успешна: {login_ok}\n"
        f"Всего цитат: {len(quotes_data)}\n"
        f"Всего запросов: {len(traffic_data)}\n"
        f"HTTP-запросов: {http_count}\n"
        f"HTTPS-запросов: {https_count}\n"
        f"Ответы 2xx: {ok_2xx}\n"
        f"Ответы 3xx: {redirect_3xx}\n"
        f"Редиректы HTTP -> HTTPS: {redirects_to_https}\n"
        f"Средний размер HTTP-ответа: {avg_http:.1f} байт\n"
        f"Средний размер HTTPS-ответа: {avg_https:.1f} байт\n\n"
        "Разница:\n"
        "1) HTTP - данные идут открытым текстом.\n"
        "2) HTTPS - данные шифруются TLS.\n"
        "3) HTTPS защищает от подмены и перехвата лучше, чем HTTP.\n"
    )

    print("Готово")
    print("Авторизация успешна:", login_ok)
    print("Цитат собрано:", len(quotes_data))
    print("Файлы сохранены: quotes.csv, traffic.csv")
    print()
    print(analysis_text)


if __name__ == "__main__":
    main()
