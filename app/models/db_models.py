from datetime import datetime, timezone

from app.database import db


class SongRecord(db.Model):
    __tablename__ = "songs"

    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    lyrics = db.Column(db.Text, nullable=False, default="")
    source_lang_code = db.Column(db.String(32), nullable=False, default="en")
    source_lang_name = db.Column(db.String(128), nullable=False, default="İngilizce")
    target_lang_code = db.Column(db.String(32), nullable=False, default="tr")
    target_lang_name = db.Column(db.String(128), nullable=False, default="Türkçe")
    source_is_japanese = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    cards = db.relationship(
        "CardRecord",
        back_populates="song",
        cascade="all, delete-orphan",
        order_by="CardRecord.sort_order",
    )

    def label(self):
        return f"{self.artist} — {self.title}"

    def to_sidebar_dict(self):
        return {
            "id": self.id,
            "artist": self.artist,
            "title": self.title,
            "source_lang_name": self.source_lang_name,
            "target_lang_name": self.target_lang_name,
            "card_count": len(self.cards),
            "created_at": self.created_at.strftime("%d.%m.%Y %H:%M") if self.created_at else "",
        }


class CardRecord(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.id"), nullable=False)
    front = db.Column(db.String(512), nullable=False)
    back = db.Column(db.String(512), nullable=False)
    romaji = db.Column(db.String(512), nullable=False, default="")
    difficulty = db.Column(db.String(32), nullable=False, default="orta")
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    song = db.relationship("SongRecord", back_populates="cards")

    def to_dict(self):
        d = {
            "id": self.id,
            "front": self.front,
            "back": self.back,
            "difficulty": self.difficulty,
        }
        if self.romaji:
            d["romaji"] = self.romaji
        return d

    def to_export_dict(self):
        return self.to_dict()
