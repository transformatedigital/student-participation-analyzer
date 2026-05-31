#!/usr/bin/env python3
"""Genera dashboard interactivo de evaluación de clase — 7 Abril 2026"""

import json
from pathlib import Path
from collections import defaultdict

cache_dir   = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/transcript_cache")
analysis_f  = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis.json")
ai_evals_f  = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/ai_evaluations.json")
output_f    = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/dashboard.html")

# ── Cargar bloques ────────────────────────────────────────────────────────────
all_blocks = []
for f in sorted(cache_dir.glob("block_*.json")):
    with open(f, encoding="utf-8") as fh:
        all_blocks.append(json.load(fh))

with open(analysis_f, encoding="utf-8") as fh:
    analysis = json.load(fh)

# Load AI evaluations
ai_evals = {}
if ai_evals_f.exists():
    with open(ai_evals_f, encoding="utf-8") as fh:
        ai_data = json.load(fh)
    ai_evals = {str(e["id"]): e for e in ai_data.get("evaluations", [])}
print(f"✅ AI evaluations loaded: {len(ai_evals)}")

# Gemini scores index
gemini_scores = {}
for q in analysis.get("teacher_questions", []):
    r = q.get("student_response", {})
    if r.get("student") and r.get("quality_score"):
        k = r["student"].upper().replace(" ", "") + "_" + q.get("timestamp", "")
        gemini_scores[k] = r["quality_score"]
for c in analysis.get("student_contributions", []):
    if c.get("student") and c.get("quality_score"):
        k = c["student"].upper().replace(" ", "") + "_" + c.get("timestamp", "")
        gemini_scores[k] = c["quality_score"]

# ── Extraer participaciones ───────────────────────────────────────────────────
STUDENT_TYPES = {"student_response", "student_question", "student_comment"}
participations = []

for block in all_blocks:
    utterances = block.get("utterances", [])
    bnum = block["block"]
    for i, u in enumerate(utterances):
        sp = u.get("speaker", "")
        if u["type"] not in STUDENT_TYPES or sp in ("UNKNOWN", "ILEANG", ""):
            continue
        context = ""
        for j in range(i - 1, max(-1, i - 6), -1):
            if utterances[j]["type"] in ("teacher_statement", "teacher_question"):
                context = utterances[j].get("text", "")[:250]
                break
        ts = u.get("timestamp_abs", u.get("timestamp", ""))
        gk = sp.replace(" ", "") + "_" + ts
        pid = len(participations) + 1
        ai_ev = ai_evals.get(str(pid), {})
        participations.append({
            "id": pid,
            "block": bnum,
            "timestamp": ts,
            "speaker": sp,
            "type": u["type"],
            "text": u.get("text", ""),
            "context": context,
            "gemini_score": gemini_scores.get(gk, ""),
            "ai_grade": ai_ev.get("grade", ""),
            "ai_rationale": ai_ev.get("rationale", ""),
        })

# ── Student stats ─────────────────────────────────────────────────────────────
STUDENTS_ORDER = ["ARYANG", "GRACE", "STHEPEN", "CHILAKA", "MEGA"]
COLORS = {"ARYANG": "#e05555", "GRACE": "#9b6bd4", "STHEPEN": "#3aada8", "CHILAKA": "#e0a030", "MEGA": "#4a90d9"}
NAMES  = {"ARYANG": "Aryang", "GRACE": "Grace", "STHEPEN": "Sthepen", "CHILAKA": "Chilaka", "MEGA": "Mega"}

by_student = {}
for sp in STUDENTS_ORDER:
    parts = [p for p in participations if p["speaker"] == sp]
    by_student[sp] = {
        "total": len(parts),
        "responses": sum(1 for p in parts if p["type"] == "student_response"),
        "questions":  sum(1 for p in parts if p["type"] == "student_question"),
        "comments":   sum(1 for p in parts if p["type"] == "student_comment"),
        "parts": parts,
    }

total_parts   = len(participations)
total_teacher = sum(
    sum(1 for u in b.get("utterances", []) if u["type"] == "teacher_question")
    for b in all_blocks
)

# ── HTML helpers ──────────────────────────────────────────────────────────────
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def badge(t):
    m = {"student_response": ("badge-resp", "Response"),
         "student_question":  ("badge-q",    "Question"),
         "student_comment":   ("badge-comm", "Comment")}
    cls, lbl = m.get(t, ("badge-comm", t))
    return f'<span class="badge {cls}">{lbl}</span>'

GRADE_SCALE = [("A", "Excellent"), ("B", "Good"), ("C", "Satisfactory"),
               ("D", "Insufficient"), ("E", "Deficient")]

def grade_buttons(pid):
    btns = []
    for g, lbl in GRADE_SCALE:
        onclick = "gradeCard(" + str(pid) + ",'" + g + "')"
        btns.append(
            '<button class="gbtn gbtn-' + g + '" onclick="' + onclick +
            '" title="' + lbl + '">' + g + '</button>'
        )
    return "".join(btns)

# ── Build student panels ──────────────────────────────────────────────────────
tabs_html   = ""
panels_html = ""

for sp in STUDENTS_ORDER:
    info = by_student[sp]
    if info["total"] == 0:
        continue
    color = COLORS[sp]
    name  = NAMES[sp]

    tabs_html += (
        '<button class="stab" data-student="' + sp +
        '" onclick="showStudent(\'' + sp + '\')" style="--sc:' + color + '">' +
        name + ' <span class="stab-count">' + str(info["total"]) + '</span></button>'
    )

    cards = ""
    for p in info["parts"]:
        ctx_html = ""
        if p["context"]:
            ctx_html = (
                '<div class="ctx"><span class="ctx-label">Ileana\'s context:</span> ' +
                esc(p["context"]) + "</div>"
            )
        ai_html = ""
        if p["gemini_score"]:
            ai_html = '<span class="ai-score">IA: ' + p["gemini_score"] + "</span>"

        if p["type"] == "student_response":
            rubric_tag = '<span class="rubric-indicator rubric-indicator-resp">Rubric A</span>'
        else:
            rubric_tag = '<span class="rubric-indicator rubric-indicator-part">Rubric B</span>'

        cards += (
            '<div class="pcard" id="pcard-' + str(p["id"]) +
            '" data-id="' + str(p["id"]) + '" data-student="' + sp + '">'
            '<div class="pcard-top">'
            '<span class="pcard-ts">⏱ ' + p["timestamp"] + "</span>" +
            badge(p["type"]) +
            rubric_tag +
            '<span class="pcard-block">B' + str(p["block"]).zfill(2) + "</span>"
            '<span class="pcard-score" id="score-label-' + str(p["id"]) + '">' +
            ai_html + "</span></div>" +
            ctx_html +
            '<div class="pcard-text">' + esc(p["text"]) + "</div>"
            '<div class="pcard-grade"><span class="grade-label">Grade:</span>' +
            grade_buttons(p["id"]) + "</div></div>"
        )

    panels_html += (
        '<div class="spanel" id="spanel-' + sp + '" style="display:none">'
        '<div class="spanel-header" style="border-color:' + color + '">'
        '<span class="spanel-name" style="color:' + color + '">' + name + "</span>"
        '<div class="spanel-stats">'
        "<span>💬 " + str(info["total"]) + " participations</span>"
        "<span>↩ " + str(info["responses"]) + " responses</span>"
        "<span>❓ " + str(info["questions"]) + " questions</span>"
        "<span>💡 " + str(info["comments"]) + " comments</span>"
        "</div>"
        '<div class="spanel-avg">Average: <span id="avg-' + sp + '" class="avg-val">—</span></div>'
        "</div>"
        '<div class="pcards-list" id="cards-' + sp + '">' + cards + "</div>"
        "</div>"
    )

# ── AI Evaluation tab HTML ────────────────────────────────────────────────────
GRADE_COLOR = {"A": "#3ada8a", "B": "#6496e8", "C": "#d4b030", "D": "#e07840", "E": "#e04040"}
GRADE_BG    = {"A": "#1a3a2a", "B": "#1a2a3a", "C": "#2a2a0a", "D": "#2a1a0a", "E": "#2a0a0a"}
GRADE_LABEL = {"A": "Excellent", "B": "Good", "C": "Satisfactory", "D": "Insufficient", "E": "Deficient"}
PTS_MAP     = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}

def ai_letter(avg):
    if avg >= 4.5: return "A"
    if avg >= 3.5: return "B"
    if avg >= 2.5: return "C"
    if avg >= 1.5: return "D"
    return "E"

# Per-student AI summary
ai_by_student = {}
for sp in STUDENTS_ORDER:
    sp_parts = [p for p in participations if p["speaker"] == sp and p.get("ai_grade")]
    pts = [PTS_MAP[p["ai_grade"]] for p in sp_parts]
    dist = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    for p in sp_parts:
        dist[p["ai_grade"]] += 1
    ai_by_student[sp] = {
        "count": len(sp_parts),
        "avg": round(sum(pts) / len(pts), 2) if pts else 0,
        "dist": dist,
    }

# Summary cards
ai_summary_cards = ""
for sp in STUDENTS_ORDER:
    st = ai_by_student[sp]
    if st["count"] == 0:
        continue
    avg = st["avg"]
    letter = ai_letter(avg)
    color = COLORS[sp]
    dist = st["dist"]
    dist_bars = ""
    for g in ["A", "B", "C", "D", "E"]:
        w = round(dist[g] / st["count"] * 60) if st["count"] else 0
        dist_bars += (
            '<div style="display:flex;align-items:center;gap:4px;margin-bottom:3px;font-size:11px">'
            '<span style="width:10px;color:' + GRADE_COLOR[g] + ';font-weight:700">' + g + '</span>'
            '<div style="width:' + str(max(w,0)) + 'px;height:8px;border-radius:2px;background:' + GRADE_COLOR[g] + ';opacity:.8"></div>'
            '<span style="color:#666">' + str(dist[g]) + '</span></div>'
        )
    ai_summary_cards += (
        '<div style="background:#1a1a28;border:1px solid #2a2a3a;border-radius:10px;padding:16px;border-top:3px solid ' + color + '">'
        '<div style="font-weight:700;color:' + color + ';margin-bottom:6px">' + NAMES[sp] + '</div>'
        '<div style="font-size:34px;font-weight:800;color:#e0e0e0;line-height:1">' + str(avg) + '</div>'
        '<div style="font-size:12px;color:#888;margin-bottom:10px;margin-top:2px">'
        + letter + ' · ' + GRADE_LABEL.get(letter, '') + ' · ' + str(st["count"]) + ' evaluated</div>'
        + dist_bars + '</div>'
    )

# Per-student AI panels
ai_student_tabs = ""
ai_student_panels = ""

for sp in STUDENTS_ORDER:
    info = by_student[sp]
    if info["total"] == 0:
        continue
    color = COLORS[sp]
    name  = NAMES[sp]
    st = ai_by_student[sp]
    avg_str = str(st["avg"]) + " (" + ai_letter(st["avg"]) + ")" if st["count"] else "—"

    ai_student_tabs += (
        '<button class="stab" data-student="' + sp +
        '" onclick="showAIStudent(\'' + sp + '\')" style="--sc:' + color + '">' +
        name + ' <span class="stab-count">' + str(info["total"]) + '</span></button>'
    )

    cards = ""
    for p in info["parts"]:
        ag = p.get("ai_grade", "")
        ar = p.get("ai_rationale", "")
        rubric_lbl = "Rubric A" if p["type"] == "student_response" else "Rubric B"
        rubric_cls = "rubric-indicator-resp" if p["type"] == "student_response" else "rubric-indicator-part"
        ctx_html = ""
        if p["context"]:
            ctx_html = (
                '<div class="ctx"><span class="ctx-label">Ileana\'s context:</span> '
                + esc(p["context"]) + "</div>"
            )
        if ag:
            grade_html = (
                '<div style="background:' + GRADE_BG[ag] + ';border:1px solid ' + GRADE_COLOR[ag] +
                ';border-radius:8px;padding:10px 14px;margin-top:8px;display:flex;align-items:center;gap:12px">'
                '<span style="font-size:30px;font-weight:800;color:' + GRADE_COLOR[ag] + '">' + ag + '</span>'
                '<div><div style="font-size:13px;font-weight:600;color:' + GRADE_COLOR[ag] + '">'
                + GRADE_LABEL[ag] + ' · ' + str(PTS_MAP[ag]) + ' pts</div>'
                '<div style="font-size:12px;color:#aaa;margin-top:2px">' + esc(ar) + '</div>'
                '</div></div>'
            )
        else:
            grade_html = '<div style="font-size:12px;color:#555;margin-top:8px;font-style:italic">Not evaluated</div>'

        cards += (
            '<div class="pcard">'
            '<div class="pcard-top">'
            '<span class="pcard-ts">⏱ ' + p["timestamp"] + "</span>" +
            badge(p["type"]) +
            '<span class="rubric-indicator ' + rubric_cls + '">' + rubric_lbl + '</span>'
            '<span class="pcard-block">B' + str(p["block"]).zfill(2) + "</span></div>" +
            ctx_html +
            '<div class="pcard-text">' + esc(p["text"]) + "</div>" +
            grade_html + "</div>"
        )

    ai_student_panels += (
        '<div class="spanel" id="ai-spanel-' + sp + '" style="display:none">'
        '<div class="spanel-header" style="border-color:' + color + '">'
        '<span class="spanel-name" style="color:' + color + '">' + name + '</span>'
        '<div class="spanel-stats">'
        '<span>💬 ' + str(info["total"]) + ' participations</span>'
        '<span>↩ ' + str(info["responses"]) + ' responses</span>'
        '<span>❓ ' + str(info["questions"]) + ' questions</span>'
        '<span>💡 ' + str(info["comments"]) + ' comments</span>'
        '</div>'
        '<div class="spanel-avg">AI Average: <span class="avg-val">' + avg_str + '</span></div>'
        '</div>'
        '<div class="pcards-list">' + cards + '</div>'
        '</div>'
    )

# ── Teacher questions table ───────────────────────────────────────────────────
tq_rows = ""
for b in all_blocks:
    for u in b.get("utterances", []):
        if u["type"] == "teacher_question":
            ts  = u.get("timestamp_abs", u.get("timestamp", ""))
            txt = esc(u.get("text", ""))
            tq_rows += "<tr><td class='ts-cell'>" + ts + "</td><td>" + txt + "</td></tr>"

# ── Bar chart HTML ────────────────────────────────────────────────────────────
max_total = max((by_student[sp]["total"] for sp in STUDENTS_ORDER), default=1)
bar_rows = ""
for sp in STUDENTS_ORDER:
    if by_student[sp]["total"] == 0:
        continue
    pct = round(by_student[sp]["total"] / max_total * 100)
    bar_rows += (
        '<div class="bar-row">'
        '<span class="bar-name">' + NAMES[sp] + "</span>"
        '<div class="bar-track"><div class="bar-fill" style="width:' + str(pct) +
        '%;background:' + COLORS[sp] + '">' + str(by_student[sp]["total"]) + "</div></div>"
        '<span class="bar-total">' + str(by_student[sp]["total"]) + "</span></div>"
    )

ai_overview_cards = ""
for sp in STUDENTS_ORDER:
    st = ai_by_student[sp]
    if st["count"] == 0:
        continue
    avg = st["avg"]
    letter = ai_letter(avg)
    color = COLORS[sp]
    ai_overview_cards += (
        '<div style="background:#141420;border:1px solid #222;border-radius:8px;padding:12px;'
        'border-top:2px solid ' + color + ';text-align:center">'
        '<div style="font-weight:700;color:' + color + ';font-size:12px;margin-bottom:6px">' + NAMES[sp] + '</div>'
        '<div style="font-size:26px;font-weight:800;color:#e0e0e0">' + str(avg) + '</div>'
        '<div style="font-size:11px;color:' + GRADE_COLOR[letter] + ';margin-top:2px">'
        + letter + ' · ' + GRADE_LABEL.get(letter, '') + '</div>'
        '<div style="font-size:10px;color:#555;margin-top:2px">' + str(st["count"]) + ' participations</div>'
        '</div>'
    )

type_rows = ""
for sp in STUDENTS_ORDER:
    if by_student[sp]["total"] == 0:
        continue
    r = by_student[sp]["responses"] * 5
    q = by_student[sp]["questions"]  * 5
    c = by_student[sp]["comments"]   * 5
    def seg(w, cls, n):
        return ('<span class="type-seg ' + cls + '" style="width:' + str(w) + 'px">' +
                (str(n) if n > 0 else "") + "</span>") if w > 0 else ""
    type_rows += (
        '<div class="type-row">'
        '<span style="width:70px;font-size:13px;color:#ccc;text-align:right">' + NAMES[sp] + "</span>" +
        seg(r, "seg-resp", by_student[sp]["responses"]) +
        seg(q, "seg-q",    by_student[sp]["questions"]) +
        seg(c, "seg-comm", by_student[sp]["comments"]) +
        "</div>"
    )

# JSON for JS
parts_json = json.dumps(participations, ensure_ascii=False)
stats_json = json.dumps(
    {sp: {k: by_student[sp][k] for k in ("total","responses","questions","comments")}
     for sp in STUDENTS_ORDER},
    ensure_ascii=False
)

# ── Full HTML ─────────────────────────────────────────────────────────────────
html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Clase — 7 Abril 2026</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0c0c10;color:#e0e0e0;font-size:14px}
.header{background:linear-gradient(135deg,#12122a 0%,#1a1a35 100%);padding:24px 32px;border-bottom:1px solid #2a2a4a}
.header h1{font-size:22px;color:#a8b4ff;margin-bottom:4px}
.header-sub{color:#666;font-size:13px}
.header-stats{display:flex;gap:16px;margin-top:16px;flex-wrap:wrap}
.hstat{background:#1e1e3a;border:1px solid #2a2a4a;border-radius:10px;padding:12px 20px;text-align:center}
.hstat-num{font-size:28px;font-weight:700;color:#a0b0ff}
.hstat-label{font-size:11px;color:#666;margin-top:2px;text-transform:uppercase;letter-spacing:.05em}
.main-nav{background:#111118;border-bottom:1px solid #222;display:flex;gap:0;padding:0 32px}
.mnav-btn{background:none;border:none;color:#666;padding:14px 20px;cursor:pointer;font-size:13px;
          border-bottom:2px solid transparent;transition:all .2s}
.mnav-btn.active{color:#a8b4ff;border-bottom-color:#a8b4ff}
.mnav-btn:hover{color:#ccc}
.section{display:none;padding:28px 32px;max-width:1300px;margin:0 auto}
.section.active{display:block}
.section-title{font-size:17px;color:#8898ee;margin-bottom:20px;font-weight:600}
.overview-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}
@media(max-width:800px){.overview-grid{grid-template-columns:1fr}}
.chart-card{background:#141420;border:1px solid #222;border-radius:12px;padding:20px}
.chart-card h3{font-size:12px;color:#666;text-transform:uppercase;letter-spacing:.06em;margin-bottom:16px}
.bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.bar-name{width:80px;font-size:13px;color:#ccc;text-align:right;flex-shrink:0}
.bar-track{flex:1;background:#1c1c28;border-radius:4px;height:22px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;padding-left:8px;
          font-size:11px;font-weight:600;color:rgba(255,255,255,.85)}
.bar-total{width:36px;font-size:13px;color:#888;text-align:right}
.type-row{display:flex;align-items:center;gap:6px;margin-bottom:8px}
.type-seg{height:18px;border-radius:3px;display:inline-flex;align-items:center;
          padding:0 6px;font-size:11px;font-weight:600;color:rgba(255,255,255,.9);min-width:4px}
.seg-resp{background:#2d7d5a}.seg-q{background:#3a6da8}.seg-comm{background:#7a5a9a}
.rubric-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:24px}
@media(max-width:900px){.rubric-grid{grid-template-columns:repeat(3,1fr)}}
.rcard{border-radius:10px;padding:14px;border:1px solid}
.rcard-A{background:rgba(34,134,84,.12);border-color:#22864a}
.rcard-B{background:rgba(50,100,200,.12);border-color:#3264c8}
.rcard-C{background:rgba(180,150,30,.12);border-color:#b49620}
.rcard-D{background:rgba(200,100,30,.12);border-color:#c8641e}
.rcard-E{background:rgba(180,30,30,.12);border-color:#b41e1e}
.rcard-letter{font-size:28px;font-weight:800;margin-bottom:4px}
.rcard-A .rcard-letter{color:#3ada8a}.rcard-B .rcard-letter{color:#6496e8}
.rcard-C .rcard-letter{color:#d4b030}.rcard-D .rcard-letter{color:#e07840}
.rcard-E .rcard-letter{color:#e04040}
.rcard-label{font-size:13px;font-weight:600;margin-bottom:6px}
.rcard-bloom{font-size:11px;color:#888;margin-bottom:2px}
.rcard-solo{font-size:11px;color:#666;margin-bottom:6px}
.rcard-desc{font-size:12px;color:#aaa;line-height:1.5}
.rubric-block{margin-bottom:28px}
.rubric-block-header{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px;
                     padding:12px 16px;background:#141420;border-radius:8px;border:1px solid #222}
.rubric-block-title{font-size:15px;font-weight:600;color:#ddd}
.rubric-block-sub{font-size:12px;color:#666;margin-left:auto}
.rubric-tag{font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;white-space:nowrap}
.rubric-tag-resp{background:#1a3a2a;color:#5aaa7a;border:1px solid #2d6645}
.rubric-tag-part{background:#1a2a3a;color:#5a8aca;border:1px solid #2d4f80}
.rubric-indicator{font-size:10px;padding:2px 7px;border-radius:4px;margin-left:4px;font-weight:600}
.rubric-indicator-resp{background:#1a3a2a;color:#5aaa7a}
.rubric-indicator-part{background:#1a2a3a;color:#5a8aca}
.stabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}
.stab{background:#1a1a28;border:1px solid #333;border-radius:8px;padding:8px 16px;
      cursor:pointer;font-size:13px;color:#aaa;transition:all .2s;display:flex;align-items:center;gap:8px}
.stab.active{background:color-mix(in srgb,var(--sc) 20%,#1a1a28);border-color:var(--sc);color:var(--sc)}
.stab:hover{border-color:var(--sc);color:var(--sc)}
.stab-count{background:#2a2a3a;border-radius:20px;padding:2px 7px;font-size:11px}
.spanel-header{border-left:4px solid;padding:12px 16px;background:#141420;border-radius:0 8px 8px 0;
               margin-bottom:16px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.spanel-name{font-size:18px;font-weight:700}
.spanel-stats{display:flex;gap:16px;font-size:12px;color:#888;flex-wrap:wrap}
.spanel-avg{margin-left:auto;font-size:13px;color:#aaa}
.avg-val{font-size:18px;font-weight:700;color:#a8b4ff}
.pcards-list{display:flex;flex-direction:column;gap:10px}
.pcard{background:#141420;border:1px solid #222;border-radius:10px;padding:14px 16px}
.pcard.graded-A{border-left:4px solid #3ada8a}
.pcard.graded-B{border-left:4px solid #6496e8}
.pcard.graded-C{border-left:4px solid #d4b030}
.pcard.graded-D{border-left:4px solid #e07840}
.pcard.graded-E{border-left:4px solid #e04040}
.pcard-top{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.pcard-ts{font-family:monospace;font-size:12px;color:#555}
.pcard-block{font-size:11px;color:#444;background:#1c1c28;padding:2px 7px;border-radius:4px}
.pcard-score{margin-left:auto;font-size:12px}
.ai-score{background:#1e2a1e;color:#70aa70;padding:2px 8px;border-radius:4px;font-size:11px}
.manual-score{background:#1a2a3a;color:#6a9aea;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:4px}
.badge{font-size:11px;padding:2px 8px;border-radius:4px;font-weight:600}
.badge-resp{background:#1a3a2a;color:#5aaa7a}
.badge-q{background:#1a2a3a;color:#5a8aca}
.badge-comm{background:#2a1a3a;color:#9a6aca}
.ctx{font-size:12px;color:#555;background:#111118;border-left:2px solid #333;
     padding:6px 10px;margin-bottom:8px;border-radius:0 4px 4px 0;line-height:1.5}
.ctx-label{color:#444;font-weight:600}
.pcard-text{font-size:14px;color:#d8d8d8;line-height:1.65;margin-bottom:12px}
.pcard-grade{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.grade-label{font-size:11px;color:#555;margin-right:4px}
.gbtn{width:32px;height:32px;border:1px solid #333;border-radius:6px;background:#1c1c28;
      color:#888;font-weight:700;cursor:pointer;transition:all .15s;font-size:13px}
.gbtn-A:hover,.gbtn-A.active{background:#22864a;border-color:#3ada8a;color:#fff}
.gbtn-B:hover,.gbtn-B.active{background:#2050a0;border-color:#6496e8;color:#fff}
.gbtn-C:hover,.gbtn-C.active{background:#806010;border-color:#d4b030;color:#fff}
.gbtn-D:hover,.gbtn-D.active{background:#804020;border-color:#e07840;color:#fff}
.gbtn-E:hover,.gbtn-E.active{background:#801010;border-color:#e04040;color:#fff}
.tq-table{width:100%;border-collapse:collapse}
.tq-table th{background:#1c1c28;color:#666;font-size:11px;text-transform:uppercase;
             letter-spacing:.05em;padding:10px 14px;text-align:left;border-bottom:1px solid #2a2a2a}
.tq-table td{padding:10px 14px;border-bottom:1px solid #1a1a24;font-size:13px;vertical-align:top;line-height:1.5}
.tq-table tr:hover td{background:rgba(255,255,255,.02)}
.ts-cell{font-family:monospace;font-size:12px;color:#555;white-space:nowrap;width:60px}
.ebtn{background:#1e2a4a;border:1px solid #3a4a7a;color:#8090cc;padding:8px 16px;
      border-radius:8px;cursor:pointer;font-size:13px;transition:all .2s}
.ebtn:hover{background:#2a3a6a;color:#aabbee}
.ebtn-del{color:#e06060;border-color:#5a2020;background:#2a1a1a}
.ebtn-del:hover{background:#3a1a1a;color:#ff8080}
.progress-row{display:flex;align-items:center;gap:12px;background:#141420;
              border:1px solid #222;border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px}
.prog-track{flex:1;background:#1c1c28;border-radius:4px;height:10px}
.prog-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,#3264c8,#32b48a);transition:width .3s}
</style>
</head>
<body>
""" + \
f"""<div class="header">
  <h1>📊 Class Dashboard — April 7, 2026</h1>
  <div class="header-sub">Verbatim Transcription + Student Evaluation · Gemini 2.5-flash · 59:30 min</div>
  <div class="header-stats">
    <div class="hstat"><div class="hstat-num">59:30</div><div class="hstat-label">Duration</div></div>
    <div class="hstat"><div class="hstat-num">{total_teacher}</div><div class="hstat-label">Ileana's Questions</div></div>
    <div class="hstat"><div class="hstat-num">{total_parts}</div><div class="hstat-label">Participations</div></div>
    <div class="hstat"><div class="hstat-num" id="graded-count">0</div><div class="hstat-label">Evaluated</div></div>
    <div class="hstat"><div class="hstat-num">4</div><div class="hstat-label">Active Students</div></div>
  </div>
</div>

<nav class="main-nav">
  <button class="mnav-btn active" onclick="showSection('overview',this)">📊 Overview</button>
  <button class="mnav-btn" onclick="showSection('ai',this)">🤖 AI Evaluation</button>
  <button class="mnav-btn" onclick="showSection('evaluate',this)">✏️ Manual Evaluation</button>
  <button class="mnav-btn" onclick="showSection('questions',this)">❓ Ileana's Questions</button>
  <button class="mnav-btn" onclick="showSection('rubric',this)">📋 Rubric</button>
</nav>

<!-- OVERVIEW -->
<div class="section active" id="section-overview">
  <p class="section-title">Student Participation</p>
  <div class="overview-grid">
    <div class="chart-card">
      <h3>Total interventions per student</h3>
      {bar_rows}
    </div>
    <div class="chart-card">
      <h3>Participation type breakdown</h3>
      {type_rows}
      <div style="display:flex;gap:12px;margin-top:12px;font-size:11px;color:#666">
        <span><span style="background:#2d7d5a;padding:2px 6px;border-radius:3px">■</span> Responses</span>
        <span><span style="background:#3a6da8;padding:2px 6px;border-radius:3px">■</span> Questions</span>
        <span><span style="background:#7a5a9a;padding:2px 6px;border-radius:3px">■</span> Comments</span>
      </div>
    </div>
  </div>
  <div class="chart-card">
    <h3>AI Evaluation averages</h3>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px">
      {ai_overview_cards}
    </div>
  </div>
  <div class="chart-card" style="margin-top:20px">
    <h3>Manual evaluation averages (updates in real time)</h3>
    <div id="overview-results" style="padding:20px;text-align:center;color:#444;font-size:13px">
      No evaluations yet. Go to <strong style="color:#a8b4ff">✏️ Manual Evaluation</strong> to grade participations.
    </div>
  </div>
</div>

<!-- AI EVALUATION -->
<div class="section" id="section-ai">
  <p class="section-title">AI Evaluation — Gemini 2.5-flash · Rubrics A &amp; B</p>
  <div style="background:#141420;border:1px solid #2a2a3a;border-radius:10px;padding:14px 18px;
              font-size:13px;color:#888;line-height:1.7;margin-bottom:20px">
    Each participation was evaluated by Gemini 2.5-flash using
    <span style="color:#5aaa7a;font-weight:600">Rubric A</span> for direct responses and
    <span style="color:#5a8aca;font-weight:600">Rubric B</span> for voluntary contributions and questions.
    Grades are read-only here — use <strong style="color:#aaa">✏️ Manual Evaluation</strong> to override.
  </div>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px">
    {ai_summary_cards}
  </div>
  <div class="stabs" id="ai-student-tabs">{ai_student_tabs}</div>
  <div id="ai-student-panels">{ai_student_panels}</div>
</div>

<!-- EVALUAR -->
<div class="section" id="section-evaluate">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px">
    <p class="section-title" style="margin-bottom:0">Manual Evaluation — Grade each participation (A–E)</p>
    <div style="display:flex;gap:8px">
      <button class="ebtn" onclick="exportCSV()">⬇️ Export CSV</button>
      <button class="ebtn ebtn-del" onclick="clearAll()">🗑 Clear all</button>
    </div>
  </div>
  <div class="progress-row">
    <span>Progress:</span>
    <div class="prog-track"><div class="prog-fill" id="prog-bar" style="width:0%"></div></div>
    <span id="prog-text">0 / {total_parts}</span>
  </div>
  <div class="stabs" id="student-tabs">{tabs_html}</div>
  <div id="student-panels">{panels_html}</div>
</div>

<!-- ILEANA'S QUESTIONS -->
<div class="section" id="section-questions">
  <p class="section-title">Ileana's Questions ({total_teacher} total)</p>
  <table class="tq-table">
    <thead><tr><th>Time</th><th>Question</th></tr></thead>
    <tbody>{tq_rows}</tbody>
  </table>
</div>

<!-- RUBRIC -->
<div class="section" id="section-rubric">

  <div class="rubric-block">
    <div class="rubric-block-header">
      <span class="rubric-tag rubric-tag-resp">↩ Response Rubric</span>
      <span class="rubric-block-title">Rubric A — Direct Responses to Teacher</span>
      <span class="rubric-block-sub">Use this rubric when grading <strong>Responses</strong> to Ileana's questions</span>
    </div>
    <div class="rubric-grid">
      <div class="rcard rcard-A"><div class="rcard-letter">A</div>
        <div class="rcard-label">Excellent · 5 pts</div>
        <div class="rcard-bloom">🧠 Bloom: Create / Evaluate</div>
        <div class="rcard-solo">SOLO: Extended Abstract</div>
        <div class="rcard-desc">Deep, reflective response with critical analysis and original connections beyond the question</div></div>
      <div class="rcard rcard-B"><div class="rcard-letter">B</div>
        <div class="rcard-label">Good · 4 pts</div>
        <div class="rcard-bloom">🧠 Bloom: Analyze / Synthesize</div>
        <div class="rcard-solo">SOLO: Relational</div>
        <div class="rcard-desc">Clear, complete response that connects concepts and demonstrates solid understanding</div></div>
      <div class="rcard rcard-C"><div class="rcard-letter">C</div>
        <div class="rcard-label">Satisfactory · 3 pts</div>
        <div class="rcard-bloom">🧠 Bloom: Apply / Understand</div>
        <div class="rcard-solo">SOLO: Multistructural</div>
        <div class="rcard-desc">Correct response but limited in detail, depth, or elaboration</div></div>
      <div class="rcard rcard-D"><div class="rcard-letter">D</div>
        <div class="rcard-label">Insufficient · 2 pts</div>
        <div class="rcard-bloom">🧠 Bloom: Remember</div>
        <div class="rcard-solo">SOLO: Unistructural</div>
        <div class="rcard-desc">Incomplete or partially correct response, lacking connection to the topic</div></div>
      <div class="rcard rcard-E"><div class="rcard-letter">E</div>
        <div class="rcard-label">Deficient · 1 pt</div>
        <div class="rcard-bloom">🧠 Bloom: Does not demonstrate</div>
        <div class="rcard-solo">SOLO: Prestructural</div>
        <div class="rcard-desc">Incorrect, irrelevant, or no response to the teacher's question</div></div>
    </div>
  </div>

  <div class="rubric-block">
    <div class="rubric-block-header">
      <span class="rubric-tag rubric-tag-part">💬 Participation Rubric</span>
      <span class="rubric-block-title">Rubric B — Voluntary Contributions &amp; Questions</span>
      <span class="rubric-block-sub">Use this rubric when grading <strong>Questions</strong> and <strong>Comments</strong> initiated by students</span>
    </div>
    <div class="rubric-grid">
      <div class="rcard rcard-A"><div class="rcard-letter">A</div>
        <div class="rcard-label">Excellent · 5 pts</div>
        <div class="rcard-bloom">🧠 Bloom: Create / Evaluate</div>
        <div class="rcard-solo">SOLO: Extended Abstract</div>
        <div class="rcard-desc">Insightful contribution or question that advances the discussion, introduces original thinking, or critically challenges ideas</div></div>
      <div class="rcard rcard-B"><div class="rcard-letter">B</div>
        <div class="rcard-label">Good · 4 pts</div>
        <div class="rcard-bloom">🧠 Bloom: Analyze / Synthesize</div>
        <div class="rcard-solo">SOLO: Relational</div>
        <div class="rcard-desc">Meaningful contribution that connects ideas, asks a clarifying question that deepens understanding, or builds on a previous point</div></div>
      <div class="rcard rcard-C"><div class="rcard-letter">C</div>
        <div class="rcard-label">Satisfactory · 3 pts</div>
        <div class="rcard-bloom">🧠 Bloom: Apply / Understand</div>
        <div class="rcard-solo">SOLO: Multistructural</div>
        <div class="rcard-desc">Relevant participation that shows topic awareness, though without significant depth or new insight</div></div>
      <div class="rcard rcard-D"><div class="rcard-letter">D</div>
        <div class="rcard-label">Insufficient · 2 pts</div>
        <div class="rcard-bloom">🧠 Bloom: Remember</div>
        <div class="rcard-solo">SOLO: Unistructural</div>
        <div class="rcard-desc">Loosely related to the topic but adds minimal value; surface-level or repetitive contribution</div></div>
      <div class="rcard rcard-E"><div class="rcard-letter">E</div>
        <div class="rcard-label">Deficient · 1 pt</div>
        <div class="rcard-bloom">🧠 Bloom: Does not demonstrate</div>
        <div class="rcard-solo">SOLO: Prestructural</div>
        <div class="rcard-desc">Off-topic, unclear, or contribution that does not add value to the class discussion</div></div>
    </div>
  </div>

  <div style="background:#141420;border:1px solid #222;border-radius:10px;padding:16px;font-size:13px;color:#888;line-height:1.7">
    Grades are saved automatically in the browser (localStorage).
    Use <strong style="color:#aaa">Export CSV</strong> to download the final grading report.
    Each participation card indicates whether to use Rubric A (response) or Rubric B (contribution).
  </div>
</div>
""" + \
f"""
<script>
const PARTICIPATIONS = {parts_json};
const BY_STUDENT = {stats_json};
const TOTAL = {total_parts};
const PTS = {{A:5,B:4,C:3,D:2,E:1}};
const COLORS = {json.dumps(COLORS)};
const NAMES = {json.dumps(NAMES)};

function loadGrades(){{try{{return JSON.parse(localStorage.getItem('grades_20260407')||'{{}}')||{{}};}}catch{{return{{}};}}}}
function saveGrades(g){{localStorage.setItem('grades_20260407',JSON.stringify(g));}}
let grades=loadGrades();

function showSection(id,btn){{
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.mnav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('section-'+id).classList.add('active');
  if(btn)btn.classList.add('active');
  updateOverview();
}}

let activeStudent=null;
let activeAIStudent=null;
function showAIStudent(sp){{
  document.querySelectorAll('.spanel[id^="ai-spanel"]').forEach(p=>p.style.display='none');
  document.querySelectorAll('#ai-student-tabs .stab').forEach(t=>t.classList.remove('active'));
  document.getElementById('ai-spanel-'+sp).style.display='block';
  document.querySelector('#ai-student-tabs .stab[data-student="'+sp+'"]').classList.add('active');
  activeAIStudent=sp;
}}
function showStudent(sp){{
  document.querySelectorAll('.spanel').forEach(p=>p.style.display='none');
  document.querySelectorAll('.stab').forEach(t=>t.classList.remove('active'));
  document.getElementById('spanel-'+sp).style.display='block';
  document.querySelector('.stab[data-student="'+sp+'"]').classList.add('active');
  activeStudent=sp;
  updateAvg(sp);
}}

function gradeCard(id,grade){{
  grades[id]=grade;
  saveGrades(grades);
  const card=document.getElementById('pcard-'+id);
  card.className=card.className.replace(/graded-[A-E]/g,'');
  card.classList.add('graded-'+grade);
  card.querySelectorAll('.gbtn').forEach(b=>b.classList.remove('active'));
  card.querySelector('.gbtn-'+grade).classList.add('active');
  const lbl=document.getElementById('score-label-'+id);
  const ex=lbl.querySelector('.manual-score');
  if(ex)ex.remove();
  const ms=document.createElement('span');
  ms.className='manual-score';
  ms.textContent='Manual: '+grade;
  lbl.appendChild(ms);
  if(activeStudent)updateAvg(activeStudent);
  updateProgress();
  updateOverview();
}}

function updateAvg(sp){{
  const pts=PARTICIPATIONS.filter(p=>p.speaker===sp&&grades[p.id]).map(p=>PTS[grades[p.id]]);
  const el=document.getElementById('avg-'+sp);
  if(!el)return;
  if(!pts.length){{el.textContent='—';return;}}
  const avg=(pts.reduce((a,b)=>a+b,0)/pts.length).toFixed(2);
  const l=avg>=4.5?'A':avg>=3.5?'B':avg>=2.5?'C':avg>=1.5?'D':'E';
  el.textContent=avg+' ('+l+')';
}}

function updateProgress(){{
  const done=Object.keys(grades).length;
  document.getElementById('graded-count').textContent=done;
  document.getElementById('prog-text').textContent=done+' / '+TOTAL;
  document.getElementById('prog-bar').style.width=Math.round(done/TOTAL*100)+'%';
}}

function updateOverview(){{
  const students=['ARYANG','GRACE','STHEPEN','CHILAKA','MEGA'];
  const any=students.some(sp=>PARTICIPATIONS.some(p=>p.speaker===sp&&grades[p.id]));
  if(!any)return;
  let html='<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px">';
  students.forEach(sp=>{{
    const pts=PARTICIPATIONS.filter(p=>p.speaker===sp&&grades[p.id]).map(p=>PTS[grades[p.id]]);
    if(!pts.length)return;
    const avg=(pts.reduce((a,b)=>a+b,0)/pts.length).toFixed(2);
    const l=avg>=4.5?'A':avg>=3.5?'B':avg>=2.5?'C':avg>=1.5?'D':'E';
    const tot=BY_STUDENT[sp]?.total||0;
    html+=`<div style="background:#1a1a28;border:1px solid #2a2a3a;border-radius:10px;padding:14px;border-top:3px solid ${{COLORS[sp]}}">
      <div style="font-weight:700;color:${{COLORS[sp]}};margin-bottom:8px">${{NAMES[sp]}}</div>
      <div style="font-size:32px;font-weight:800;color:#e0e0e0;line-height:1">${{avg}}</div>
      <div style="font-size:13px;color:#888;margin-top:4px">${{l}} &nbsp;·&nbsp; ${{pts.length}}/${{tot}} graded</div></div>`;
  }});
  html+='</div>';
  document.getElementById('overview-results').innerHTML=html;
}}

function exportCSV(){{
  const rows=[['ID','Time','Block','Student','Type','Text','Grade','Points','AI_Score']];
  PARTICIPATIONS.forEach(p=>{{
    const g=grades[p.id]||'';
    rows.push([p.id,p.timestamp,'B'+String(p.block).padStart(2,'0'),
               p.speaker,p.type,'"'+p.text.replace(/"/g,'""')+'"',g,g?PTS[g]:'',p.gemini_score||'']);
  }});
  const a=document.createElement('a');
  a.href='data:text/csv;charset=utf-8,\\uFEFF'+encodeURIComponent(rows.map(r=>r.join(',')).join('\\n'));
  a.download='class_evaluation_20260407.csv';
  a.click();
}}

function clearAll(){{
  if(!confirm('Clear all grades? This cannot be undone.'))return;
  grades={{}};
  saveGrades(grades);
  document.querySelectorAll('.pcard').forEach(c=>{{
    c.className='pcard';
    c.querySelectorAll('.gbtn').forEach(b=>b.classList.remove('active'));
    const ms=c.querySelector('.manual-score');
    if(ms)ms.remove();
  }});
  ['ARYANG','GRACE','STHEPEN','CHILAKA','MEGA'].forEach(sp=>{{
    const el=document.getElementById('avg-'+sp);
    if(el)el.textContent='—';
  }});
  updateProgress();
  document.getElementById('overview-results').innerHTML='No evaluations yet.';
}}

// Init — restore saved grades
(function(){{
  Object.entries(grades).forEach(([id,g])=>{{
    const card=document.getElementById('pcard-'+id);
    if(!card)return;
    card.classList.add('graded-'+g);
    const btn=card.querySelector('.gbtn-'+g);
    if(btn)btn.classList.add('active');
    const lbl=document.getElementById('score-label-'+id);
    if(lbl){{
      const ms=document.createElement('span');
      ms.className='manual-score';
      ms.textContent='Manual: '+g;
      lbl.appendChild(ms);
    }}
  }});
  updateProgress();
  const first=document.querySelector('#student-tabs .stab');
  if(first)showStudent(first.dataset.student);
  const firstAI=document.querySelector('#ai-student-tabs .stab');
  if(firstAI)showAIStudent(firstAI.dataset.student);
}})();
</script>
</body>
</html>
"""

with open(output_f, "w", encoding="utf-8") as f:
    f.write(html)

size = output_f.stat().st_size / 1024
print(f"✅ Dashboard: {output_f}")
print(f"   {size:.0f} KB · {total_parts} participaciones · {total_teacher} preguntas Ileana")
print(f'\n   open "{output_f}"')
