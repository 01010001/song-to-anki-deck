from app.database import db
from app.models.db_models import SongRecord, CardRecord


def list_songs(limit=100):
    return (
        SongRecord.query
        .order_by(SongRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def get_song(song_id):
    return SongRecord.query.get(song_id)


def save_song(artist, title, lyrics, source_code, source_name, target_code, target_name, is_japanese, cards):
    song = SongRecord(
        artist=artist,
        title=title,
        lyrics=lyrics,
        source_lang_code=source_code,
        source_lang_name=source_name,
        target_lang_code=target_code,
        target_lang_name=target_name,
        source_is_japanese=is_japanese,
    )
    db.session.add(song)
    db.session.flush()

    for i, c in enumerate(cards):
        db.session.add(CardRecord(
            song_id=song.id,
            front=c.get("front", ""),
            back=c.get("back", ""),
            romaji=c.get("romaji", ""),
            difficulty=c.get("difficulty", "orta"),
            sort_order=i,
        ))

    db.session.commit()
    return song


def get_cards_for_export(song):
    return [c.to_export_dict() for c in song.cards]


def update_card(card_id, front, back, romaji="", difficulty="orta"):
    card = CardRecord.query.get(card_id)
    if not card:
        return None, "Kart bulunamadı."
    card.front = front.strip()
    card.back = back.strip()
    card.romaji = (romaji or "").strip()
    card.difficulty = (difficulty or "orta").strip()
    db.session.commit()
    return card, ""
