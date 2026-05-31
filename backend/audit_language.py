#!/usr/bin/env python3
"""
Auditoría de idioma / contenido ajeno por clase y por bloque.

La clase es un seminario EN INGLÉS (GTC/ICP). Este script detecta:
  - Densidad de español por bloque (palabras función inequívocas del español)
  - Bloques sospechosos de contener una grabación ajena (alta densidad ES)

Uso:
    python3 backend/audit_language.py
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "clases"

# Palabras función del español que NO existen en inglés (o son rarísimas).
# Evitamos falsos positivos como "no", "a", "me", "son" (sun?), "the" etc.
SPANISH_MARKERS = {
    "que", "qué", "porque", "está", "están", "esto", "esta", "este", "eso",
    "pero", "también", "entonces", "ahora", "muy", "para", "cómo", "dónde",
    "cuándo", "hacer", "tiene", "tienes", "nosotros", "ustedes", "verdad",
    "señor", "señora", "gracias", "claro", "bueno", "entonces", "porqué",
    "según", "través", "además", "aquí", "allá", "ahí", "puedes", "puede",
    "vamos", "estoy", "estás", "somos", "quiero", "quieres", "hay",
    "más", "así", "sí", "todo", "todos", "nada", "algo", "alguien",
    "mucho", "poco", "siempre", "nunca", "porfavor", "favor", "ojalá",
    "facturación", "factura", "régimen", "honorarios", "pesos", "berrinche",
    "divorcio", "abogado", "hijo", "esposa", "esposo",
}

# Términos privados/financieros que jamás deberían estar en una clase pública.
PRIVATE_FLAGS = re.compile(
    r"\b(factura|facturaci[oó]n|r[eé]gimen|honorarios|RFC|SAT|INE|"
    r"berrinche|divorci|abogad|deposit[oa]|transferenci|n[oó]mina|"
    r"pesos|hijo adolescente|tu hijo|mi esposa|mi esposo)\b",
    re.IGNORECASE,
)

WORD_RE = re.compile(r"[a-záéíóúñü]+", re.IGNORECASE)


def audit_class(session_dir):
    analysis = json.loads((session_dir / "analysis.json").read_text(encoding="utf-8"))
    ft = analysis.get("full_transcription", [])

    by_block = {}
    for u in ft:
        b = u.get("block", 0)
        by_block.setdefault(b, []).append(u.get("text", ""))

    flagged = []
    total_words = 0
    total_es = 0
    private_hits = []

    for b in sorted(by_block):
        text = " ".join(by_block[b])
        words = [w.lower() for w in WORD_RE.findall(text)]
        n = len(words)
        es = sum(1 for w in words if w in SPANISH_MARKERS)
        total_words += n
        total_es += es
        density = (es / n * 100) if n else 0
        # Bloque sospechoso: densidad ES alta y con suficiente texto
        if density >= 8 and n >= 30:
            sample = text[:160].replace("\n", " ")
            flagged.append((b, n, es, density, sample))
        for m in PRIVATE_FLAGS.finditer(text):
            ctx_start = max(0, m.start() - 50)
            private_hits.append((b, text[ctx_start:m.end() + 50].replace("\n", " ")))

    overall = (total_es / total_words * 100) if total_words else 0
    return {
        "session": session_dir.name,
        "total_words": total_words,
        "overall_es_pct": overall,
        "flagged_blocks": flagged,
        "private_hits": private_hits,
        "n_blocks": len(by_block),
    }


def main():
    sessions = sorted(d for d in DATA_DIR.iterdir() if d.is_dir())
    print(f"{'='*78}")
    print(f"  AUDITORÍA DE IDIOMA / CONTENIDO AJENO — {len(sessions)} clases")
    print(f"{'='*78}\n")

    for sd in sessions:
        if not (sd / "analysis.json").exists():
            continue
        r = audit_class(sd)
        status = "✅" if r["overall_es_pct"] < 2 and not r["flagged_blocks"] and not r["private_hits"] else "⚠️"
        print(f"{status} {r['session']}  ·  {r['total_words']} palabras  ·  "
              f"{r['n_blocks']} bloques  ·  ES global: {r['overall_es_pct']:.2f}%")
        if r["flagged_blocks"]:
            print(f"   🚩 Bloques con alta densidad de español:")
            for b, n, es, dens, sample in r["flagged_blocks"]:
                print(f"      block {b:02d}: {dens:.1f}% ES ({es}/{n})  → «{sample}…»")
        if r["private_hits"]:
            print(f"   🔴 Posible contenido privado:")
            for b, ctx in r["private_hits"][:8]:
                print(f"      block {b}: …{ctx}…")
        print()


if __name__ == "__main__":
    main()
