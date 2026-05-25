# Şarkı Sözlerinden Anki Kartları

Yabancı dil öğrenenler için şarkı sözlerinden LLM (Gemini) yardımıyla Anki destesi (.apkg) oluşturan web uygulaması.

## Özellikler

- Şarkı arama (iTunes API)
- Şarkı sözü çekme (7 kaynak sırayla: LRCLIB, lyrics.ovh, ChartLyrics, …)
- Gemini ile kelime/cümle analizi ve çeviri
- Anki .apkg dosyası indirme

## Kurulum

```bash
cd "proje kodu"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

`.env.example` dosyasını `.env` olarak kopyalayın ve Gemini API anahtarınızı ekleyin:

```
GEMINI_API_KEY=your_key_here
```

Anahtar: https://aistudio.google.com/apikey

Ücretsiz planda `.env` örneği (Gemini 3 free tier):
```
GEMINI_MODEL=gemini-3.1-flash-lite
```
Alternatifler: `gemini-3.5-flash`, `gemini-3.1-flash-lite-preview`. `gemini-3.1-pro-preview` ücretsiz değildir.
`limit: 0` hatası alırsanız AI Studio'da faturalandırma bağlamanız gerekebilir.

## Çalıştırma

```bash
python run.py
```

Tarayıcıda: http://127.0.0.1:5000

Veriler `data/app.db` SQLite dosyasında saklanır. Sol panelde geçmiş şarkılar listelenir.

Komut satırında her API adımı `[DEBUG]` / `[INFO]` satırlarıyla loglanır (arama, söz çekme, Gemini, export). Log seviyesi `.env` içinde `LOG_LEVEL=DEBUG` ile ayarlanır.

## Mimari (MVC)

- **Model:** `app/models/` — Song, FlashCard, AnkiDeck
- **View:** `app/templates/`, `app/static/`
- **Controller:** `app/controllers/main_controller.py`
- **Servisler:** `app/services/` — API entegrasyonları

## Test

Kara kutu testleri (`tests/test_blackbox.py`):

```bash
python -m pytest tests/test_blackbox.py -v
```

Tüm testler:

```bash
python -m pytest tests/ -v
```
