"""
Şarkı sözü sağlayıcıları — her biri (lyrics, hata_mesajı) döner.
Başarı: (metin, None)  |  Başarısız: (None, kısa sebep)
"""

import logging
import re
import time
import xml.etree.ElementTree as ET
import requests
from urllib.parse import quote

logger = logging.getLogger("lyrics.providers")

HEADERS = {
    "User-Agent": "AnkiSongLyrics/1.0 (edu-project)",
    "Accept": "application/json",
}

TIMEOUT = 18


def _get(url, params=None, provider_name=""):
    start = time.time()
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        elapsed = time.time() - start
        logger.debug("[%s] HTTP %d (%.2fs) url=%s", provider_name, r.status_code, elapsed, url)
        return r, None
    except requests.RequestException as e:
        logger.warning("[%s] Bağlantı hatası: %s", provider_name, e)
        return None, str(e)


def _strip_lrc(text):
    """Senkron sözlerden zaman damgalarını temizle."""
    lines = []
    for line in text.splitlines():
        cleaned = re.sub(r"\[\d+:\d+(?:\.\d+)?\]", "", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def _from_lrclib_record(data):
    plain = (data.get("plainLyrics") or "").strip()
    if plain:
        return plain
    synced = (data.get("syncedLyrics") or "").strip()
    if synced:
        return _strip_lrc(synced)
    return ""


# --- 1. LRCLIB: önbellekli eşleşme (hızlı) ---


def fetch_lrclib_cached(artist, title):
    url = "https://lrclib.net/api/get-cached"
    params = {"artist_name": artist, "track_name": title}
    r, err = _get(url, params, "LRCLIB-cached")
    if err:
        return None, err
    if r.status_code == 404:
        return None, "önbellekte yok"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    text = _from_lrclib_record(r.json())
    return (text, None) if text else (None, "boş yanıt")


# --- 2. LRCLIB: tam arama (dış kaynaklara da bakar) ---


def fetch_lrclib_get(artist, title):
    url = "https://lrclib.net/api/get"
    params = {"artist_name": artist, "track_name": title}
    r, err = _get(url, params, "LRCLIB-get")
    if err:
        return None, err
    if r.status_code == 404:
        return None, "eşleşme yok"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    text = _from_lrclib_record(r.json())
    return (text, None) if text else (None, "boş yanıt")


# --- 3. LRCLIB: anahtar kelime araması ---


def fetch_lrclib_search(artist, title):
    url = "https://lrclib.net/api/search"
    q = f"{artist} {title}".strip()
    r, err = _get(url, {"q": q}, "LRCLIB-search")
    if err:
        return None, err
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    items = r.json()
    if not items:
        return None, "sonuç yok"

    artist_l = artist.lower()
    title_l = title.lower()
    best = None
    for item in items:
        a = (item.get("artistName") or "").lower()
        t = (item.get("trackName") or "").lower()
        if artist_l in a or a in artist_l:
            if title_l in t or t in title_l:
                best = item
                break
    if not best:
        best = items[0]
        logger.debug("[LRCLIB-search] Tam eşleşme yok, ilk sonuç: %r - %r",
                     best.get("artistName"), best.get("trackName"))

    text = _from_lrclib_record(best)
    return (text, None) if text else (None, "boş yanıt")


# --- 4. lyrics.ovh ---


def fetch_lyrics_ovh(artist, title):
    url = f"https://api.lyrics.ovh/v1/{quote(artist)}/{quote(title)}"
    r, err = _get(url, None, "lyrics.ovh")
    if err:
        return None, err
    if r.status_code == 404:
        return None, "404"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    text = (r.json().get("lyrics") or "").strip()
    return (text, None) if text else (None, "boş yanıt")


# --- 5. lyrics.ovh suggest (Deezer) → düzeltilmiş isimle tekrar dene ---


def fetch_lyrics_ovh_suggest(artist, title):
    suggest_url = f"https://api.lyrics.ovh/suggest/{quote(artist + ' ' + title)}"
    r, err = _get(suggest_url, None, "lyrics.ovh-suggest")
    if err:
        return None, err
    if r.status_code != 200:
        return None, f"suggest HTTP {r.status_code}"

    data = r.json()
    items = data.get("data") or []
    if not items:
        return None, "suggest sonuç yok"

    hit = items[0]
    new_artist = hit.get("artist", {}).get("name") or artist
    new_title = hit.get("title") or title
    logger.debug("[lyrics.ovh-suggest] Yeni eşleşme: %r - %r", new_artist, new_title)

    if new_artist == artist and new_title == title:
        return None, "suggest aynı isim"

    return fetch_lyrics_ovh(new_artist, new_title)


# --- 6. ChartLyrics (XML, iki adım) ---


def fetch_chartlyrics(artist, title):
    search_url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyric"
    r, err = _get(search_url, {"artist": artist, "song": title}, "ChartLyrics")
    if err:
        return None, err
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"

    try:
        root = ET.fromstring(r.text)
    except ET.ParseError as e:
        return None, f"XML hatası: {e}"

    lyric_id = lyric_checksum = None
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "LyricId" and elem.text:
            lyric_id = elem.text
        if tag == "LyricChecksum" and elem.text:
            lyric_checksum = elem.text
        if tag == "Lyric" and elem.text and elem.text.strip():
            return elem.text.strip(), None

    if not lyric_id or not lyric_checksum:
        return None, "ChartLyrics eşleşme yok"

    get_url = "http://api.chartlyrics.com/apiv1.asmx/GetLyric"
    r2, err2 = _get(get_url, {"lyricId": lyric_id, "lyricChecksum": lyric_checksum}, "ChartLyrics-Get")
    if err2:
        return None, err2
    if r2.status_code != 200:
        return None, f"GetLyric HTTP {r2.status_code}"

    try:
        root2 = ET.fromstring(r2.text)
    except ET.ParseError as e:
        return None, f"XML hatası: {e}"

    for elem in root2.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "Lyric" and elem.text and elem.text.strip():
            return elem.text.strip(), None

    return None, "GetLyric boş"


# --- 7. lyrics.ovh: sanatçı/şarkı sırası ters (bazı kayıtlar için) ---


def fetch_lyrics_ovh_reversed(artist, title):
    return fetch_lyrics_ovh(title, artist)


# Sağlayıcı sırası (önce hızlı/güvenilir olanlar)
PROVIDERS = [
    ("LRCLIB (önbellek)", fetch_lrclib_cached),
    ("LRCLIB (arama)", fetch_lrclib_search),
    ("LRCLIB (tam)", fetch_lrclib_get),
    ("lyrics.ovh", fetch_lyrics_ovh),
    ("lyrics.ovh (Deezer öneri)", fetch_lyrics_ovh_suggest),
    ("ChartLyrics", fetch_chartlyrics),
    ("lyrics.ovh (ters)", fetch_lyrics_ovh_reversed),
]
