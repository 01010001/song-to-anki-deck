import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import (
    _get_model_list,
    _quota_hint,
    _is_quota_error,
    analyze_lyrics,
)


def test_default_models_include_gemini3_free_tier():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("GEMINI_MODEL", None)
        os.environ.pop("GEMINI_MODELS", None)
        models = _get_model_list()
    assert models[0] == "gemini-3.1-flash-lite"
    assert "gemini-3.5-flash" in models
    assert "gemini-3.1-pro-preview" not in models


def test_env_single_model():
    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-1.5-flash"}):
        assert _get_model_list() == ["gemini-1.5-flash"]


def test_quota_hint_limit_zero():
    msg = _quota_hint([Exception("limit: 0, model: gemini-2.0-flash")])
    assert "gemini-3.1-flash-lite" in msg


@patch("app.services.llm_service._call_gemini")
def test_tries_second_model_on_quota(mock_call):
    mock_call.side_effect = [
        Exception("429 quota limit: 0"),
        [{"source": "hi", "target": "merhaba", "difficulty": "kolay"}],
    ]
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODELS": "bad-model,good-model"}):
        cards, err = analyze_lyrics("hello world " * 5, "İngilizce", "Türkçe")
    assert err == ""
    assert len(cards) == 1
    assert mock_call.call_count == 2


def test_is_quota_error():
    assert _is_quota_error(Exception("429 ResourceExhausted")) is True
    assert _is_quota_error(Exception("something else")) is False
