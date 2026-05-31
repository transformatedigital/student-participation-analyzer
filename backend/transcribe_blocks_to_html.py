#!/usr/bin/env python3
"""
Transcribe todos los bloques de audio con Gemini 2.5-flash y genera HTML con colores:
- ROJO: Preguntas de Ileana a los alumnos
- AZUL: Participaciones/preguntas de alumnos
- GRIS: Explicaciones de Ileana
"""

import json
import os
import sys
import time
import re
from pathlib import Path
from google import genai
from google.genai import types

api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("❌ Error: Configura GOOGLE_API_KEY")
    print("   export GOOGLE_API_KEY='tu-api-key'")
    sys.exit(1)

client = genai.Client(api_key=api_key)
print("✅ Gemini API configurada (google-genai v1.x)\n")

# Paths
blocks_dir = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/audio_blocks_5min_cleaned")
cache_dir = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/transcript_cache")
html_output = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/transcripcion_completa.html")
blocks_info_file = blocks_dir / "blocks_5min_info.json"

cache_dir.mkdir(exist_ok=True)

with open(blocks_info_file) as f:
    blocks_info = json.load(f)

print(f"📊 Bloques a procesar: {len(blocks_info)}\n")


# ============================================================
# TRANSCRIPCIÓN CON GEMINI
# ============================================================

def transcribe_block(audio_path, block_num, start_time, end_time, start_seconds):
    """Transcribe un bloque verbatim con diarización"""
    print(f"📤 Block {block_num:02d} ({start_time}-{end_time}): Subiendo...", flush=True)

    try:
        # Upload file using path directly
        uploaded = client.files.upload(
            file=audio_path,
            config=types.UploadFileConfig(mime_type="audio/mp4")
        )

        # Wait for processing
        file_name = uploaded.name
        while True:
            file_info = client.files.get(name=file_name)
            if file_info.state.name == "ACTIVE":
                break
            elif file_info.state.name == "FAILED":
                print(f"   ❌ Gemini rechazó el archivo")
                client.files.delete(name=file_name)
                return None
            time.sleep(2)

        print(f"   ⏳ Analizando con Gemini...", flush=True)

        prompt = f"""Transcribe LITERALMENTE este segmento de audio de una clase universitaria.

SEGMENTO: {start_time} a {end_time} del total de 59:30 minutos.

HABLANTES EN LA CLASE:
- ILEANA: La profesora/instructora. Habla la mayoría del tiempo. Dirige la clase.
- ARYANG: Estudiante (voz masculina, tono medio)
- GRACE: Estudiante (voz más aguda/femenina)
- CHILAKA: Estudiante
- MEGA: Estudiante
- STHEPEN: Estudiante (voz más grave)

INSTRUCCIONES ESTRICTAS:
1. Transcribe TODO lo que se dice, palabra por palabra, sin resumir
2. Identifica el speaker de cada intervención
3. Registra el timestamp en MM:SS desde el inicio de ESTE bloque
4. Clasifica cada intervención:
   - "teacher_question" → Ileana hace una pregunta directa a los alumnos
   - "teacher_statement" → Ileana explica, instruye, o comenta (no pregunta)
   - "student_response" → Alumno respondiendo a pregunta de Ileana
   - "student_question" → Alumno preguntando a Ileana
   - "student_comment" → Alumno haciendo comentario o aportación
5. Si no puedes identificar el speaker, usa "UNKNOWN"
6. Si no se entiende una palabra, escribe [inaudible]
7. OMITE solo: risas sueltas sin contenido, "mm-hmm" de afirmación corta sin significado
8. INCLUYE: todo lo que tenga contenido semántico aunque sea una sola oración

RESPONDE ÚNICAMENTE CON JSON VÁLIDO, sin texto antes ni después:
{{
  "block": {block_num},
  "time_range": "{start_time}-{end_time}",
  "utterances": [
    {{
      "timestamp": "MM:SS",
      "speaker": "ILEANA",
      "type": "teacher_statement",
      "text": "texto literal aquí"
    }},
    {{
      "timestamp": "MM:SS",
      "speaker": "ARYANG",
      "type": "student_response",
      "text": "texto literal aquí"
    }}
  ]
}}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_uri(file_uri=uploaded.uri, mime_type="audio/mp4"),
                types.Part.from_text(text=prompt)
            ]
        )

        # Cleanup uploaded file
        try:
            client.files.delete(name=file_name)
        except:
            pass

        text = response.text.strip()

        # Extract JSON (handle markdown code blocks)
        if "```json" in text:
            m = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if m:
                text = m.group(1)
        elif "```" in text:
            m = re.search(r'```\s*([\s\S]*?)\s*```', text)
            if m:
                text = m.group(1)
        else:
            m = re.search(r'\{[\s\S]*\}', text)
            if m:
                text = m.group()

        block_data = json.loads(text)

        # Add absolute timestamps
        for u in block_data.get('utterances', []):
            rel_ts = u.get('timestamp', '00:00')
            try:
                parts = rel_ts.split(':')
                rel_sec = int(parts[0]) * 60 + int(parts[1])
                abs_sec = start_seconds + rel_sec
                u['timestamp_abs'] = f"{abs_sec // 60:02d}:{abs_sec % 60:02d}"
            except:
                u['timestamp_abs'] = start_time

        utterances = block_data.get('utterances', [])
        q_count = sum(1 for u in utterances if u.get('type') == 'teacher_question')
        s_count = sum(1 for u in utterances if 'student' in u.get('type', ''))
        print(f"   ✅ {len(utterances)} líneas | {q_count} preguntas Ileana | {s_count} participaciones alumnos")

        return block_data

    except json.JSONDecodeError as e:
        print(f"   ⚠️  Error JSON bloque {block_num}: {e}")
        try:
            print(f"   Respuesta parcial: {response.text[:400]}")
        except:
            pass
        return None
    except Exception as e:
        print(f"   ❌ Error bloque {block_num}: {e}")
        return None


# ============================================================
# PROCESAMIENTO DE BLOQUES
# ============================================================

all_blocks = []

for block_info in blocks_info:
    block_num = block_info['block']
    block_file = blocks_dir / block_info['file']
    start_time = block_info['start_time']
    end_time = block_info['end_time']
    start_seconds = block_info['start']

    cache_file = cache_dir / f"block_{block_num:02d}.json"

    if cache_file.exists():
        print(f"📂 Block {block_num:02d} ({start_time}-{end_time}): Cargando desde caché")
        with open(cache_file, encoding='utf-8') as f:
            block_data = json.load(f)
    else:
        if not block_file.exists():
            print(f"⚠️  Block {block_num}: Archivo no encontrado: {block_file.name}")
            continue

        block_data = transcribe_block(str(block_file), block_num, start_time, end_time, start_seconds)

        if block_data:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(block_data, f, indent=2, ensure_ascii=False)
        else:
            print(f"   ⚠️  Block {block_num}: No se pudo procesar, continuando...")
            time.sleep(4)
            continue

        time.sleep(4)

    if block_data:
        all_blocks.append(block_data)

print(f"\n✅ Bloques listos: {len(all_blocks)}/{len(blocks_info)}\n")

if not all_blocks:
    print("❌ No hay bloques procesados. Verifica errores arriba.")
    sys.exit(1)


# ============================================================
# GENERACIÓN DE HTML
# ============================================================

def type_to_css(utype):
    if utype == 'teacher_question':
        return 'teacher-question'
    elif utype == 'teacher_statement':
        return 'teacher-statement'
    elif utype in ('student_response', 'student_question', 'student_comment'):
        return 'student'
    return 'other'

def type_to_label(utype, speaker):
    if utype == 'teacher_question':
        return f'❓ QUESTION → {speaker}'
    elif utype == 'teacher_statement':
        return f'📖 {speaker}'
    elif utype == 'student_response':
        return f'💬 RESPONSE — {speaker}'
    elif utype == 'student_question':
        return f'❓ QUESTION — {speaker}'
    elif utype == 'student_comment':
        return f'💬 CONTRIBUTION — {speaker}'
    return speaker

total_utterances = sum(len(b.get('utterances', [])) for b in all_blocks)
total_teacher_q = sum(
    sum(1 for u in b.get('utterances', []) if u.get('type') == 'teacher_question')
    for b in all_blocks
)
total_student_parts = sum(
    sum(1 for u in b.get('utterances', []) if 'student' in u.get('type', ''))
    for b in all_blocks
)

html_blocks = ""
for block in all_blocks:
    block_num = block['block']
    time_range = block['time_range']
    utterances = block.get('utterances', [])

    block_q = sum(1 for u in utterances if u.get('type') == 'teacher_question')
    block_s = sum(1 for u in utterances if 'student' in u.get('type', ''))

    rows = ""
    for u in utterances:
        utype = u.get('type', 'other')
        css = type_to_css(utype)
        speaker = u.get('speaker', 'UNKNOWN')
        text = u.get('text', '').replace('<', '&lt;').replace('>', '&gt;')
        ts_abs = u.get('timestamp_abs', '')
        label = type_to_label(utype, speaker)

        rows += f"""
        <tr class="{css}">
          <td class="ts">{ts_abs}</td>
          <td class="label">{label}</td>
          <td class="speech">{text}</td>
        </tr>"""

    html_blocks += f"""
    <section class="block" id="block-{block_num}">
      <div class="block-header">
        <span class="block-num">Block {block_num:02d}</span>
        <span class="block-time">⏱ {time_range}</span>
        <span class="block-stats">
          <span class="stat-q">❓ {block_q} Ileana's questions</span>
          <span class="stat-s">💬 {block_s} student participations</span>
        </span>
      </div>
      <table class="transcript-table">
        <thead>
          <tr><th>Time</th><th>Speaker / Type</th><th>Transcription</th></tr>
        </thead>
        <tbody>{rows}
        </tbody>
      </table>
    </section>
"""

nav_items = ""
for b in all_blocks:
    nav_items += f'<a href="#block-{b["block"]}" class="nav-btn">B{b["block"]:02d}<br><small>{b["time_range"]}</small></a>'

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Class Transcription — April 7, 2026</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f0f0f; color: #e8e8e8; font-size: 14px; }}
    .top-bar {{
      background: #1a1a2e; border-bottom: 2px solid #4a4a8a;
      padding: 16px 24px; position: sticky; top: 0; z-index: 100;
    }}
    .top-bar h1 {{ font-size: 20px; color: #a0a8ff; margin-bottom: 6px; }}
    .top-stats {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; }}
    .stat-pill {{ background: #2a2a4a; padding: 4px 12px; border-radius: 20px; }}
    .stat-pill.red {{ background: #3d1515; color: #ff8080; }}
    .stat-pill.blue {{ background: #0d2a3d; color: #80c0ff; }}
    .stat-pill.green {{ background: #0d2d1a; color: #70e0a0; }}
    .legend {{
      background: #161616; padding: 10px 24px;
      display: flex; gap: 24px; flex-wrap: wrap; border-bottom: 1px solid #333; font-size: 13px;
    }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; }}
    .legend-dot {{ width: 14px; height: 14px; border-radius: 3px; }}
    .dot-red {{ background: #8b1a1a; border: 1px solid #ff4040; }}
    .dot-blue {{ background: #0d2d4a; border: 1px solid #4090ff; }}
    .dot-gray {{ background: #2a2a2a; border: 1px solid #555; }}
    .block-nav {{
      background: #111; padding: 10px 24px;
      display: flex; gap: 6px; flex-wrap: wrap; border-bottom: 1px solid #333;
    }}
    .nav-btn {{
      background: #222; color: #ccc; text-decoration: none;
      border: 1px solid #444; border-radius: 6px; padding: 5px 8px;
      font-size: 11px; text-align: center; line-height: 1.4; transition: background 0.2s;
    }}
    .nav-btn:hover {{ background: #4a4a8a; color: white; }}
    .content {{ padding: 24px; max-width: 1300px; margin: 0 auto; }}
    .block {{
      background: #161616; border: 1px solid #2a2a2a; border-radius: 10px;
      margin-bottom: 28px; overflow: hidden;
    }}
    .block-header {{
      background: #1e1e3a; padding: 12px 20px;
      display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
    }}
    .block-num {{ font-size: 17px; font-weight: bold; color: #8888ff; }}
    .block-time {{ color: #888; font-size: 13px; }}
    .block-stats {{ margin-left: auto; display: flex; gap: 12px; }}
    .stat-q {{ color: #ff8080; font-size: 12px; }}
    .stat-s {{ color: #80aaff; font-size: 12px; }}
    .transcript-table {{ width: 100%; border-collapse: collapse; }}
    .transcript-table thead th {{
      background: #1c1c1c; color: #666; font-size: 11px; text-transform: uppercase;
      letter-spacing: 0.05em; padding: 8px 14px; text-align: left;
      border-bottom: 1px solid #2a2a2a;
    }}
    .transcript-table tbody tr {{ border-bottom: 1px solid #1e1e1e; }}
    .transcript-table tbody tr:last-child {{ border-bottom: none; }}
    tr.teacher-question {{
      background: rgba(139, 26, 26, 0.22);
      border-left: 4px solid #cc3333;
    }}
    tr.teacher-question:hover {{ background: rgba(139, 26, 26, 0.38); }}
    tr.teacher-statement {{ background: transparent; }}
    tr.teacher-statement:hover {{ background: rgba(255,255,255,0.03); }}
    tr.student {{
      background: rgba(13, 55, 95, 0.28);
      border-left: 4px solid #3377cc;
    }}
    tr.student:hover {{ background: rgba(13, 55, 95, 0.42); }}
    tr.other {{ background: rgba(80, 80, 20, 0.12); }}
    td.ts {{
      padding: 10px 14px; white-space: nowrap; font-family: monospace;
      font-size: 12px; color: #555; width: 65px; vertical-align: top;
    }}
    td.label {{
      padding: 10px 14px; width: 210px; vertical-align: top; font-size: 12px;
    }}
    tr.teacher-question td.label {{ color: #ff8888; font-weight: 600; }}
    tr.student td.label {{ color: #80aaff; font-weight: 600; }}
    tr.teacher-statement td.label {{ color: #666; }}
    td.speech {{
      padding: 10px 14px; line-height: 1.65; font-size: 14px; vertical-align: top;
    }}
    tr.teacher-question td.speech {{ color: #ffe0e0; }}
    tr.student td.speech {{ color: #d0e8ff; }}
    tr.teacher-statement td.speech {{ color: #c8c8c8; }}
    .footer {{ text-align: center; color: #444; font-size: 12px; margin-top: 16px; padding-bottom: 40px; }}
  </style>
</head>
<body>

<div class="top-bar">
  <h1>🎤 Class Transcription — April 7, 2026</h1>
  <div class="top-stats">
    <span class="stat-pill green">📊 {len(all_blocks)}/12 blocks processed · {total_utterances} utterances</span>
    <span class="stat-pill red">❓ {total_teacher_q} Ileana's questions</span>
    <span class="stat-pill blue">💬 {total_student_parts} student participations</span>
  </div>
</div>

<div class="legend">
  <div class="legend-item"><div class="legend-dot dot-red"></div><span>Ileana's question to students</span></div>
  <div class="legend-item"><div class="legend-dot dot-blue"></div><span>Student participation / response / question</span></div>
  <div class="legend-item"><div class="legend-dot dot-gray"></div><span>Ileana's explanation or instruction</span></div>
</div>

<div class="block-nav">
  {nav_items}
</div>

<div class="content">
  {html_blocks}
  <p class="footer">Generated: 2026-04-29 · Gemini 2.5-flash · {len(all_blocks)} blocks of 5 min</p>
</div>

</body>
</html>
"""

with open(html_output, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = html_output.stat().st_size / 1024
print(f"✅ HTML generado: {html_output}")
print(f"   Tamaño: {size_kb:.0f} KB")
print(f"   Bloques: {len(all_blocks)}")
print(f"   Total utterances: {total_utterances}")
print(f"   Preguntas de Ileana (rojo): {total_teacher_q}")
print(f"   Participaciones alumnos (azul): {total_student_parts}")
print(f"\n👉 Abrir en navegador:")
print(f"   open \"{html_output}\"")
