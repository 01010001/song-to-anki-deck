"""
Kara kutu test vakaları — HTTP API üzerinden gerçek kullanıcı akışları.
"""

from app.database import db
from app.models.db_models import SongRecord, CardRecord


def test_tv1_valid_song_search_returns_results(client):
    from unittest.mock import patch

    with patch("app.services.search_service.search_songs") as mock_search:
        mock_search.return_value = [
            {"title": "Hello", "artist": "Adele", "track_id": None},
        ]
        response = client.post(
            "/api/search",
            json={"query": "Adele Hello"},
            content_type="application/json",
        )
    data = response.get_json()
    assert response.status_code == 200, data
    assert len(data["results"]) >= 1
    assert data["results"][0].get("title")
    assert data["results"][0].get("artist")


def test_tv2_analyze_without_song_info_rejected(client):
    response = client.post(
        "/api/analyze",
        json={"artist": "", "title": "", "source_lang": "en", "target_lang": "tr"},
        content_type="application/json",
    )
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data


def test_tv3_export_without_song_rejected(client):
    response = client.post("/api/songs/999/export")
    data = response.get_json()
    assert response.status_code == 404
    assert "error" in data


def test_export_with_saved_song(client):
    with client.application.app_context():
        song = SongRecord(artist="Test", title="Song", lyrics="line", source_lang_code="en", source_lang_name="English", target_lang_code="tr", target_lang_name="Turkish")
        db.session.add(song)
        db.session.flush()
        db.session.add(CardRecord(song_id=song.id, front="hi", back="merhaba", sort_order=0))
        db.session.commit()
        sid = song.id

    response = client.post(f"/api/songs/{sid}/export")
    assert response.status_code == 200
    assert response.data[:2] == b"PK"


def test_update_card(client):
    with client.application.app_context():
        song = SongRecord(artist="A", title="B", lyrics="x", source_lang_code="en", source_lang_name="En", target_lang_code="tr", target_lang_name="Tr")
        db.session.add(song)
        db.session.flush()
        card = CardRecord(song_id=song.id, front="old", back="eski", sort_order=0)
        db.session.add(card)
        db.session.commit()
        sid, cid = song.id, card.id

    res = client.put(
        f"/api/songs/{sid}/cards/{cid}",
        json={"front": "new", "back": "yeni", "difficulty": "kolay"},
    )
    assert res.status_code == 200
    assert res.get_json()["card"]["front"] == "new"
