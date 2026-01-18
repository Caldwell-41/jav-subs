import requests
from bs4 import BeautifulSoup
import time
import re
import os

BASE_URL = "https://www.subtitlecat.com"
NET_SEM = None  # handled in downloader.py


def safe_get(url, retries=3, timeout=10):
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
        except Exception:
            pass
        time.sleep(1)
    return None


def find_best_result_href(search_url, code):
    r = safe_get(search_url)
    if not r:
        return None

    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table", class_="table sub-table")
    if not table:
        return None

    rows = table.find("tbody").find_all("tr")

    best_href = None
    most_downloads = 0

    for i, row in enumerate(rows):
        if i > 20:
            break

        a = row.find("a")
        if not a:
            continue

        title = a.text.strip()

        if code.lower() not in title.lower():
            continue

        cols = row.find_all("td")
        try:
            downloads = int(cols[-2].text.split()[0])
        except Exception:
            downloads = 0

        if downloads > most_downloads:
            most_downloads = downloads
            best_href = a.get("href")

    return best_href


def get_english_download_href(page_url):
    r = safe_get(page_url)
    if not r:
        return None

    soup = BeautifulSoup(r.text, "lxml")
    a = soup.find("a", id="download_en")
    if not a:
        return None

    return a.get("href")


def get_subtitle(jav_code, log):
    search_url = f"{BASE_URL}/index.php?search={jav_code}"

    page_href = find_best_result_href(search_url, jav_code)
    if not page_href:
        return None

    if not page_href.startswith("/"):
        page_href = "/" + page_href

    page_url = BASE_URL + page_href

    href = get_english_download_href(page_url)
    if not href:
        return None

    if not href.startswith("/"):
        href = "/" + href

    final_url = BASE_URL + href

    r = safe_get(final_url)
    if not r:
        return None

    return {
        "content": r.content,
        "source": final_url,
        "provider": "subtitlecat"
    }
