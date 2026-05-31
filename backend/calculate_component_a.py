#!/usr/bin/env python3
"""
Componente A (20%) — rúbrica oficial de la maestra:

    Componente A — Preparation, Participation & Attendance (20%)
    ├── Preparation   7.5%   (escala 1–6)
    ├── Participation 7.5%   (escala 1–6)
    └── Attendance    5.0%   (manual)

Rúbrica 1–6 (Class Preparation & Participation):
    6 = preparado, contribuye sin dominar, thoughtful, respeta opiniones, activo en grupos
    5 = preparado, comments thoughtful cuando se le llama, contribuye ocasionalmente sin prompt
    4 = generalmente preparado, participa pero domina/divaga/interrumpe/no lee señales
    3 = preparado, NO contribuye voluntariamente, respuestas mínimas, escucha y toma notas
    2 = NO preparado, NO contribuye, no aporta cuando se le llama
    1 = NO preparado, disruptivo, impacto negativo

Lógica de scoring (heurística determinística basada en métricas + calidad):

  PREPARATION (qué tan preparado vino):
    señal principal: calidad de respuestas a preguntas directas del profe
                   + calidad de contribuciones que demuestran dominio del tema
    avg_quality_when_called → score base
        ≥ 4.5 → 6 ; ≥ 4.0 → 5 ; ≥ 3.0 → 4 ; ≥ 2.0 → 3 ; ≥ 1.5 → 2 ; < 1.5 → 1
    si nunca fue llamado/no respondió → 2 (presente pero no demostró preparación)

  PARTICIPATION (frecuencia + iniciativa + dinámica):
    señales: cantidad total de participaciones, % iniciativa propia, calidad
    frecuencia: alta (≥30) / media (10-29) / baja (1-9) / nula (0)
    iniciativa: % voluntary (vol_resp + question + comment) sobre total
    Lógica:
      0 part. → 1
      1-4 part. → 2
      5-9 part., iniciativa < 30% → 3
      10+ part., iniciativa < 30% → 3 (preparado pero pasivo)
      10+ part., iniciativa 30-60%, calidad ≥ 4 → 5
      30+ part., iniciativa ≥ 50%, calidad ≥ 4 → 6
      30+ part., iniciativa ≥ 70% pero calidad ≤ 3.5 → 4 (domina sin sustancia)

Fórmula final:
    prep_pts = (score_prep / 6) * 7.5
    part_pts = (score_part / 6) * 7.5
    att_pts  = attendance_overrides[student] (default 5.0)
    total_A  = prep_pts + part_pts + att_pts   (sobre 20)
"""

import json
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSION_DIR = REPO_ROOT / "data" / "clases" / "2026-04-07"
CACHE_DIR = SESSION_DIR / "transcript_cache"
EVALS_FILE = SESSION_DIR / "ai_evaluations.json"
ATTENDANCE_FILE = SESSION_DIR / "attendance.json"
OUTPUT_FILE = SESSION_DIR / "component_a_grades.json"

GRADE_TO_NUM = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
PREP_WEIGHT, PART_WEIGHT, ATT_WEIGHT = 7.5, 7.5, 5.0
STUDENT_TYPES = {"student_response", "student_question", "student_comment"}
EXCLUDED_SPEAKERS = {"UNKNOWN", "ILEANG", "ILEANA", ""}


# ─── Reconstruir participaciones en el mismo orden que evaluate_with_ai.py ───
def load_participations():
    parts = []
    for f in sorted(CACHE_DIR.glob("block_*.json")):
        with open(f, encoding="utf-8") as fh:
            block = json.load(fh)
        utterances = block.get("utterances", [])
        for u in utterances:
            sp = u.get("speaker", "")
            if u.get("type") not in STUDENT_TYPES or sp in EXCLUDED_SPEAKERS:
                continue
            parts.append({
                "id": len(parts) + 1,
                "speaker": sp,
                "type": u["type"],
                "text": u.get("text", ""),
                "block": block["block"],
            })
    return parts


def load_evaluations():
    with open(EVALS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return {e["id"]: e["grade"] for e in data.get("evaluations", [])}


def load_attendance():
    if ATTENDANCE_FILE.exists():
        with open(ATTENDANCE_FILE) as f:
            return json.load(f)
    return {}


# ─── Cálculo de scores 1–6 según la rúbrica ─────────────────────────────────
def score_preparation(metrics):
    """Score 1–6 basado en respuestas a preguntas directas del profe."""
    rt = metrics["responses_when_called"]
    if not rt:
        return 2, "Presente pero nunca demostró preparación al ser llamado"
    avg = sum(rt) / len(rt)
    if avg >= 4.5:
        return 6, f"Respuestas thoughtful y profundas (avg {avg:.2f}/5, n={len(rt)})"
    if avg >= 4.0:
        return 5, f"Comments thoughtful cuando se le llamó (avg {avg:.2f}/5, n={len(rt)})"
    if avg >= 3.0:
        return 4, f"Generalmente preparado, calidad media-alta (avg {avg:.2f}/5, n={len(rt)})"
    if avg >= 2.0:
        return 3, f"Preparado pero respuestas mínimas (avg {avg:.2f}/5, n={len(rt)})"
    if avg >= 1.5:
        return 2, f"Poco preparado al ser llamado (avg {avg:.2f}/5, n={len(rt)})"
    return 1, f"No preparado (avg {avg:.2f}/5, n={len(rt)})"


def score_participation(metrics):
    """Score 1–6 basado en frecuencia, iniciativa y calidad de contribución."""
    total = metrics["total"]
    voluntary = metrics["voluntary_count"]
    pct_vol = (voluntary / total * 100) if total else 0
    avg_all = metrics["avg_quality_all"]

    if total == 0:
        return 1, "No participó en clase"
    if total <= 4:
        return 2, f"Participación muy baja ({total} contribuciones, no aporta usefully)"
    if total <= 9 and pct_vol < 30:
        return 3, f"Pasivo: solo {total} part., {pct_vol:.0f}% por iniciativa"
    if pct_vol < 30:
        return 3, f"Preparado pero pasivo: {total} part. pero solo {pct_vol:.0f}% iniciativa"
    if total >= 30 and pct_vol >= 70 and avg_all <= 3.5:
        return 4, f"Domina la conversación pero sin sustancia ({total} part., {pct_vol:.0f}% iniciativa, avg {avg_all:.2f})"
    if total >= 30 and pct_vol >= 50 and avg_all >= 4.0:
        return 6, f"Contribuye readily sin dominar, thoughtful ({total} part., {pct_vol:.0f}% iniciativa, avg {avg_all:.2f})"
    if total >= 10 and pct_vol >= 30 and avg_all >= 4.0:
        return 5, f"Contribuye ocasionalmente sin prompt, thoughtful ({total} part., {pct_vol:.0f}% iniciativa, avg {avg_all:.2f})"
    if total >= 10 and pct_vol >= 30:
        return 4, f"Participa activo, calidad media ({total} part., {pct_vol:.0f}% iniciativa, avg {avg_all:.2f})"
    return 3, f"Participación moderada ({total} part., {pct_vol:.0f}% iniciativa, avg {avg_all:.2f})"


# ─── Main ───────────────────────────────────────────────────────────────────
parts = load_participations()
evals = load_evaluations()
attendance = load_attendance()

per_student = defaultdict(lambda: {
    "responses_when_called": [],   # student_response
    "voluntary_responses": [],     # NO existe en transcript_cache, va vacío
    "questions": [],
    "comments": [],
})

for p in parts:
    grade_letter = evals.get(p["id"])
    if grade_letter not in GRADE_TO_NUM:
        continue
    n = GRADE_TO_NUM[grade_letter]
    s = p["speaker"]
    t = p["type"]
    if t == "student_response":
        per_student[s]["responses_when_called"].append(n)
    elif t == "student_question":
        per_student[s]["questions"].append(n)
    elif t == "student_comment":
        per_student[s]["comments"].append(n)

results = {}
for student, d in per_student.items():
    rt = d["responses_when_called"]
    qs = d["questions"]
    cm = d["comments"]
    voluntary = qs + cm
    all_grades = rt + qs + cm
    total = len(all_grades)
    metrics = {
        "responses_when_called": rt,
        "voluntary_count": len(voluntary),
        "total": total,
        "avg_quality_all": (sum(all_grades) / total) if total else 0,
        "avg_quality_voluntary": (sum(voluntary) / len(voluntary)) if voluntary else 0,
    }

    prep_score, prep_reason = score_preparation(metrics)
    part_score, part_reason = score_participation(metrics)

    prep_pts = round((prep_score / 6) * PREP_WEIGHT, 2)
    part_pts = round((part_score / 6) * PART_WEIGHT, 2)
    att_pts = float(attendance.get(student, ATT_WEIGHT))
    total_a = round(prep_pts + part_pts + att_pts, 2)

    results[student] = {
        "preparation": {
            "score_1_6": prep_score,
            "rationale": prep_reason,
            "n_responses_when_called": len(rt),
            "avg_quality_when_called": round(sum(rt) / len(rt), 2) if rt else None,
            "points_obtained": prep_pts,
            "points_max": PREP_WEIGHT,
        },
        "participation": {
            "score_1_6": part_score,
            "rationale": part_reason,
            "total_participations": total,
            "voluntary_count": len(voluntary),
            "pct_voluntary": round((len(voluntary) / total * 100) if total else 0, 1),
            "avg_quality_all": round(metrics["avg_quality_all"], 2),
            "points_obtained": part_pts,
            "points_max": PART_WEIGHT,
        },
        "attendance": {
            "points_obtained": att_pts,
            "points_max": ATT_WEIGHT,
            "source": "manual_override" if student in attendance else "default",
        },
        "component_a_total": total_a,
        "component_a_max": 20.0,
        "percent_of_a_obtained": round((total_a / 20.0) * 100, 1),
    }

output = {
    "rubric": {
        "component": "A",
        "name": "Student's Preparation, Participation & Attendance",
        "weight_in_total_grade": "20%",
        "subcomponents": {
            "preparation":   {"weight": "7.5%", "scale": "1–6 holistic"},
            "participation": {"weight": "7.5%", "scale": "1–6 holistic"},
            "attendance":    {"weight": "5.0%", "scale": "manual"},
        },
        "rubric_levels": {
            "6": "Comes prepared. Contributes readily without dominating. Thoughtful, advances conversation. Respects others. Active in small groups.",
            "5": "Comes prepared, thoughtful when called. Contributes occasionally without prompting. Respectful, active in small groups.",
            "4": "Generally prepared. Participates but may dominate, ramble, interrupt with digressive questions, bluff when unprepared.",
            "3": "Comes prepared. Does NOT voluntarily contribute. Minimal answers when called. Listens attentively, takes notes.",
            "2": "Comes to class but NOT prepared. Does not contribute. Unable to contribute usefully when called.",
            "1": "Comes but NOT prepared. May be disruptive. Negative impact on group.",
        },
    },
    "students": dict(sorted(results.items(), key=lambda x: x[1]["component_a_total"], reverse=True)),
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# ── Reporte por consola ──
print("=" * 78)
print("  COMPONENTE A — Preparation (7.5) + Participation (7.5) + Attendance (5)")
print("  Escala holística 1–6 (rúbrica oficial maestra)")
print("=" * 78)
for student, r in output["students"].items():
    p, pa, a = r["preparation"], r["participation"], r["attendance"]
    print(f"\n📚 {student}")
    print(f"   PREPARATION   score {p['score_1_6']}/6 → {p['points_obtained']:>5.2f}/{p['points_max']:.1f}")
    print(f"     {p['rationale']}")
    print(f"   PARTICIPATION score {pa['score_1_6']}/6 → {pa['points_obtained']:>5.2f}/{pa['points_max']:.1f}")
    print(f"     {pa['rationale']}")
    src = "(manual)" if a["source"] == "manual_override" else "(default)"
    print(f"   ATTENDANCE    {a['points_obtained']:>5.2f}/{a['points_max']:.1f} {src}")
    print(f"   ─────────────────────────────────")
    print(f"   COMPONENTE A: {r['component_a_total']:>5.2f}/20  ({r['percent_of_a_obtained']}%)")

print(f"\n✅ Guardado: {OUTPUT_FILE.relative_to(REPO_ROOT)}")
print(f"   Para asistencia manual edita: {ATTENDANCE_FILE.relative_to(REPO_ROOT)}")
print(f'   (formato: {{"Aryang": 5.0, "Mega": 0.0, ...}})')
