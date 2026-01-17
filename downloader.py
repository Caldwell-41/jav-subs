# downloader.py
import os
import re
import time
import logging
import requests as req
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

USE_MULTITHREADING = True
MAX_THREADS = 10

VIDEO_EXTENSIONS = {"mkv", "mp4", "mov", "avi"}
BASE_URL = "https://www.subtitlecat.com"

# logging config (root logger)
logging.basicConfig(
    filename="jav_subtitle_downloader.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

JAV_REGEX = re.compile(
    r"""
    (?<!\w)
    ([A-Za-z]{2,5})
    [-_ ]?
    (\d{2,5}[A-Za-z]?)
    (?!\w)
    """,
    re.VERBOSE
)

def extract_jav_code(filename):
    name = os.path.splitext(filename)[0]

    if "[" in name and "]" in name:
        inside = name.split("[", 1)[1].split("]", 1)[0]
        if JAV_REGEX.match(inside):
            return inside.upper()

    match = JAV_REGEX.search(name)
    if match:
        prefix, number = match.groups()
        return f"{prefix.upper()}-{number.upper()}"

    return name.split()[0].upper()

def get_videos_recursive(root_dir):
    videos = []
    for folder, _, files in os.walk(root_dir):
        for file in files:
            ext = file.split(".")[-1].lower()
            if ext in VIDEO_EXTENSIONS:
                videos.append(os.path.join(folder, file))
    return videos

def get_best_page_url(search_url, code):
    try:
        response = req.get(search_url)
        soup = BeautifulSoup(response.text, "lxml")

        table = soup.find("table", class_="table sub-table")
        if not table:
            return None

        rows = table.find("tbody").find_all("tr")
        best_href = None
        most_downs = 0

        for i, row in enumerate(rows):
            if i > 20:
                break

            a = row.find("a")
            if not a:
                continue

            text = a.text
            if code.lower() not in text.lower():
                continue

            downs_cell = row.find_all("td")[-2]
            downs = int(downs_cell.text.split()[0])

            if downs > most_downs:
                most_downs = downs
                best_href = a["href"]

        return best_href

    except Exception as e:
        logger.error(f"Error parsing search results for {code}: {e}")
        return None

def get_download_link(page_url):
    try:
        response = req.get(page_url)
        soup = BeautifulSoup(response.text, "lxml")
        a = soup.find("a", id="download_en")
        return a["href"] if a else None
    except Exception as e:
        logger.error(f"Error extracting download link from {page_url}: {e}")
        return None

def download_subtitle(code, save_path):
    search_url = f"{BASE_URL}/index.php?search={code}"
    logger.info(f"Searching subtitles for: {code}")

    page_href = None
    attempts = 0

    while page_href is None and attempts < 5:
        page_href = get_best_page_url(search_url, code)
        if not page_href:
            logger.info("Retrying search...")
            time.sleep(1)
        attempts += 1

    if not page_href:
        logger.error(f"FAILED: No subtitles found for {code}")
        return False

    page_url = f"{BASE_URL}/{page_href}"
    logger.info(f"Found subtitle page: {page_url}")

    dl_href = get_download_link(page_url)
    if not dl_href:
        logger.error(f"FAILED: No EN subtitle link for {code}")
        return False

    dl_url = f"{BASE_URL}{dl_href}"
    logger.info(f"Downloading from: {dl_url}")

    try:
        r = req.get(dl_url)
        with open(save_path, "wb") as f:
            f.write(r.content)

        logger.info(f"Saved subtitle: {save_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving subtitle for {code}: {e}")
        return False

def process_video(video):
    filename = os.path.basename(video)
    code = extract_jav_code(filename)
    subtitle_path = os.path.splitext(video)[0] + ".srt"

    logger.info("---------------------------------")
    logger.info(f"VIDEO: {filename}")
    logger.info(f"DETECTED CODE: {code}")
    logger.info(f"SAVING TO: {subtitle_path}")

    download_subtitle(code, subtitle_path)

def run_downloader(root_dir, use_multithreading=True, max_threads=10):
    global USE_MULTITHREADING, MAX_THREADS
    USE_MULTITHREADING = use_multithreading
    MAX_THREADS = max_threads

    videos = get_videos_recursive(root_dir)
    logger.info(f"Found {len(videos)} videos (recursive scan)")

    if USE_MULTITHREADING:
        logger.info(f"Using multithreading with {MAX_THREADS} threads")
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_video, v) for v in videos]
            for _ in as_completed(futures):
                pass
    else:
        logger.info("Running sequentially (no multithreading)")
        for video in videos:
            process_video(video)
