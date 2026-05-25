class Song:
    def __init__(self, title, artist, track_id=None):
        self.title = title
        self.artist = artist
        self.track_id = track_id
        self.lyrics = ""

    def to_dict(self):
        return {
            "title": self.title,
            "artist": self.artist,
            "track_id": self.track_id,
        }
