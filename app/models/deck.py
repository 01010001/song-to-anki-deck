class AnkiDeck:
    def __init__(self, name="Sarki Sozleri Destesi"):
        self.name = name
        self.cards = []

    def add_card(self, card, require_romaji=False):
        if card.is_valid(require_romaji=require_romaji):
            self.cards.append(card)

    def valid_cards(self, require_romaji=False):
        return [c for c in self.cards if c.is_valid(require_romaji=require_romaji)]
