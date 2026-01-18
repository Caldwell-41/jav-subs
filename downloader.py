import os
import time
import threading
import re
import logging
import requests
from bs4 import BeautifulSoup

from providers import avsubtitles  # NEW

logger = logging.getLogger(__name__)

BASE_URL = "https://www.subtitlecat.com"
NET_SEM = threading.Semaphore(3)
SUB_CACHE = {}


# ------------------------------------------------------------
# JAV CODE EXTRACTION
# ------------------------------------------------------------
def extract_jav_code(filename):
    m = re.search(r"

\[([A-Za-z]{2,10}[-_]\d{2,5}[A-Za-z]?)\]

", filename)
    if m:
        return m.group(1)

    matches = re.findall(r"[A-Za-z]{2,10}[-_]\d{2,5}[A-Za-z]?", filename)
    if matches:
        return matches[-1]

    return None


# ------------------------------------------------------------
# SAFE GET
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# SUBTITLECAT SEARCH LOGIC
# ------------------------------------------------------------
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


def download_subtitle_from_subtitlecat(code):
    if code in SUB_CACHE:
        return SUB_CACHE[code]

    with NET_SEM:
        search_url = f"{BASE_URL}/index.php?search={code}"

        attempts = 0
        page_href = None

        while page_href is None and attempts < 6:
            page_href = find_best_result_href(search_url, code)
            if not page_href:
                attempts += 1
                time.sleep(1)

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

        result = {
            "bytes": r.content,
            "title": os.path.basename(page_href),
            "source": final_url
        }

        SUB_CACHE[code] = result
        return result


# ------------------------------------------------------------
# NEW: Unified provider chain
# ------------------------------------------------------------
def download_subtitle(jav_code, log):
    log.append(f"[System] Searching subtitles for {jav_code}")

    # 1. Try AVSubtitles first
    log.append("[System] Trying AVSubtitles first…")
    av_result = avsubtitles.get_subtitle(jav_code, log)
    if av_result:
        return {
            "content": av_result["content"],
            "source": av_result["source"],
            "provider": "avsubtitles"
        }

    # 2. Fallback to SubtitleCat
    log.append("[System] AVSubtitles failed, trying SubtitleCat…")
    sc_result = download_subtitle_from_subtitlecat(jav_code)
    if sc_result:
        return {
            "content": sc_result["bytes"],
            "source": sc_result["source"],
            "provider": "subtitlecat"
        }

    log.append("[System] No subtitles found from any provider")
    return None


# ------------------------------------------------------------
# VIDEO SCANNING
# ------------------------------------------------------------
def scan_videos(root_dir, include_existing=False):
    results = []

    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith((".mp4", ".mkv", ".avi", ".mov")):
                full = os.path.join(root, f)
                code = extract_jav_code(f)

                base, _ = os.path.splitext(full)
                has_sub = (
                    os.path.exists(base + ".srt") or
                    os.path.exists(base + ".en.srt")
                )

                results.append({
                    "file": full,
                    "code": code,
                    "has_sub": has_sub
                })

    return results
