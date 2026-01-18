from providers import avsubtitles, subtitlecat


def download_subtitle(jav_code, log):
    log.append(f"Searching subtitles for {jav_code}")

    # Try AVSubtitles first
    log.append("[System] Trying AVSubtitles first…")
    result = avsubtitles.get_subtitle(jav_code, log)
    if result:
        log.append("[System] Subtitle found via AVSubtitles")
        return result

    # Fallback to SubtitleCat
    log.append("[System] AVSubtitles failed, trying SubtitleCat…")
    result = subtitlecat.get_subtitle(jav_code, log)
    if result:
        log.append("[System] Subtitle found via SubtitleCat")
        return result

    log.append("[System] No subtitles found from any provider")
    return None
