#!/usr/bin/env python3
"""
Genera una página HTML por clase con:
  - Resumen Componente A (2 escenarios)
  - Transcripción completa con timestamps
  - Detalle de scoring por utterance (rúbrica 1-6)
  - Link de regreso al dashboard

Output: docs/classes/<session_id>.html
"""

import json
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "clases"
DOCS_DIR = REPO_ROOT / "docs"
CLASSES_OUT = DOCS_DIR / "classes"
CLASSES_OUT.mkdir(parents=True, exist_ok=True)

STUDENTS = ["Aryang", "Mega", "Chilaka", "Grace", "Sthepen"]


def render_class_html(sid):
    """Genera HTML de detalle para una clase."""
    sd = DATA_DIR / sid
    ca_file = sd / "component_a.json"
    analysis_file = sd / "analysis.json"
    if not ca_file.exists() or not analysis_file.exists():
        return None

    with open(ca_file, encoding="utf-8") as f:
        ca = json.load(f)
    with open(analysis_file, encoding="utf-8") as f:
        analysis = json.load(f)

    summary = ca.get("summary", {})
    prep_rows = ca.get("preparation", {}).get("rows", [])
    part_rows = ca.get("participation", {}).get("rows", [])
    full_transcript = analysis.get("full_transcription", [])
    is_virtual = not full_transcript and ca.get("note", "").lower().startswith("presentation")
    virtual_note = ca.get("note", "")

    # Generar tabla de resumen
    summary_rows = ""
    sorted_students = sorted(summary.items(), key=lambda x: x[1]["component_a_total_scenario_A"], reverse=True)
    for s, sm in sorted_students:
        summary_rows += f"""<tr>
          <td class="student-name">{s}</td>
          <td>{sm['preparation_pct']:.2f}</td>
          <td>{sm['participation_pct_A_quality_only']:.2f}</td>
          <td>{sm['attendance_pct']:.2f}</td>
          <td class="total">{sm['component_a_total_scenario_A']:.2f}</td>
        </tr>"""

    # Tabla de transcripción
    transcript_rows = ""
    for u in full_transcript:
        speaker = u.get("speaker", "?")
        ttype = u.get("type", "")
        text = (u.get("text", "") or "").replace("<", "&lt;").replace(">", "&gt;")
        ts = u.get("timestamp", "")
        css = "row-teacher" if ttype.startswith("teacher") else "row-student"
        if ttype == "teacher_question":
            css += " row-question"
        type_label = {
            "teacher_question": "❓ Question",
            "teacher_statement": "📖 Teacher",
            "teacher_response": "💬 Teacher",
            "teacher_comment": "💭 Teacher",
            "student_response": "💬 Response",
            "student_question": "❓ Student question",
            "student_comment": "💬 Comment",
        }.get(ttype, ttype)
        transcript_rows += f"""<tr class="{css}">
          <td class="ts">{ts}</td>
          <td class="speaker">{speaker.title()}</td>
          <td class="type">{type_label}</td>
          <td class="text">{text}</td>
        </tr>"""

    # Preparation matrix
    prep_table = "<table class='detail-table'><thead><tr><th>Time</th><th>Question</th>"
    for s in STUDENTS:
        prep_table += f"<th>{s}</th>"
    prep_table += "</tr></thead><tbody>"
    for r in prep_rows:
        is_open = r.get("is_open", False)
        directed = r.get("directed_to", "")
        tag = " (open)" if is_open else f" → {directed}"
        q = (r.get("question", "") or "")[:120].replace("<", "&lt;").replace(">", "&gt;")
        prep_table += f"<tr><td class='ts'>{r.get('timestamp','')}</td><td class='question-cell'>{q}<small>{tag}</small></td>"
        for s in STUDENTS:
            v = r["scores"].get(s)
            if v is None:
                prep_table += "<td class='na'>—</td>"
            elif v == 0:
                prep_table += "<td class='zero'>0</td>"
            else:
                color_class = f"score-{v}"
                prep_table += f"<td class='score {color_class}'>{v}</td>"
        prep_table += "</tr>"
    prep_table += "</tbody></table>"

    # Participation matrix
    part_table = "<table class='detail-table'><thead><tr><th>Time</th><th>Type / Text</th>"
    for s in STUDENTS:
        part_table += f"<th>{s}</th>"
    part_table += "</tr></thead><tbody>"
    for r in part_rows:
        text = (r.get("text", "") or "")[:120].replace("<", "&lt;").replace(">", "&gt;")
        ptype = r.get("type", "")
        part_table += f"<tr><td class='ts'>{r.get('timestamp','')}</td><td class='question-cell'><strong>[{ptype}]</strong> {text}</td>"
        for s in STUDENTS:
            v = r["scores"].get(s)
            if v is None:
                part_table += "<td class='na'>—</td>"
            else:
                color_class = f"score-{v}"
                part_table += f"<td class='score {color_class}'>{v}</td>"
        part_table += "</tr>"
    part_table += "</tbody></table>"

    # Value questions (solo preguntas explícitas de valor sobre el tema)
    vq_file = sd / "value_questions.json"
    has_value = vq_file.exists()
    if has_value:
        vq_data = json.loads(vq_file.read_text(encoding="utf-8"))
        all_rows = vq_data.get("questions", [])
        # Todas las preguntas sustanciales (de valor), con su puntaje visible
        vq_rows = [r for r in all_rows if r.get("is_substantive")]
        vq_rows.sort(key=lambda r: r.get("timestamp", ""))
        n_high = sum(1 for r in vq_rows if isinstance(r.get("score"), int) and r["score"] >= 4)
        value_table = (
            "<p style='color:#64748b; font-size:12px; margin-bottom:12px;'>"
            "The teacher's substantive topic questions, rewritten with context from "
            "the transcript so each question and answer reads on its own. Each shows the "
            "rubric score (1–6) so it can be reviewed. "
            f"<strong>{len(vq_rows)} substantive questions</strong> "
            f"<span style='color:#94a3b8;'>(of {len(all_rows)} answered)</span> · "
            f"<span style='color:#16a34a;'>{n_high} scored 4–6</span>.</p>"
            "<table class='value-table'><thead><tr>"
            "<th style='width:55px'>Time</th><th style='width:150px'>Topic</th>"
            "<th>Question &amp; answer</th><th style='width:110px'>Answered by</th>"
            "<th style='width:60px'>Score</th></tr></thead><tbody>"
        )
        for r in vq_rows:
            q = (r.get("question", "") or "").replace("<", "&lt;").replace(">", "&gt;")
            topic = (r.get("topic", "") or "").replace("<", "&lt;").replace(">", "&gt;")
            who = r.get("answered_by")
            resp = (r.get("response_text", "") or "").replace("<", "&lt;").replace(">", "&gt;")
            score = r.get("score")
            star = "⭐ " if r.get("is_substantive") else ""
            qa_cell = (
                f"<div class='vq-q'>{star}{q}</div>"
                + (f"<div class='vq-a'>💬 {resp}</div>" if resp else "")
            )
            who_cell = f"<strong>{who}</strong>" if who else "<span class='na'>— no answer</span>"
            if score is None:
                score_cell = "<span class='na'>—</span>"
            else:
                score_cell = f"<span class='score score-{score}'>{score}</span>"
            value_table += (
                f"<tr><td class='ts'>{r.get('timestamp','')}</td>"
                f"<td><span class='topic-pill'>{topic}</span></td>"
                f"<td class='question-cell'>{qa_cell}</td>"
                f"<td>{who_cell}</td><td style='text-align:center'>{score_cell}</td></tr>"
            )
        value_table += "</tbody></table>"
    else:
        value_table = (
            "<p style='color:#94a3b8; font-size:13px;'>No value-questions file yet. "
            "Run <code>backend/contextualize_questions.py " + sid + "</code> to generate it.</p>"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Class {sid} — Component A Detail</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f1f5f9; color: #0f172a; line-height: 1.5; }}
  .header {{
    background: linear-gradient(135deg, #305496 0%, #1e3a8a 100%);
    color: white; padding: 24px 40px;
  }}
  .header h1 {{ font-size: 22px; }}
  .back-link {{
    display: inline-block; color: #c7d7f0; text-decoration: none; font-size: 13px;
    margin-bottom: 8px;
  }}
  .back-link:hover {{ color: white; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 40px; }}
  .section {{ background: white; border-radius: 12px; padding: 24px;
              margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
  .section h2 {{ font-size: 16px; margin-bottom: 16px; color: #1e293b; }}
  .tabs {{ display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0; }}
  .tab {{
    padding: 10px 20px; cursor: pointer; border: none; background: none;
    color: #64748b; font-weight: 500; font-size: 14px;
    border-bottom: 2px solid transparent; margin-bottom: -2px;
  }}
  .tab.active {{ color: #305496; border-bottom-color: #305496; font-weight: 700; }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 10px 12px; background: #f8fafc;
        font-weight: 600; color: #475569; border-bottom: 1px solid #e2e8f0;
        font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }}
  .total {{ font-weight: 700; color: #305496; }}
  .student-name {{ font-weight: 600; }}
  .ts {{ font-family: monospace; color: #64748b; white-space: nowrap; }}
  .row-teacher {{ background: rgba(16, 185, 129, 0.04); }}
  .row-question {{ background: rgba(220, 38, 38, 0.06); border-left: 3px solid #dc2626; }}
  .row-student {{ background: rgba(48, 84, 150, 0.04); border-left: 3px solid #305496; }}
  .speaker {{ font-weight: 600; }}
  .type {{ color: #64748b; font-size: 12px; }}
  .text {{ color: #1e293b; }}
  .detail-table th, .detail-table td {{ text-align: center; }}
  .detail-table .question-cell {{ text-align: left; max-width: 380px; font-size: 12px; }}
  .detail-table small {{ color: #94a3b8; display: block; }}
  .value-table td {{ vertical-align: top; }}
  .value-table .question-cell {{ text-align: left; max-width: 560px; }}
  .vq-q {{ font-size: 13px; color: #0f172a; font-weight: 600; }}
  .vq-a {{ font-size: 12.5px; color: #475569; margin-top: 6px; padding: 6px 10px;
           background: #f8fafc; border-left: 3px solid #cbd5e1; border-radius: 4px; }}
  .topic-pill {{ display: inline-block; background: #ede9fe; color: #5b21b6;
                 font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 999px; }}
  .tab-value.active {{ color: #7c3aed; border-bottom-color: #7c3aed; }}
  .score {{ font-weight: 700; font-size: 13px; border-radius: 4px; }}
  .score-6 {{ background: #d1fae5; color: #065f46; }}
  .score-5 {{ background: #d1fae5; color: #047857; }}
  .score-4 {{ background: #fef3c7; color: #92400e; }}
  .score-3 {{ background: #fed7aa; color: #9a3412; }}
  .score-2 {{ background: #fee2e2; color: #991b1b; }}
  .score-1 {{ background: #fecaca; color: #7f1d1d; }}
  .zero {{ background: #fecaca; color: #7f1d1d; font-weight: 700; }}
  .na {{ color: #cbd5e1; }}
  .stats-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 12px; margin-bottom: 20px; }}
  .stat {{ background: #f8fafc; padding: 14px; border-radius: 8px; }}
  .stat-label {{ font-size: 11px; color: #64748b; text-transform: uppercase;
                 letter-spacing: 0.04em; }}
  .stat-value {{ font-size: 22px; font-weight: 700; color: #305496; margin-top: 2px; }}
</style>
</head>
<body>

<div class="header">
  <a href="../dashboard.html" class="back-link">← Back to dashboard</a>
  <h1>📅 Class {sid} — Component A Detail</h1>
</div>

<div class="container">

  <div class="section">
    <h2>📊 Class summary</h2>
    <div class="stats-row">
      <div class="stat"><div class="stat-label">Teacher questions</div><div class="stat-value">{len(prep_rows)}</div></div>
      <div class="stat"><div class="stat-label">Contributions</div><div class="stat-value">{len(part_rows)}</div></div>
      <div class="stat"><div class="stat-label">Total utterances</div><div class="stat-value">{len(full_transcript)}</div></div>
    </div>
    <table>
      <thead><tr><th>Student</th><th>Prep (7.5)</th><th>Part (7.5)</th><th>Att (5)</th><th>Total / 20</th></tr></thead>
      <tbody>
        {summary_rows}
      </tbody>
    </table>
  </div>

  {f'''<div class="section" style="background:#fef3c7; border:1px solid #f59e0b;">
    <h2 style="color:#92400e;">📋 Presentations Day — Week 7</h2>
    <p style="color:#78350f; line-height:1.6;">
      {virtual_note}<br><br>
      <strong>All students received maximum grade (20/20):</strong> Preparation 7.5 + Participation 7.5 + Attendance 5.0
    </p>
  </div>''' if is_virtual else f'''<div class="section">
    <h2>📑 Detail</h2>
    <div class="tabs">
      <button class="tab active" onclick="showTab(this, 'transcript')">Full transcript</button>
      <button class="tab tab-value" onclick="showTab(this, 'value')">Value</button>
      <button class="tab" onclick="showTab(this, 'prep')">Preparation (teacher questions)</button>
      <button class="tab" onclick="showTab(this, 'part')">Participation (voluntary)</button>
    </div>

    <div id="tab-transcript" class="tab-content active">
      <table>
        <thead><tr><th style="width:60px">Time</th><th style="width:120px">Speaker</th><th style="width:160px">Type</th><th>Text</th></tr></thead>
        <tbody>{transcript_rows}</tbody>
      </table>
    </div>

    <div id="tab-value" class="tab-content">
      {value_table}
    </div>

    <div id="tab-prep" class="tab-content">
      {prep_table}
    </div>

    <div id="tab-part" class="tab-content">
      {part_table}
    </div>
  </div>'''}

</div>

<script>
function showTab(btn, name) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}}
</script>
</body>
</html>"""

    out_file = CLASSES_OUT / f"{sid}.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    return out_file


def main():
    print("Generando páginas de detalle por clase...")
    n = 0
    for sd in sorted(DATA_DIR.iterdir()):
        if not sd.is_dir():
            continue
        out = render_class_html(sd.name)
        if out:
            print(f"  ✅ {out.relative_to(REPO_ROOT)}")
            n += 1
    print(f"\n{n} páginas generadas en {CLASSES_OUT.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    main()
