import logging

from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for



from app.services import search_service, lyrics_service, llm_service, anki_service

from app.services import song_repository

from app.config.languages import LANGUAGES, resolve_language, is_japanese_source



bp = Blueprint("main", __name__)

logger = logging.getLogger("controller")





@bp.route("/")

def index():

    return render_template("index.html", languages=LANGUAGES)





@bp.route("/api/search", methods=["POST"])

def search():

    data = request.get_json() or {}

    query = (data.get("query") or "").strip()



    ok, msg = search_service.is_valid_search(query)

    if not ok:

        return jsonify({"error": msg}), 400



    try:

        results = search_service.search_songs(query)

        return jsonify({"results": results})

    except Exception as e:

        logger.exception("Arama hatası: %s", e)

        return jsonify({"error": f"Arama hatası: {e}"}), 500





@bp.route("/api/analyze", methods=["POST"])

def analyze():

    data = request.get_json() or {}

    artist = (data.get("artist") or "").strip()

    title = (data.get("title") or "").strip()

    source_lang_code = (data.get("source_lang") or "auto").strip()



    source_lang, err = resolve_language(source_lang_code, data.get("source_lang_custom", ""))

    if err:

        return jsonify({"error": err}), 400



    target_lang_code = (data.get("target_lang") or "tr").strip()

    target_lang, err = resolve_language(target_lang_code, data.get("target_lang_custom", ""))

    if err:

        return jsonify({"error": err}), 400



    if not artist or not title:

        return jsonify({"error": "Sanatçı ve şarkı adı gerekli."}), 400



    lyrics, err = lyrics_service.fetch_lyrics(artist, title)

    if err:

        return jsonify({"error": err}), 400



    cards, err = llm_service.analyze_lyrics(

        lyrics, source_lang, target_lang, source_lang_code=source_lang_code,

    )

    if err:

        return jsonify({"error": err}), 500



    is_ja = is_japanese_source(source_lang_code, source_lang)
    if source_lang_code == "auto":
        is_ja = any(c.get("romaji") for c in cards)

    song = song_repository.save_song(

        artist, title, lyrics,

        source_lang_code, source_lang,

        target_lang_code, target_lang,

        is_ja, cards,

    )

    logger.info("Şarkı kaydedildi: id=%d, %d kart", song.id, len(cards))



    return jsonify({

        "song_id": song.id,

        "redirect": url_for("main.song_page", song_id=song.id),

    })





@bp.route("/song/<int:song_id>")

def song_page(song_id):

    song = song_repository.get_song(song_id)

    if not song:

        return redirect(url_for("main.index"))



    cards = [c.to_dict() for c in song.cards]

    return render_template(

        "analysis.html",

        song_id=song.id,

        lyrics=song.lyrics,

        cards=cards,

        title=song.title,

        artist=song.artist,

        show_romaji=song.source_is_japanese,
        source_lang_name=song.source_lang_name,
        target_lang_name=song.target_lang_name,
        active_song_id=song.id,
    )





@bp.route("/analysis")

def analysis_legacy():

    return redirect(url_for("main.index"))





@bp.route("/api/songs/<int:song_id>/cards/<int:card_id>", methods=["PUT"])

def update_card(song_id, card_id):

    song = song_repository.get_song(song_id)

    if not song:

        return jsonify({"error": "Şarkı bulunamadı."}), 404



    card = next((c for c in song.cards if c.id == card_id), None)

    if not card:

        return jsonify({"error": "Kart bulunamadı."}), 404



    data = request.get_json() or {}

    front = (data.get("front") or "").strip()

    back = (data.get("back") or "").strip()

    romaji = (data.get("romaji") or "").strip()

    difficulty = (data.get("difficulty") or "orta").strip()



    if not front or not back:

        return jsonify({"error": "Ön yüz ve çeviri zorunludur."}), 400

    if song.source_is_japanese and not romaji:

        return jsonify({"error": "Japonca kartlarda romaji zorunludur."}), 400



    updated, err = song_repository.update_card(card_id, front, back, romaji, difficulty)

    if err:

        return jsonify({"error": err}), 404



    return jsonify({"card": updated.to_dict()})





@bp.route("/api/songs/<int:song_id>/export", methods=["POST"])

def export_deck(song_id):

    song = song_repository.get_song(song_id)

    if not song:

        return jsonify({"error": "Şarkı bulunamadı."}), 404



    cards = song_repository.get_cards_for_export(song)

    if not cards:

        return jsonify({"error": "Dışa aktarılacak kart yok."}), 400



    filepath, err = anki_service.create_apkg(

        f"{song.title} - Anki",

        cards,

        require_romaji=song.source_is_japanese,

    )

    if err:

        return jsonify({"error": err}), 400



    return send_file(

        filepath,

        as_attachment=True,

        download_name=f"{song.title.replace(' ', '_')}.apkg",

        mimetype="application/octet-stream",

    )


