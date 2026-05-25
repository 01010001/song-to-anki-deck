let selectedSong = null;
let sourceLangSelect = null;
let targetLangSelect = null;

function initTomSelect(selectId, customInputId) {
    const el = document.getElementById(selectId);
    const custom = document.getElementById(customInputId);
    if (!el || typeof TomSelect === "undefined") return null;

    const ts = new TomSelect(el, {
        create: false,
        maxOptions: 200,
        allowEmptyOption: false,
        placeholder: "Dil ara veya seç...",
        onChange(value) {
            if (custom) {
                custom.classList.toggle("hidden", value !== "other");
                if (value === "other") custom.focus();
            }
        },
    });

    if (custom) custom.classList.toggle("hidden", ts.getValue() !== "other");
    return ts;
}

function getLangValue(tomSelect, customInputId) {
    const code = tomSelect ? tomSelect.getValue() : "";
    const custom = document.getElementById(customInputId);
    return {
        code,
        custom: code === "other" && custom ? custom.value : "",
    };
}

function initSearchPage() {
    const searchBtn = document.getElementById("searchBtn");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const queryInput = document.getElementById("searchQuery");
    if (!searchBtn) return;

    sourceLangSelect = initTomSelect("sourceLang", "sourceLangCustom");
    targetLangSelect = initTomSelect("targetLang", "targetLangCustom");

    searchBtn.addEventListener("click", doSearch);
    queryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") doSearch();
    });
    analyzeBtn.addEventListener("click", doAnalyze);
}

async function doSearch() {
    const query = document.getElementById("searchQuery").value;
    const errorEl = document.getElementById("searchError");
    const listEl = document.getElementById("resultsList");
    const analyzeBtn = document.getElementById("analyzeBtn");

    errorEl.classList.add("hidden");
    listEl.innerHTML = "";
    analyzeBtn.classList.add("hidden");
    selectedSong = null;

    const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
    });
    const data = await res.json();

    if (!res.ok) {
        errorEl.textContent = data.error || "Arama başarısız.";
        errorEl.classList.remove("hidden");
        return;
    }

    if (!data.results || data.results.length === 0) {
        errorEl.textContent = "Sonuç bulunamadı.";
        errorEl.classList.remove("hidden");
        return;
    }

    data.results.forEach((song) => {
        const li = document.createElement("li");
        li.textContent = `${song.artist} — ${song.title}`;
        li.addEventListener("click", () => selectSong(li, song));
        listEl.appendChild(li);
    });
}

function selectSong(li, song) {
    document.querySelectorAll("#resultsList li").forEach((el) => el.classList.remove("selected"));
    li.classList.add("selected");
    selectedSong = song;
    document.getElementById("analyzeBtn").classList.remove("hidden");
}

async function doAnalyze() {
    if (!selectedSong) return;

    const statusEl = document.getElementById("analyzeStatus");
    const errorEl = document.getElementById("searchError");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const src = getLangValue(sourceLangSelect, "sourceLangCustom");
    const tgt = getLangValue(targetLangSelect, "targetLangCustom");

    statusEl.textContent = "Sözler çekiliyor ve LLM analiz ediyor... (biraz sürebilir)";
    statusEl.classList.remove("hidden");
    errorEl.classList.add("hidden");
    analyzeBtn.disabled = true;

    const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            artist: selectedSong.artist,
            title: selectedSong.title,
            source_lang: src.code,
            target_lang: tgt.code,
            source_lang_custom: src.custom,
            target_lang_custom: tgt.custom,
        }),
    });

    analyzeBtn.disabled = false;
    statusEl.classList.add("hidden");

    const data = await res.json();
    if (!res.ok) {
        errorEl.textContent = data.error || "Analiz başarısız.";
        errorEl.classList.remove("hidden");
        return;
    }

    window.location.href = data.redirect || `/song/${data.song_id}`;
}

function initSongPage(songId, showRomaji) {
    const exportBtn = document.getElementById("exportBtn");
    const modal = document.getElementById("editModal");
    const form = document.getElementById("editCardForm");
    let editingRow = null;

    if (exportBtn) {
        exportBtn.addEventListener("click", async () => {
            const errorEl = document.getElementById("exportError");
            errorEl.classList.add("hidden");
            const res = await fetch(`/api/songs/${songId}/export`, { method: "POST" });
            if (!res.ok) {
                const data = await res.json();
                errorEl.textContent = data.error || "İndirme başarısız.";
                errorEl.classList.remove("hidden");
                return;
            }
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "sarki_destesi.apkg";
            a.click();
            URL.revokeObjectURL(url);
        });
    }

    document.querySelectorAll(".btn-edit").forEach((btn) => {
        btn.addEventListener("click", () => {
            editingRow = btn.closest("tr");
            const cardId = editingRow.dataset.cardId;
            document.getElementById("editCardId").value = cardId;
            document.getElementById("editFront").value = editingRow.querySelector(".cell-front").textContent.trim();
            document.getElementById("editBack").value = editingRow.querySelector(".cell-back").textContent.trim();
            const romajiEl = document.getElementById("editRomaji");
            if (romajiEl) {
                const r = editingRow.querySelector(".cell-romaji");
                romajiEl.value = r ? r.textContent.trim().replace("—", "") : "";
            }
            const diff = editingRow.querySelector(".cell-diff .badge").textContent.trim();
            document.getElementById("editDifficulty").value = diff;
            document.getElementById("editError").classList.add("hidden");
            modal.classList.remove("hidden");
        });
    });

    document.getElementById("editCancel").addEventListener("click", () => {
        modal.classList.add("hidden");
        editingRow = null;
    });

    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.classList.add("hidden");
        }
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const cardId = document.getElementById("editCardId").value;
        const payload = {
            front: document.getElementById("editFront").value,
            back: document.getElementById("editBack").value,
            difficulty: document.getElementById("editDifficulty").value,
        };
        const romajiEl = document.getElementById("editRomaji");
        if (romajiEl) payload.romaji = romajiEl.value;

        const errEl = document.getElementById("editError");
        errEl.classList.add("hidden");

        const res = await fetch(`/api/songs/${songId}/cards/${cardId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            errEl.textContent = data.error || "Kaydedilemedi.";
            errEl.classList.remove("hidden");
            return;
        }

        const c = data.card;
        editingRow.querySelector(".cell-front").textContent = c.front;
        editingRow.querySelector(".cell-back").textContent = c.back;
        if (showRomaji) {
            editingRow.querySelector(".cell-romaji").textContent = c.romaji || "—";
        }
        editingRow.querySelector(".cell-diff .badge").textContent = c.difficulty;
        modal.classList.add("hidden");
    });
}
