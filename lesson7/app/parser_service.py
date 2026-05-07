import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def _build_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1400,900")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    chromium_bin = Path("/usr/bin/chromium")
    chromedriver_bin = Path("/usr/bin/chromedriver")

    if chromium_bin.exists():
        chrome_options.binary_location = str(chromium_bin)

    if chromedriver_bin.exists():
        return webdriver.Chrome(service=Service(str(chromedriver_bin)), options=chrome_options)

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


def run_parser(base_url: str, username: str, password: str):
    driver = _build_driver()
    wait = WebDriverWait(driver, 15)
    quotes_data = []
    traffic_data = []
    login_ok = False

    try:
        driver.get(base_url.rstrip("/") + "/login")
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        login_ok = "logout" in body_text

        driver.get(base_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".quote")))

        page_number = 1
        while True:
            cards = driver.find_elements(By.CSS_SELECTOR, ".quote")
            for card in cards:
                quote_text = card.find_element(By.CSS_SELECTOR, ".text").text
                author = card.find_element(By.CSS_SELECTOR, ".author").text
                tags = ", ".join([x.text for x in card.find_elements(By.CSS_SELECTOR, ".tag")])
                author_url = card.find_element(By.CSS_SELECTOR, "span a").get_attribute("href")

                quotes_data.append(
                    {
                        "quote": quote_text,
                        "author": author,
                        "tags": tags,
                        "author_url": author_url,
                        "page": page_number,
                        "scraped_at": datetime.now(),
                    }
                )

            next_button = driver.find_elements(By.CSS_SELECTOR, "li.next > a")
            if not next_button:
                break
            next_button[0].click()
            page_number += 1
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".quote")))

        perf_logs = driver.get_log("performance")
        request_map = {}
        size_map = {}

        for item in perf_logs:
            message = json.loads(item["message"])["message"]
            method = message.get("method", "")
            params = message.get("params", {})

            if method == "Network.requestWillBeSent":
                req_id = params.get("requestId", "")
                req_data = params.get("request", {})
                request_map[req_id] = {
                    "url": req_data.get("url", ""),
                    "method": req_data.get("method", ""),
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
                        "content_type": content_type,
                        "response_size_bytes": size_map.get(req_id, 0),
                        "redirect_location": location,
                    }
                )
    finally:
        driver.quit()

    http_count = sum(1 for x in traffic_data if x["scheme"] == "http")
    https_count = sum(1 for x in traffic_data if x["scheme"] == "https")
    redirects_to_https = sum(
        1
        for x in traffic_data
        if x["scheme"] == "http" and str(x["redirect_location"]).startswith("https://")
    )
    responses_2xx = sum(1 for x in traffic_data if str(x["status_code"]).startswith("2"))
    responses_3xx = sum(1 for x in traffic_data if str(x["status_code"]).startswith("3"))

    avg_http_size = (
        int(sum(x["response_size_bytes"] for x in traffic_data if x["scheme"] == "http") / http_count)
        if http_count
        else 0
    )
    avg_https_size = (
        int(sum(x["response_size_bytes"] for x in traffic_data if x["scheme"] == "https") / https_count)
        if https_count
        else 0
    )

    stats = {
        "login_ok": login_ok,
        "total_quotes": len(quotes_data),
        "total_requests": len(traffic_data),
        "http_requests": http_count,
        "https_requests": https_count,
        "responses_2xx": responses_2xx,
        "responses_3xx": responses_3xx,
        "redirects_http_to_https": redirects_to_https,
        "avg_http_size": avg_http_size,
        "avg_https_size": avg_https_size,
    }

    return quotes_data, stats
