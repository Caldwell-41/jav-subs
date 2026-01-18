import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.subtitlecat.com"


def get_subtitle(jav_code, log):
    search_url = f"{BASE_URL}/?s={jav_code}"
    log.append(f"[SubCat] Searching: {search_url}")

    try:
        r = requests.get(search_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        log.append(f"[SubCat] Request failed: {e}")
        return None

    soup = BeautifulSoup(r.text, "lxml")
    links = soup.select("a[href*='/sub/']")

    if not links:
        log.append("[SubCat] No results found")
        return None

    first = links[0]["href"]
    page_url = BASE_URL + first
    log.append(f"[SubCat] Subtitle page → {page_url}")

    try:
        r2 = requests.get(page_url, timeout=15)
        r2.raise_for_status()
    except Exception as e:
        log.append(f"[SubCat] Failed to load subtitle page: {e}")
        return None

    soup2 = BeautifulSoup(r2.text, "lxml")
    download = soup2.select_one("a[href*='download']")

    if not download:
        log.append("[SubCat] No download link found")
        return None

    dl_url = BASE_URL + download["href"]
    log.append(f"[SubCat] Downloading: {dl_url}")

    try:
        srt = requests.get(dl_url, timeout=20)
        srt.raise_for_status()
    except Exception as e:
        log.append(f"[SubCat] Download failed: {e}")
        return None

    return {
        "content": srt.content,
        "source": dl_url,
        "provider": "subtitlecat",
    }
