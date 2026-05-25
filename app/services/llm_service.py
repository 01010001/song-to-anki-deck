import json
import logging
import os
import re
import time
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.debug import truncate
from app.config.languages import is_japanese_source

logger = logging.getLogger("llm")

MAX_LYRICS_LENGTH = 8000
# LLM'e gönderilen max söz uzunluğu (token / kota tasarrufu)
MAX_PROMPT_LYRICS = 4500

# Google AI Studio ücretsiz katman (2026) — önce hafif, sonra güçlü
# Ücretsiz DEĞİL: gemini-3.1-pro-preview (atlanır)
DEFAULT_MODELS = [
    "gemini-3.1-flash-lite",           # Free — çeviri / yüksek hacim
    "gemini-3.1-flash-lite-preview",   # Free — preview
    "gemini-3.5-flash",                # Free — daha akıllı
    "gemini-2.5-flash-lite",           # Yedek (eski free tier)
    "gemini-2.5-flash",
]


def _get_model_list():
    """Önce .env'deki tek model, yoksa GEMINI_MODELS, yoksa varsayılan liste."""
    single = os.getenv("GEMINI_MODEL", "").strip()
    if single:
        return [single]

    multi = os.getenv("GEMINI_MODELS", "").strip()
    if multi:
        return [m.strip() for m in multi.split(",") if m.strip()]

    return DEFAULT_MODELS.copy()


def _is_quota_error(exc):
    msg = str(exc).lower()
    return (
        "429" in msg
        or "resourceexhausted" in msg
        or "quota" in msg
        or isinstance(exc, google_exceptions.ResourceExhausted)
    )


def _quota_hint(errors):
    combined = " ".join(str(e) for e in errors)
    if "limit: 0" in combined:
        return (
            "Gemini ücretsiz kotanız seçilen model(ler) için 0 görünüyor. "
            "Çözüm: .env dosyasına GEMINI_MODEL=gemini-3.1-flash-lite ekleyin ve sunucuyu yeniden başlatın. "
            "Hâlâ olmazsa Google AI Studio'da projeye faturalandırma bağlayın "
            "(ücretsiz kullanım kotası için Google bunu isteyebilir): https://aistudio.google.com/"
        )
    retry = re.search(r"retry in (\d+)", combined, re.I)
    if retry:
        sec = int(float(retry.group(1)))
        return f"Gemini kota aşıldı. Yaklaşık {sec} saniye bekleyip tekrar deneyin."
    return "Gemini kota aşıldı. Bir dakika bekleyip tekrar deneyin."


def _build_prompt(lyrics, source_lang, target_lang, source_lang_code=""):
    snippet = lyrics[:MAX_PROMPT_LYRICS]
    truncated_note = ""
    if len(lyrics) > MAX_PROMPT_LYRICS:
        truncated_note = f"(Not: Sözlerin ilk {MAX_PROMPT_LYRICS} karakteri gönderildi.)\n"

    japanese = is_japanese_source(source_lang_code, source_lang)
    is_auto = source_lang_code == "auto"

    if is_auto:
        json_example = (
            '[\n  {"source": "kelime veya öbek", "target": "çeviri", "difficulty": "orta", '
            '"romaji": "sadece kaynak Japonca ise doldur"},\n  ...\n]'
        )
        romaji_rules = """
Kaynak dil OTOMATİK: Önce şarkı sözlerinin dilini kendin tespit et.
- Tespit ettiğin dilde "source" yaz, hedef dilde "target" çevir.
- Kaynak Japonca ise her öğede "romaji" (Hepburn) ZORUNLU.
- Japonca değilse "romaji" alanını ekleme veya boş bırak.
"""
        source_line = "Aşağıdaki şarkı sözlerinin dilini önce sen belirle, sonra o kaynak dilden analiz et."
    elif japanese:
        json_example = (
            '[\n  {"source": "愛してる", "romaji": "aishiteru", '
            '"target": "çeviri", "difficulty": "orta"},\n  ...\n]'
        )
        romaji_rules = """
ZORUNLU — Kaynak dil Japonca:
- Her öğe için "romaji" alanı ŞART (Hepburn romaji, küçük harf, boşluklu öbeklerde kelimeler ayrı).
- "source" alanında orijinal Japonca (kanji/kana) yaz.
- Romaji olmadan öğe ekleme.
"""
        source_line = f"Aşağıdaki şarkı sözlerini {source_lang} dilinden analiz et."
    else:
        json_example = '[\n  {"source": "kelime veya öbek", "target": "çeviri", "difficulty": "orta"},\n  ...\n]'
        romaji_rules = ""
        source_line = f"Aşağıdaki şarkı sözlerini {source_lang} dilinden analiz et."

    return f"""{source_line}
Her satır için öğrenmeye değer kelime veya kısa cümle öbeği seç (en fazla 25 öğe).
Her öğe için {target_lang} dilinde çeviri ver ve zorluk seviyesi belirle (kolay/orta/zor).
{romaji_rules}
SADECE JSON dizisi döndür, başka metin yazma:
{json_example}

{truncated_note}
Şarkı sözleri:
{snippet}
"""


def _parse_response(text):
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def _call_gemini(model_name, prompt, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    start = time.time()
    response = model.generate_content(prompt)
    elapsed = time.time() - start
    text = response.text.strip()
    logger.debug("[%s] Yanıt (%.2fs), uzunluk=%d", model_name, elapsed, len(text))
    logger.debug("[%s] Önizleme: %s", model_name, truncate(text, 200))
    return _parse_response(text)


def analyze_lyrics(lyrics, source_lang, target_lang, source_lang_code=""):
    if not lyrics or not lyrics.strip():
        logger.warning("Boş söz metni")
        return None, "Şarkı sözü içeriği eksik."

    if len(lyrics) > MAX_LYRICS_LENGTH:
        logger.warning("Metin sınırı aşıldı: %d karakter", len(lyrics))
        return None, f"Metin sınırı aşıldı (max {MAX_LYRICS_LENGTH} karakter)."

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY yok — .env dosyasını kontrol edin")
        return None, "GEMINI_API_KEY tanımlı değil. .env dosyasını kontrol edin."

    models = _get_model_list()
    japanese = is_japanese_source(source_lang_code, source_lang)
    prompt = _build_prompt(lyrics, source_lang, target_lang, source_lang_code)
    logger.info(
        "LLM analizi: %s -> %s | söz=%d karakter | japonca=%s | %d model",
        source_lang, target_lang, len(lyrics), japanese, len(models),
    )
    logger.debug("Model sırası: %s", models)

    quota_errors = []
    other_errors = []

    for model_name in models:
        logger.debug("--- Gemini model: %s ---", model_name)
        try:
            items = _call_gemini(model_name, prompt, api_key)
            logger.info("Başarılı model: %s (%d ham öğe)", model_name, len(items))
            break
        except json.JSONDecodeError as e:
            logger.error("[%s] JSON hatası: %s", model_name, e)
            other_errors.append(f"{model_name}: JSON hatası")
            continue
        except Exception as e:
            if _is_quota_error(e):
                logger.warning("[%s] Kota/limit: %s", model_name, truncate(str(e), 120))
                quota_errors.append(e)
                continue
            logger.exception("[%s] Beklenmeyen hata: %s", model_name, e)
            other_errors.append(f"{model_name}: {e}")
            continue
    else:
        # Tüm modeller başarısız
        if quota_errors:
            return None, _quota_hint(quota_errors)
        if other_errors:
            return None, f"LLM entegrasyon hatası: {' | '.join(other_errors[:3])}"
        return None, "LLM yanıt vermedi."

    cards = []
    skipped = 0
    romaji_missing = 0
    for item in items:
        source = (item.get("source") or "").strip()
        target = (item.get("target") or "").strip()
        romaji = (item.get("romaji") or "").strip()
        difficulty = (item.get("difficulty") or "orta").strip()

        if not source or not target:
            skipped += 1
            continue

        if japanese and not romaji:
            romaji_missing += 1
            logger.debug("Romaji eksik, atlandı: %r", source)
            continue

        card = {
            "front": source,
            "back": target,
            "difficulty": difficulty,
        }
        if romaji:
            card["romaji"] = romaji
        cards.append(card)

    logger.info(
        "Kart üretimi: %d geçerli, %d atlandı, %d romaji eksik (japonca)",
        len(cards), skipped, romaji_missing,
    )
    if not cards:
        return None, "LLM kart üretemedi. Farklı dil çifti veya şarkı deneyin."

    return cards, ""
