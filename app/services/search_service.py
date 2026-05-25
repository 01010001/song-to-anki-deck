import logging
import re
import time
import requests

logger = logging.getLogger("search")

# Geçersiz arama karakterleri (Test Vakası 1)
INVALID_SEARCH_PATTERN = re.compile(r"^[^a-zA-Z0-9\sçğıöşüÇĞİÖŞÜ\-\'\.]+$")


def is_valid_search(query):
    query = query.strip()
    if len(query) < 2:
        logger.debug("Doğrulama FAIL: çok kısa arama (%d karakter)", len(query))
        return False, "Arama en az 2 karakter olmalıdır."
    if INVALID_SEARCH_PATTERN.match(query):
        logger.debug("Doğrulama FAIL: geçersiz karakterler query=%r", query)
        return False, "Geçersiz arama. Lütfen şarkı veya sanatçı adı girin."
    logger.debug("Doğrulama OK: query=%r", query)
    return True, ""


def search_songs(query, limit=10):
    url = "https://itunes.apple.com/search"
    params = {"term": query, "media": "music", "entity": "song", "limit": limit}
    logger.debug("iTunes API çağrısı: term=%r limit=%d", query, limit)

    start = time.time()
    response = requests.get(url, params=params, timeout=10)
    elapsed = time.time() - start

    logger.debug("iTunes yanıt: HTTP %d (%.2fs)", response.status_code, elapsed)
    response.raise_for_status()
    data = response.json()

    raw_count = len(data.get("results", []))
    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("trackName", ""),
            "artist": item.get("artistName", ""),
            "track_id": item.get("trackId"),
        })

    logger.debug("iTunes ham=%d, işlenen=%d", raw_count, len(results))
    if results:
        logger.debug("İlk sonuç: %r - %r", results[0]["artist"], results[0]["title"])
    else:
        logger.warning("iTunes sonuç döndürmedi")

    return results
