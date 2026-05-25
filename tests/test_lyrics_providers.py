"""Çoklu söz kaynağı mantığı testleri."""
from unittest.mock import patch

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import lyrics_service
from app.services.lyrics_providers import PROVIDERS


def test_multiple_providers_defined():
    assert len(PROVIDERS) >= 5
    names = [p[0] for p in PROVIDERS]
    assert any("LRCLIB" in n for n in names)
    assert any("lyrics.ovh" in n for n in names)


@patch("app.services.lyrics_service.PROVIDERS", [
    ("Kaynak-A", lambda a, t: (None, "yok")),
    ("Kaynak-B", lambda a, t: ("Satır bir\nSatır iki", None)),
    ("Kaynak-C", lambda a, t: (None, "yok")),
])
def test_tries_until_one_succeeds():
    lyrics, err = lyrics_service.fetch_lyrics("Artist", "Title")
    assert err == ""
    assert "Satır bir" in lyrics


@patch("app.services.lyrics_service.PROVIDERS", [
    ("A", lambda a, t: (None, "404")),
    ("B", lambda a, t: (None, "404")),
])
def test_all_fail_returns_message():
    lyrics, err = lyrics_service.fetch_lyrics("X", "Y")
    assert lyrics is None
    assert "Hiçbir kaynaktan" in err
