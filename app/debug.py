"""Komut satırı debug yardımcıları."""

import logging

logger = logging.getLogger(__name__)


def truncate(text, max_len=120):
    if not text:
        return "(boş)"
    text = str(text).replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
