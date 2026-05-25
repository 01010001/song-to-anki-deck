import logging



from app.debug import truncate

from app.services.lyrics_providers import PROVIDERS



logger = logging.getLogger("lyrics")



MAX_LYRICS_LENGTH = 8000





def _validate_length(lyrics, artist, title, provider_name):

    if len(lyrics) > MAX_LYRICS_LENGTH:

        logger.warning("[%s] Söz çok uzun: %d > %d", provider_name, len(lyrics), MAX_LYRICS_LENGTH)

        return None, f"Şarkı sözü çok uzun (max {MAX_LYRICS_LENGTH} karakter)."

    logger.info("Söz bulundu [%s]: %d karakter | %r - %r", provider_name, len(lyrics), artist, title)

    logger.debug("Önizleme: %s", truncate(lyrics, 80))

    return lyrics, ""





def fetch_lyrics(artist, title):

    logger.info("Söz aranıyor: %r - %r (%d kaynak denenecek)", artist, title, len(PROVIDERS))



    errors = []



    for name, provider_fn in PROVIDERS:

        logger.debug("--- Deneniyor: %s ---", name)

        try:

            lyrics, err = provider_fn(artist, title)

        except Exception as e:

            logger.exception("[%s] Beklenmeyen hata: %s", name, e)

            errors.append(f"{name}: {e}")

            continue



        if lyrics:

            return _validate_length(lyrics, artist, title, name)



        reason = err or "bilinmeyen"

        logger.debug("[%s] Başarısız: %s", name, reason)

        errors.append(f"{name}: {reason}")



    logger.error("Tüm kaynaklar başarısız (%d): %s", len(errors), " | ".join(errors[:5]))

    return None, (

        "Hiçbir kaynaktan şarkı sözü bulunamadı. "

        "Farklı bir şarkı deneyin veya sanatçı/şarkı adını kontrol edin."

    )


