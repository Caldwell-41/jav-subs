import os
import time
import threading
import re
import logging
import requests
from bs4 import BeautifulSoup

from providers import avsubtitles
from providers import subtitlecat   # NEW: use the real provider

logger = logging.getLogger(__name__)

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
# UNIFIED PROVIDER CHAIN
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
    sc_result = subtitlecat.get_subtitle(jav_code, log)
    if sc_result:
        return {
            "content": sc_result["content"],
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
