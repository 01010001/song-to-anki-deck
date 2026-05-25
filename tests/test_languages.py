import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.languages import resolve_language, LANGUAGES


def test_many_languages_available():
    assert len(LANGUAGES) >= 50


def test_custom_language():
    name, err = resolve_language("other", "Norveççe (Nynorsk)")
    assert err == ""
    assert name == "Norveççe (Nynorsk)"


def test_auto_resolves():
    name, err = resolve_language("auto", "")
    assert err == ""
    assert "Otomatik" in name


def test_japanese_resolves():
    name, err = resolve_language("ja", "")
    assert err == ""
    assert name == "Japonca"
