import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.languages import is_japanese_source
from app.models.card import FlashCard
from app.services.llm_service import _build_prompt


def test_is_japanese_by_code():
    assert is_japanese_source("ja", "Japonca") is True


def test_is_not_japanese():
    assert is_japanese_source("en", "İngilizce") is False


def test_prompt_requires_romaji_for_japanese():
    prompt = _build_prompt("test", "Japonca", "Türkçe", "ja")
    assert "romaji" in prompt.lower()
    assert "ZORUNLU" in prompt


def test_flashcard_anki_front_with_romaji():
    card = FlashCard("愛してる", "Seni seviyorum", romaji="aishiteru")
    assert "aishiteru" in card.anki_front()
    assert "愛してる" in card.anki_front()


def test_flashcard_requires_romaji_when_japanese():
    card = FlashCard("愛", "sevgi", romaji="")
    assert card.is_valid(require_romaji=True) is False
    assert card.is_valid(require_romaji=False) is True
