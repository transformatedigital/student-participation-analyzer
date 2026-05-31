#!/usr/bin/env python3
"""
Re-scoring de cada utterance directamente contra la rúbrica oficial 1–6 de la maestra,
SIN pasar por el mapeo A–E de Gemini. Lee el texto y aplica criterio alineado con
los descriptores literales:

  6 Thoughtful, advances conversation, prepared, doesn't dominate, respectful
  5 Prepared, thoughtful when called, contributes occasionally without prompting
  4 Generally prepared, may ramble/dominate/digress
  3 Prepared but minimal answers, doesn't voluntarily contribute
  2 Not prepared, can't contribute usefully
  1 Not prepared, disruptive, negative impact

Reglas aplicadas (por utterance):
  · LONGITUD: muy corto (<3 palabras) → mínimo aceptable (2-3)
  · SUSTANCIA: presencia de conectores explicativos ("because", "so", "I think",
    "porque", "creo que", "por ejemplo") → bonifica
  · ANÁLISIS: respuestas que conectan conceptos → 5
  · DETALLE: respuestas largas (>30 palabras) y coherentes → 5-6
  · INAUDIBLE / "I don't know" / "Yeah" / "OK" → 2-3
  · Tipo PREGUNTA: thoughtful question (>10 palabras) → 5; mecánica → 3
  · Tipo COMMENT: depende de profundidad

Output: data/clases/2026-04-07/manual_scores_1_6.json
        formato: { "<id>": <score>, ... }
"""

import json
import re
from pathlib import Path

import os
REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_ID = os.getenv("SESSION_ID", "2026-04-07")
SESSION_DIR = REPO_ROOT / "data" / "clases" / SESSION_ID
CACHE_DIR = SESSION_DIR / "transcript_cache"
EVALS_FILE = SESSION_DIR / "ai_evaluations.json"
OUTPUT_FILE = SESSION_DIR / "manual_scores_1_6.json"

STUDENT_TYPES = {"student_response", "student_question", "student_comment"}
EXCLUDED_SPEAKERS = {"UNKNOWN", "ILEANG", "ILEANA", ""}

SUBSTANTIVE_MARKERS = re.compile(
    r"\b(because|so that|in order|i think|i believe|for example|"
    r"such as|that's why|the reason|porque|creo que|pienso que|por ejemplo|"
    r"es decir|sin embargo|además|también|de hecho|"
    r"how about|what if|why don't|how can|why does|"
    r"connect|relate|relacion|conexión|"
    r"compare|contrast|sin embargo|en cambio)\b",
    re.IGNORECASE,
)
DISMISSIVE = re.compile(
    r"^(yeah|yes|no|ok|okay|sí|si|mm|mmm|hmm|ah|oh|right|claro|exact|exactly)[\s.,!?]*$",
    re.IGNORECASE,
)
INAUDIBLE = re.compile(r"\[inaudible\]|\[unclear|\[no audible|\[unintelligible", re.IGNORECASE)


def count_words(text):
    return len(re.findall(r"\b\w+\b", text or ""))


def has_substance(text):
    return bool(SUBSTANTIVE_MARKERS.search(text or ""))


def is_dismissive(text):
    return bool(DISMISSIVE.match((text or "").strip()))


def is_inaudible(text):
    return bool(INAUDIBLE.search(text or ""))


def score_response(text, gemini_grade):
    """Score 1–6 para una respuesta a pregunta del profe (Preparation).

    La rúbrica habla de cuán preparado viene el alumno. La respuesta es la
    evidencia. Aplico:
      - inaudible/incoherente → 1
      - dismissive ("yeah") → 2
      - muy corto (<5 palabras) sin sustancia → 3 (mínimo when called)
      - 5-15 palabras, sustantivo → 4
      - 15-30 palabras o con conectores → 5 (thoughtful)
      - 30+ palabras y conectores explicativos → 6 (advances conversation)
      - Gemini D/E rebaja un nivel; A puede subir un nivel si texto largo
    """
    if not text or is_inaudible(text):
        return 1
    n = count_words(text)
    sustantivo = has_substance(text)
    dismissive = is_dismissive(text)

    if dismissive and n <= 3:
        score = 2
    elif n < 5:
        score = 3 if sustantivo else 2
    elif n < 15:
        score = 4 if sustantivo else 3
    elif n < 30:
        score = 5 if sustantivo else 4
    else:
        # Respuesta larga
        score = 6 if sustantivo else 5

    # Ajuste por grade Gemini (señal adicional)
    if gemini_grade == "E":
        score = max(1, score - 2)
    elif gemini_grade == "D":
        score = max(2, score - 1)
    elif gemini_grade == "A" and n >= 25 and sustantivo:
        score = min(6, score + 1)

    return score


def score_question(text, gemini_grade):
    """Score 1–6 para pregunta del alumno al profe (Participation).

    Una pregunta thoughtful que abre discusión = 5-6.
    Una pregunta aclaratoria = 3-4.
    Una pregunta mecánica corta = 2-3.
    """
    if not text or is_inaudible(text):
        return 1
    n = count_words(text)
    sustantivo = has_substance(text)

    if n < 4:
        score = 3  # "Can I know?", "Why?" — pregunta mínima
    elif n < 10:
        score = 4 if sustantivo else 3
    elif n < 20:
        score = 5 if sustantivo else 4
    else:
        score = 6 if sustantivo else 5

    if gemini_grade == "E":
        score = max(1, score - 2)
    elif gemini_grade == "D":
        score = max(2, score - 1)
    elif gemini_grade == "A" and n >= 15:
        score = min(6, score + 1)
    return score


def score_comment(text, gemini_grade):
    """Score 1–6 para comentario voluntario (Participation).

    Comment reflexivo largo = 5-6.
    Comment short pero sustantivo = 4.
    Comment de relleno = 2-3.
    """
    if not text or is_inaudible(text):
        return 1
    n = count_words(text)
    sustantivo = has_substance(text)
    dismissive = is_dismissive(text)

    if dismissive:
        score = 2
    elif n < 4:
        score = 3 if sustantivo else 2
    elif n < 10:
        score = 4 if sustantivo else 3
    elif n < 25:
        score = 5 if sustantivo else 4
    else:
        score = 6 if sustantivo else 5

    if gemini_grade == "E":
        score = max(1, score - 2)
    elif gemini_grade == "D":
        score = max(2, score - 1)
    elif gemini_grade == "A" and n >= 20:
        score = min(6, score + 1)
    return score


# Cargar evaluaciones existentes (A-E de Gemini) si existen, como señal adicional
# Para clases nuevas no es obligatorio — el scoring 1-6 se hace contra el texto.
gemini_grades = {}
if EVALS_FILE.exists():
    with open(EVALS_FILE, encoding="utf-8") as f:
        evals_data = json.load(f)
    gemini_grades = {e["id"]: e["grade"] for e in evals_data.get("evaluations", [])}

# Reconstruir parts en mismo orden que evaluate_with_ai.py
parts = []
for f in sorted(CACHE_DIR.glob("block_*.json")):
    with open(f, encoding="utf-8") as fh:
        block = json.load(fh)
    for u in block.get("utterances", []):
        sp = u.get("speaker", "")
        if u.get("type") not in STUDENT_TYPES or sp in EXCLUDED_SPEAKERS:
            continue
        parts.append({
            "id": len(parts) + 1,
            "speaker": sp.title(),
            "type": u["type"],
            "text": u.get("text", ""),
        })

scores = {}
distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

for p in parts:
    g = gemini_grades.get(p["id"], "C")
    if p["type"] == "student_response":
        s = score_response(p["text"], g)
    elif p["type"] == "student_question":
        s = score_question(p["text"], g)
    else:  # student_comment
        s = score_comment(p["text"], g)
    scores[str(p["id"])] = s
    distribution[s] += 1

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(scores, f, indent=2)

print("=" * 60)
print("RE-SCORING CON RÚBRICA 1–6 (criterio de la maestra)")
print("=" * 60)
print(f"\nTotal utterances evaluados: {len(parts)}")
print(f"\nDistribución de scores:")
for lvl in (6, 5, 4, 3, 2, 1):
    n = distribution[lvl]
    pct = (n / len(parts) * 100) if parts else 0
    bar = "█" * int(pct / 2)
    print(f"  {lvl}: {n:>3}  ({pct:>4.1f}%)  {bar}")

# Comparativa con mapeo viejo
print(f"\nComparación con mapeo viejo (A→5, B→4, C→3, D→2, E→1):")
old_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
old_map = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
for p in parts:
    g = gemini_grades.get(p["id"], "C")
    old_dist[old_map.get(g, 3)] += 1

print(f"  {'Lvl':>3}  {'Viejo':>6}  {'Nuevo':>6}  Diff")
for lvl in (6, 5, 4, 3, 2, 1):
    diff = distribution[lvl] - old_dist[lvl]
    sign = "+" if diff > 0 else ""
    print(f"  {lvl:>3}  {old_dist[lvl]:>6}  {distribution[lvl]:>6}  {sign}{diff}")

print(f"\n✅ Scores guardados: {OUTPUT_FILE.relative_to(REPO_ROOT)}")
print(f"   Para aplicarlos, vuelve a correr: python3 backend/build_component_a.py")
