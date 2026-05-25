# ISO 639-1 kodu → Türkçe dil adı (LLM prompt için tam isim kullanılır)

LANGUAGES = [
    ("af", "Afrikaans"),
    ("sq", "Arnavutça"),
    ("am", "Amharca"),
    ("ar", "Arapça"),
    ("hy", "Ermenice"),
    ("az", "Azerbaycanca"),
    ("eu", "Baskça"),
    ("be", "Belarusça"),
    ("bn", "Bengalce"),
    ("bs", "Boşnakça"),
    ("bg", "Bulgarca"),
    ("my", "Burmaca"),
    ("ca", "Katalanca"),
    ("zh", "Çince (Mandarin)"),
    ("zh-yue", "Çince (Kantonca)"),
    ("hr", "Hırvatça"),
    ("cs", "Çekçe"),
    ("da", "Danca"),
    ("nl", "Felemenkçe"),
    ("en", "İngilizce"),
    ("eo", "Esperanto"),
    ("et", "Estonca"),
    ("fi", "Fince"),
    ("fr", "Fransızca"),
    ("gl", "Galiçyaca"),
    ("ka", "Gürcüce"),
    ("de", "Almanca"),
    ("el", "Yunanca"),
    ("gu", "Guceratça"),
    ("ht", "Haitice"),
    ("ha", "Hausa"),
    ("he", "İbranice"),
    ("hi", "Hintçe"),
    ("hu", "Macarca"),
    ("is", "İzlandaca"),
    ("id", "Endonezce"),
    ("ga", "İrlandaca"),
    ("it", "İtalyanca"),
    ("ja", "Japonca"),
    ("kn", "Kannada"),
    ("kk", "Kazakça"),
    ("km", "Khmerce"),
    ("ko", "Korece"),
    ("ku", "Kürtçe"),
    ("ky", "Kırgızca"),
    ("lo", "Laoca"),
    ("la", "Latince"),
    ("lv", "Letonca"),
    ("lt", "Litvanca"),
    ("mk", "Makedonca"),
    ("ms", "Malayca"),
    ("ml", "Malayalam"),
    ("mt", "Maltaca"),
    ("mr", "Marathi"),
    ("mn", "Moğolca"),
    ("ne", "Nepalce"),
    ("no", "Norveççe"),
    ("or", "Odiya"),
    ("ps", "Peştuca"),
    ("fa", "Farsça"),
    ("pl", "Lehçe"),
    ("pt", "Portekizce"),
    ("pt-br", "Portekizce (Brezilya)"),
    ("pa", "Pencapça"),
    ("ro", "Romence"),
    ("ru", "Rusça"),
    ("sr", "Sırpça"),
    ("si", "Sinhala"),
    ("sk", "Slovakça"),
    ("sl", "Slovence"),
    ("so", "Somalice"),
    ("es", "İspanyolca"),
    ("sw", "Svahili"),
    ("sv", "İsveççe"),
    ("tl", "Tagalogca / Filipince"),
    ("ta", "Tamilce"),
    ("te", "Telugu"),
    ("th", "Tayca"),
    ("tr", "Türkçe"),
    ("uk", "Ukraynaca"),
    ("ur", "Urduca"),
    ("uz", "Özbekçe"),
    ("vi", "Vietnamca"),
    ("cy", "Galce"),
    ("xh", "Kosa"),
    ("zu", "Zuluca"),
    ("other", "Diğer (elle yazın)"),
]

# Kod → tam ad sözlüğü
LANG_NAMES = dict(LANGUAGES)
LANG_NAMES["auto"] = "Otomatik (algıla)"


def is_japanese_source(lang_code, lang_name=""):
    """Kaynak dil Japonca mı? (romaji zorunluluğu için)"""
    code = (lang_code or "").strip().lower()
    if code == "ja":
        return True
    name = (lang_name or "").lower()
    return any(k in name for k in ("japon", "japanese", "日本", "nihongo"))


def resolve_language(code, custom_name=""):
    """Seçilen kodu LLM için okunabilir dil adına çevirir."""
    code = (code or "").strip()
    custom_name = (custom_name or "").strip()

    if code == "auto":
        return LANG_NAMES["auto"], ""

    if code == "other":
        if not custom_name:
            return None, "Lütfen dil adını yazın."
        if len(custom_name) < 2:
            return None, "Dil adı en az 2 karakter olmalıdır."
        return custom_name, ""

    name = LANG_NAMES.get(code)
    if not name:
        return None, "Geçersiz dil seçimi."
    return name, ""
