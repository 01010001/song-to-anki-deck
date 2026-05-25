class FlashCard:
    def __init__(self, front, back, difficulty="orta", romaji=""):
        self.front = front
        self.back = back
        self.difficulty = difficulty
        self.romaji = romaji or ""

    def is_valid(self, require_romaji=False):
        if not (self.front and self.back):
            return False
        if require_romaji and not self.romaji.strip():
            return False
        return True

    def anki_front(self):
        """Anki ön yüz: Japonca + romaji (HTML)."""
        if self.romaji.strip():
            return f'{self.front}<br><span style="color:#555;font-style:italic;">{self.romaji}</span>'
        return self.front

    def to_dict(self):
        d = {
            "front": self.front,
            "back": self.back,
            "difficulty": self.difficulty,
        }
        if self.romaji:
            d["romaji"] = self.romaji
        return d
