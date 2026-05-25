import logging
import os
import random
import tempfile
import genanki
from app.models.card import FlashCard
from app.models.deck import AnkiDeck

logger = logging.getLogger("anki")


def create_apkg(deck_name, cards_data, require_romaji=False):
    logger.debug("Deste oluşturuluyor: name=%r ham_kart=%d", deck_name, len(cards_data))
    deck = AnkiDeck(deck_name)

    for item in cards_data:
        card = FlashCard(
            front=item.get("front", ""),
            back=item.get("back", ""),
            difficulty=item.get("difficulty", "orta"),
            romaji=item.get("romaji", ""),
        )
        deck.add_card(card, require_romaji=require_romaji)

    valid = deck.valid_cards(require_romaji=require_romaji)
    logger.debug("Geçerli kart: %d / %d", len(valid), len(cards_data))
    if not valid:
        logger.warning("Hiç geçerli kart yok")
        return None, "Dışa aktarılacak geçerli kart bulunamadı."

    model_id = random.randrange(1 << 30, 1 << 31)
    deck_id = random.randrange(1 << 30, 1 << 31)

    anki_model = genanki.Model(
        model_id,
        "Sarki Kart Modeli",
        fields=[{"name": "OnYuz"}, {"name": "ArkaYuz"}],
        templates=[
            {
                "name": "Kart 1",
                "qfmt": "{{OnYuz}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{ArkaYuz}}',
            }
        ],
    )

    anki_deck = genanki.Deck(deck_id, deck_name)
    for card in valid:
        note = genanki.Note(
            model=anki_model,
            fields=[card.anki_front(), card.back],
        )
        anki_deck.add_note(note)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".apkg")
    tmp.close()
    genanki.Package(anki_deck).write_to_file(tmp.name)
    size = os.path.getsize(tmp.name)
    logger.info(".apkg yazıldı: %s (%d byte, %d kart)", tmp.name, size, len(valid))
    return tmp.name, ""
