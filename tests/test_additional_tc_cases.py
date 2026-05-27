from unittest.mock import MagicMock, patch

import io
import os
import tempfile


def test_TC_01_gecerli_sarkı_araması(client):
    with patch("app.services.search_service.search_songs") as mock_search:
        mock_search.return_value = [
            {"title": "Tokyo Incidents", "artist": "Artist A", "track_id": None},
        ]
        res = client.post(
            "/api/search",
            json={"query": "Tokyo Incidents"},
            content_type="application/json",
        )

    data = res.get_json()
    assert res.status_code == 200
    assert len(data["results"]) >= 1
    assert data["results"][0]["title"]
    assert data["results"][0]["artist"]


def test_TC_02_var_olmayan_sarkı_araması(client):
    with patch("app.services.search_service.search_songs") as mock_search:
        mock_search.return_value = []
        res = client.post(
            "/api/search",
            json={"query": "xqzw123notexist"},
            content_type="application/json",
        )

    data = res.get_json()
    assert res.status_code == 200
    assert data["results"] == []
    # Beklenen: boş liste ve mesaj
    assert "Sonuç bulunamadı" in data.get("message", "")


def test_TC_03_bos_arama_girisi_sinir_deger(client):
    with patch("app.services.search_service.requests.get") as mock_get:
        res = client.post(
            "/api/search",
            json={"query": ""},
            content_type="application/json",
        )
        assert not mock_get.called

    data = res.get_json()
    assert res.status_code == 400
    assert data["error"] == "Arama alanı boş bırakılamaz"


def test_TC_04_cok_uzun_arama_girisi(client):
    long_query = "a" * 300
    with patch("app.services.search_service.requests.get") as mock_get:
        res = client.post(
            "/api/search",
            json={"query": long_query},
            content_type="application/json",
        )
        assert not mock_get.called

    data = res.get_json()
    assert res.status_code == 400
    # Beklenen: HTTP 400 veya kırpılmış istek; biz 400 dönüyoruz.
    assert "Arama çok uzun" in data["error"]


def test_TC_05_sarkı_secmeden_analiz(client):
    with patch("app.services.lyrics_service.fetch_lyrics") as mock_lyrics, patch(
        "app.services.llm_service.analyze_lyrics"
    ) as mock_llm:
        res = client.post(
            "/api/analyze",
            json={"artist": "", "title": "", "source_lang": "en", "target_lang": "tr"},
            content_type="application/json",
        )

    data = res.get_json()
    assert res.status_code == 400
    assert "Lütfen önce bir şarkı seçin" in data["error"]
    assert not mock_lyrics.called
    assert not mock_llm.called


def test_TC_06_analiz_yapilmadan_deste_indirme(client):
    with patch("app.services.anki_service.create_apkg") as mock_apkg:
        res = client.post("/api/export", json=None, content_type="application/json")
        assert not mock_apkg.called

    # Bazı durumlarda Flask get_json() parse edemeyebiliyor; güvenli fallback yapıyoruz.
    data = res.get_json(silent=True) or {"error": res.data.decode("utf-8", errors="ignore")}
    assert res.status_code == 400
    assert "Önce analiz yapılması gerekiyor" in data["error"]


def test_TC_07_basarili_analiz_sonrasi_disya_aktarma(client):
    dummy_lyrics = "lyrics..."
    dummy_cards = [
        {"front": "hello", "back": "merhaba", "difficulty": "kolay", "romaji": ""},
        {"front": "world", "back": "dünya", "difficulty": "orta", "romaji": ""},
    ]

    # 1) Analyze: LLM ve söz servislerini taklit et
    with patch("app.services.lyrics_service.fetch_lyrics") as mock_lyrics, patch(
        "app.services.llm_service.analyze_lyrics"
    ) as mock_llm:
        mock_lyrics.return_value = (dummy_lyrics, "")
        mock_llm.return_value = (dummy_cards, "")

        res = client.post(
            "/api/analyze",
            json={
                "artist": "Artist A",
                "title": "Tokyo Incidents",
                "source_lang": "en",
                "target_lang": "tr",
                "source_lang_custom": "",
                "target_lang_custom": "",
            },
            content_type="application/json",
        )

    assert res.status_code == 200
    song_id = res.get_json()["song_id"]

    # 2) Export: Anki paket üretimini taklit et
    fd, path = tempfile.mkstemp(suffix=".apkg")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(b"PK\x03\x04" + b"0" * 128)  # zip header başlangıcı

    with patch("app.services.anki_service.create_apkg") as mock_apkg:
        mock_apkg.return_value = (path, "")

        res2 = client.post(f"/api/songs/{song_id}/export")

    assert res2.status_code == 200
    assert res2.data[:2] == b"PK"

