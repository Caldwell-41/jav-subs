import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.avsubtitles.com/"


def code_in_title(jav_code, title):
    jc = jav_code.replace("-", "").replace("_", "").upper()
    t = title.replace("-", "").replace("_", "").upper()
    t = t.replace("[", "").replace("]", "")
    return jc in t


def search(jav_code, log):
    search_url = (
        f"{BASE_URL}search_results.php?"
        f"search={jav_code}&category=&language=en&not_before=&not_after="
        f"&screenshots=&rating=&scope=&orderby=movie_desc"
    )

    log.append(f"[AVSubs] Searching: {search_url}")

    try:
        r = requests.get(search_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        log.append(f"[AVSubs] Request failed: {e}")
        return None

    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.find_all("div", class_="card")

    for card in cards:
        h5 = card.find("h5")
        if not h5:
            continue

        title_text = h5.get_text(strip=True)
        if not code_in_title(jav_code, title_text):
            continue

        footer = card.find("div", class_="card-content-footer")
        if not footer:
            continue

        a = footer.find("a")
        if not a or not a.get("href"):
            continue

        details_url = urljoin(BASE_URL, a["href"])
        log.append(f"[AVSubs] Match found → {details_url}")
        return details_url

    log.append("[AVSubs] No matching titles found")
    return None


def get_english_info_link(details_url, log):
    log.append(f"[AVSubs] Loading details page: {details_url}")

    try:
        r = requests.get(details_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        log.append(f"[AVSubs] Failed to load details page: {e}")
        return None

    soup = BeautifulSoup(r.text, "lxml")
    rows = soup.find_all("tr")

    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 2:
            continue

        lang_td = tds[0]
        lang_img = lang_td.find("img", class_="language-flag")
        lang_text = lang_td.get_text(strip=True).lower()

        is_english = False
        if lang_img and "language_en" in lang_img.get("src", ""):
            is_english = True
        if "english" in lang_text:
            is_english = True

        if not is_english:
            continue

        a = tds[1].find("a", class_="link_button")
        if not a or not a.get("href"):
            continue

        info_url = urljoin(BASE_URL, a["href"])
        log.append(f"[AVSubs] English subtitle link → {info_url}")
        return info_url

    log.append("[AVSubs] No English subtitles available")
    return None


def download_subtitle(info_url, log):
    log.append(f"[AVSubs] Loading subtitle info page: {info_url}")

    try:
        r = requests.get(info_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        log.append(f"[AVSubs] Failed to load subtitle info page: {e}")
        return None

    soup = BeautifulSoup(r.text, "lxml")

    subid = soup.find("input", {"name": "subid"})
    revid = soup.find("input", {"name": "revid"})

    if not subid or not revid:
        log.append("[AVSubs] Missing subid/revid fields")
        return None

    subid = subid.get("value", "").strip()
    revid = revid.get("value", "").strip()

    if not subid or not revid:
        log.append("[AVSubs] Empty subid/revid")
        return None

    download_url = f"{BASE_URL}download_sub.php?subid={subid}&revid={revid}"
    log.append(f"[AVSubs] Downloading subtitle: {download_url}")

    try:
        srt = requests.get(download_url, timeout=20)
        srt.raise_for_status()
    except Exception as e:
        log.append(f"[AVSubs] Failed to download subtitle: {e}")
        return None

    return {
        "content": srt.content,
        "source": download_url,
        "provider": "avsubtitles",
    }


def get_subtitle(jav_code, log):
    details = search(jav_code, log)
    if not details:
        return None

    info = get_english_info_link(details, log)
    if not info:
        return None

    return download_subtitle(info, log)
