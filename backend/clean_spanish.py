#!/usr/bin/env python3
"""
Elimina utterances en español del transcript_cache de una clase.

La clase es un seminario EN INGLÉS. Cualquier intervención en español proviene
de una conversación ajena que se coló en la grabación → se elimina.

El cache (block_NN.json) es la fuente canónica: score_with_rubric.py y
build_component_a.py reconstruyen los IDs desde ahí. Tras limpiar, hay que
re-correr el pipeline (process_class --skip-transcription) para propagar.

Uso:
    python3 backend/clean_spanish.py <session_id> [--apply]
    (sin --apply = dry-run, solo muestra qué eliminaría)
"""

import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "clases"

from langdetect import detect, LangDetectException, DetectorFactory
DetectorFactory.seed = 0  # determinismo

# Palabras cortas inequívocamente españolas (para utterances <4 palabras donde
# langdetect no es confiable). NO incluye homógrafos del inglés ("no", "si", "okay").
SHORT_ES = {
    "sí", "pero", "qué", "cómo", "dónde", "cuándo", "hola", "gracias", "claro",
    "bueno", "entonces", "también", "tambien", "aquí", "aqui", "ahí", "ahi",
    "allá", "ahora", "eso", "esto", "esta", "este", "nada", "más", "mas", "muy",
    "oye", "mira", "pues", "verdad", "señor", "señora", "cosa", "ya",
    "quiero", "creo", "vamos", "voy", "porque", "según", "está", "están",
}
# Palabras-función del español (señal de que HAY español). Se usan SOLO como
# gate: para texto largo se exige además que langdetect confirme 'es', así una
# frase puramente inglesa (sin ninguna de estas) jamás se marca por error.
SPANISH_FUNCTION = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "del", "de", "que",
    "qué", "y", "en", "es", "está", "están", "esto", "esta", "este", "esos",
    "esas", "eso", "esa", "ese", "por", "para", "con", "sin", "pero", "como",
    "cómo", "más", "muy", "ya", "uno", "mientras", "porque", "entonces",
    "también", "así", "sí", "donde", "dónde", "cuando", "cuándo", "nos", "le",
    "lo", "se", "su", "sus", "mi", "mis", "tu", "tus", "yo", "él", "ella",
    "nosotros", "ustedes", "ellos", "hacer", "hace", "tiene", "tienen", "hay",
    "caos", "ministerio", "creo", "quiero", "vamos", "voy", "según", "verdad",
}
# Palabras inequívocamente inglesas (sin significado en español). Si aparece
# alguna, la utterance NO es español puro → protege el inglés de falsos positivos.
ENGLISH_UNAMBIG = {
    "the", "is", "are", "was", "were", "be", "been", "being", "to", "of", "and",
    "you", "your", "yours", "that", "this", "these", "those", "for", "with",
    "what", "when", "where", "which", "who", "whom", "whose", "how", "why",
    "have", "has", "had", "do", "does", "did", "we", "they", "them", "their",
    "he", "she", "his", "her", "it's", "i'm", "you're", "we're", "they're",
    "don't", "doesn't", "didn't", "can't", "won't", "isn't", "aren't", "wasn't",
    "okay", "ok", "yes", "yeah", "yep", "right", "thing", "things", "think",
    "thought", "because", "about", "would", "could", "should", "will", "shall",
    "from", "into", "than", "then", "there", "here", "very", "much", "many",
    "good", "great", "but", "not", "now", "just", "like", "know", "need",
    "want", "make", "made", "say", "said", "see", "saw", "get", "got", "give",
    "go", "going", "come", "came", "take", "look", "work", "use", "first",
    "people", "student", "students", "professor", "teacher", "problem",
    "technology", "market", "research", "question", "answer", "example",
}
WORD_RE = re.compile(r"[a-záéíóúñü']+", re.IGNORECASE)
ES_CHARS = re.compile(r"[áéíóúñ]", re.IGNORECASE)


def is_spanish(text: str) -> bool:
    """True si la utterance está en español.

    Combina: ¿¡ inequívocos · acento+función · señal léxica (palabra-función ES
    sin ninguna palabra inequívocamente inglesa) · langdetect para frases ·
    heurística conservadora para frases muy cortas. SPANISH_FUNCTION no contiene
    homógrafos del inglés, así que su presencia es señal fuerte de español."""
    if not text or not text.strip():
        return False
    words = [w.lower() for w in WORD_RE.findall(text)]
    n = len(words)
    if n == 0:
        return False
    accent = bool(ES_CHARS.search(text))
    es_func = sum(1 for w in words if w in SPANISH_FUNCTION)
    en_unambig = sum(1 for w in words if w in ENGLISH_UNAMBIG)

    # Texto largo → langdetect es fiable (maneja bien el code-switch: una
    # intervención mayormente en inglés con una palabra suelta en español → 'en').
    if n >= 12:
        try:
            return detect(text) == "es"
        except LangDetectException:
            return es_func >= 2 and es_func > en_unambig

    # Texto corto/medio → léxico (langdetect falla en frases cortas).
    # SPANISH_FUNCTION no tiene homógrafos del inglés: su presencia sin ninguna
    # palabra inequívocamente inglesa es señal segura de español.
    if "¿" in text or "¡" in text:
        return en_unambig < 2  # ¿? embebido en frase dominada por inglés → conservar
    if es_func >= 1 and en_unambig == 0:
        return True
    if es_func >= 2 and es_func > en_unambig:
        return True
    if accent and en_unambig == 0:
        return True
    if n < 4 and any(w in SHORT_ES for w in words):
        return True
    return False


def clean_session(sid: str, apply: bool):
    cache = DATA_DIR / sid / "transcript_cache"
    if not cache.exists():
        print(f"❌ No existe cache para {sid}")
        return

    if apply:
        backup = cache.parent / "transcript_cache_backup_es"
        if not backup.exists():
            shutil.copytree(cache, backup)
            print(f"   💾 Respaldo: {backup.relative_to(REPO_ROOT)}")

    removed_samples = []
    kept_total = removed_total = 0
    per_block = {}

    for f in sorted(cache.glob("block_*.json")):
        block = json.loads(f.read_text(encoding="utf-8"))
        utts = block.get("utterances", [])
        new_utts = []
        rm = 0
        for u in utts:
            if is_spanish(u.get("text", "")):
                removed_total += 1
                rm += 1
                if len(removed_samples) < 25:
                    removed_samples.append(
                        f'      [{f.name} · {u.get("speaker","?")}/{u.get("type","?")}] '
                        f'{u.get("text","")[:110]}'
                    )
            else:
                new_utts.append(u)
                kept_total += 1
        if rm:
            per_block[block.get("block", f.name)] = rm
        if apply and rm:
            block["utterances"] = new_utts
            f.write_text(json.dumps(block, indent=2, ensure_ascii=False), encoding="utf-8")

    mode = "APLICADO" if apply else "DRY-RUN"
    print(f"\n{'='*70}")
    print(f"  {mode} — {sid}")
    print(f"{'='*70}")
    print(f"  Utterances: {kept_total} en inglés (conservadas) · "
          f"{removed_total} en español (eliminadas)")
    if per_block:
        print(f"  Por bloque: " + ", ".join(f"b{b}:{n}" for b, n in sorted(per_block.items())))
    if removed_samples:
        print(f"  Muestra de eliminadas:")
        for s in removed_samples:
            print(s)


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 backend/clean_spanish.py <session_id> [--apply]")
        sys.exit(1)
    sid = sys.argv[1]
    apply = "--apply" in sys.argv
    clean_session(sid, apply)


if __name__ == "__main__":
    main()
