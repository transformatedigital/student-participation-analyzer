#!/usr/bin/env python3
"""
Orquestador del pipeline completo para procesar una clase nueva:

  1. Recibe ruta del audio fuente + fecha de clase (session_id)
  2. Crea estructura de carpetas data/clases/{session_id}/
  3. Fragmenta el audio en bloques de 5 min con ffmpeg
  4. Transcribe cada bloque con Gemini 2.5-flash (con caché por bloque)
  5. Genera analysis.json compatible con el resto del pipeline
  6. Aplica score_with_rubric.py (rúbrica 1–6)
  7. Genera build_component_a.py (Excel + JSON con escenarios A y B)

Uso:
    python3 backend/process_class.py <audio_path> <session_id>
    python3 backend/process_class.py /tmp/clase.m4a 2026-05-09

Requisitos:
    - GOOGLE_API_KEY exportada (Google AI Studio)
    - ffmpeg instalado
    - venv activado con google-genai y openpyxl
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "clases"

# Hablantes esperados (mismos alumnos en todas las clases)
DEFAULT_STUDENTS = ["Aryang", "Mega", "Chilaka", "Grace", "Sthepen"]
TEACHER = "Ileana"

BLOCK_SECONDS = 300  # 5 min


def ensure_session_dir(session_id):
    """Crea estructura de carpetas para la clase."""
    sdir = DATA_DIR / session_id
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "audio_blocks_5min_cleaned").mkdir(exist_ok=True)
    (sdir / "transcript_cache").mkdir(exist_ok=True)
    return sdir


def fragment_audio(audio_path, blocks_dir):
    """Divide el audio en bloques de 5 min usando ffmpeg.

    Devuelve lista de info de bloques compatible con blocks_5min_info.json.
    """
    audio_path = Path(audio_path).expanduser().resolve()
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio no encontrado: {audio_path}")

    # Obtener duración total
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1", str(audio_path)
    ]).decode().strip()
    total_seconds = float(out)
    print(f"📊 Audio fuente: {audio_path.name}")
    print(f"   Duración: {total_seconds/60:.1f} min ({total_seconds:.1f}s)")

    # Limpiar bloques previos (si existen)
    for f in blocks_dir.glob("block_*.m4a"):
        f.unlink()

    # Fragmentar
    n_blocks = int(total_seconds // BLOCK_SECONDS) + (1 if total_seconds % BLOCK_SECONDS > 5 else 0)
    print(f"   Fragmentando en {n_blocks} bloques de 5 min...")

    blocks_info = []
    for i in range(n_blocks):
        start = i * BLOCK_SECONDS
        end = min((i + 1) * BLOCK_SECONDS, total_seconds)
        duration = end - start
        block_num = i + 1
        filename = f"block_{block_num:02d}_{start:05d}_{int(end):05d}.m4a"
        out_path = blocks_dir / filename

        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(audio_path),
            "-ss", str(start), "-t", str(duration),
            "-c", "copy", str(out_path)
        ]
        subprocess.run(cmd, check=True)

        start_time = f"{int(start)//60:02d}:{int(start)%60:02d}"
        end_time = f"{int(end)//60:02d}:{int(end)%60:02d}"
        blocks_info.append({
            "block": block_num,
            "file": filename,
            "start": int(start),
            "end": int(end),
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
        })
        print(f"   ✓ Block {block_num:02d} ({start_time}-{end_time}) → {filename}")

    info_file = blocks_dir / "blocks_5min_info.json"
    with open(info_file, "w") as f:
        json.dump(blocks_info, f, indent=2)
    return blocks_info


def transcribe_block(client, audio_path, block_num, time_range, start_seconds, students):
    """Transcribe un bloque con Gemini 2.5-flash."""
    from google.genai import types

    print(f"   📤 Subiendo block {block_num:02d}...", flush=True)
    uploaded = client.files.upload(
        file=str(audio_path),
        config=types.UploadFileConfig(mime_type="audio/mp4")
    )
    file_name = uploaded.name
    while True:
        info = client.files.get(name=file_name)
        if info.state.name == "ACTIVE":
            break
        if info.state.name == "FAILED":
            client.files.delete(name=file_name)
            return None
        time.sleep(2)

    speakers_section = "\n".join(f"- {s.upper()}: Estudiante" for s in students)
    prompt = f"""Transcribe LITERALMENTE este segmento de audio de una clase universitaria.

SEGMENTO: {time_range} del audio total.

HABLANTES EN LA CLASE:
- {TEACHER.upper()}: La profesora/instructora. Habla la mayoría del tiempo. Dirige la clase.
{speakers_section}

INSTRUCCIONES ESTRICTAS:
1. Transcribe TODO lo que se dice, palabra por palabra, sin resumir
2. Identifica el speaker de cada intervención
3. Registra el timestamp en MM:SS desde el inicio de ESTE bloque
4. Clasifica cada intervención:
   - "teacher_question" → {TEACHER} hace una pregunta directa a los alumnos
   - "teacher_statement" → {TEACHER} explica, instruye, o comenta (no pregunta)
   - "student_response" → Alumno respondiendo a pregunta de {TEACHER}
   - "student_question" → Alumno preguntando a {TEACHER}
   - "student_comment" → Alumno haciendo comentario o aportación
5. Si no puedes identificar el speaker, usa "UNKNOWN"
6. Si no se entiende una palabra, escribe [inaudible]
7. Si una pregunta del profesor está dirigida a un alumno específico, agrega "directed_to": "NombreAlumno". Si es abierta a todo el grupo, "directed_to": "Class"

RESPONDE ÚNICAMENTE CON JSON VÁLIDO, sin texto antes ni después:
{{
  "block": {block_num},
  "time_range": "{time_range}",
  "utterances": [
    {{
      "timestamp": "MM:SS",
      "speaker": "{TEACHER.upper()}",
      "type": "teacher_question",
      "directed_to": "ARYANG",
      "text": "texto literal"
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
    try:
        client.files.delete(name=file_name)
    except Exception:
        pass

    text = response.text.strip()
    if "```json" in text:
        m = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if m: text = m.group(1)
    elif "```" in text:
        m = re.search(r'```\s*([\s\S]*?)\s*```', text)
        if m: text = m.group(1)
    else:
        m = re.search(r'\{[\s\S]*\}', text)
        if m: text = m.group()

    data = json.loads(text)
    for u in data.get("utterances", []):
        rel = u.get("timestamp", "00:00")
        try:
            mm, ss = rel.split(":")
            abs_s = start_seconds + int(mm) * 60 + int(ss)
            u["timestamp_abs"] = f"{abs_s//60:02d}:{abs_s%60:02d}"
        except Exception:
            u["timestamp_abs"] = rel
    return data


def transcribe_all_blocks(blocks_info, blocks_dir, cache_dir, students):
    from google import genai
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY no configurada. Exporta con: export GOOGLE_API_KEY='tu-key'")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    print(f"\n📡 Gemini configurada. Procesando {len(blocks_info)} bloques...\n")

    all_blocks = []
    for info in blocks_info:
        n = info["block"]
        cache = cache_dir / f"block_{n:02d}.json"
        if cache.exists():
            print(f"📂 Block {n:02d} ({info['start_time']}-{info['end_time']}): caché")
            with open(cache, encoding="utf-8") as f:
                all_blocks.append(json.load(f))
            continue

        audio = blocks_dir / info["file"]
        time_range = f"{info['start_time']}-{info['end_time']}"
        print(f"⏳ Block {n:02d} ({time_range})...")
        try:
            data = transcribe_block(client, audio, n, time_range, info["start"], students)
            if data:
                with open(cache, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                all_blocks.append(data)
                u_n = len(data.get("utterances", []))
                print(f"   ✅ {u_n} utterances")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
        time.sleep(4)

    return all_blocks


def build_analysis_json(all_blocks, session_dir, students):
    """Construye analysis.json compatible con build_component_a.py."""
    teacher_questions = []
    student_contributions = []
    full_transcription = []
    qid = 1
    cid = 1

    student_set = {s.upper() for s in students}
    student_titles = {s.upper(): s for s in students}

    # Para emparejar pregunta+respuesta cuando una pregunta se dirige a un alumno
    last_teacher_question = None

    for block in all_blocks:
        for u in block.get("utterances", []):
            sp = u.get("speaker", "").strip()
            ttype = u.get("type", "")
            text = u.get("text", "")
            ts = u.get("timestamp_abs") or u.get("timestamp", "")
            full_transcription.append({
                "timestamp": ts,
                "speaker": sp,
                "type": ttype,
                "text": text,
                "block": block.get("block"),
            })
            if ttype == "teacher_question":
                directed = (u.get("directed_to") or "").strip()
                target = directed.title() if directed and directed.lower() not in ("class", "everyone", "all", "open", "") else "Class"
                tq = {
                    "id": qid,
                    "timestamp": ts,
                    "question": text,
                    "directed_to": target,
                    "block": block.get("block"),
                    "student_response": None,
                }
                last_teacher_question = tq
                teacher_questions.append(tq)
                qid += 1
            elif ttype == "student_response":
                student = student_titles.get(sp.upper())
                if student and last_teacher_question:
                    last_teacher_question["student_response"] = {
                        "student": student,
                        "response": text,
                        "quality_score": "C",  # placeholder, se re-evalúa con la rúbrica
                    }
                    last_teacher_question = None
                # También se contabiliza como contribución (voluntaria si no hay pregunta dirigida pendiente)
                if student:
                    student_contributions.append({
                        "id": cid,
                        "timestamp": ts,
                        "student": student,
                        "type": "voluntary_response",
                        "content": text,
                        "quality_score": "C",
                        "block": block.get("block"),
                    })
                    cid += 1
            elif ttype in ("student_question", "student_comment"):
                student = student_titles.get(sp.upper())
                if student:
                    sc_type = "question_to_teacher" if ttype == "student_question" else "comment"
                    student_contributions.append({
                        "id": cid,
                        "timestamp": ts,
                        "student": student,
                        "type": sc_type,
                        "content": text,
                        "quality_score": "C",
                        "block": block.get("block"),
                    })
                    cid += 1

    analysis = {
        "session": {
            "id": session_dir.name,
            "date": session_dir.name,
            "instructor": TEACHER,
            "students": students,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "full_transcription": full_transcription,
        "teacher_questions": teacher_questions,
        "student_contributions": student_contributions,
    }
    return analysis


def write_metadata_and_speakers(session_dir, students, n_segments):
    """Crea metadata.json y speakers.json mínimos."""
    sid = session_dir.name
    metadata = {
        "session_id": sid,
        "date": sid,
        "course": "Graduate Seminar",
        "instructor": f"Dr. {TEACHER}",
        "audio_file": "audio_unificado.m4a",
        "status": "analyzed",
        "total_segments": n_segments,
        "speakers_count": 1 + len(students),
    }
    with open(session_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    speakers = {
        "speakers": [
            {"id": "speaker_1", "role": "Teacher", "name": f"Dr. {TEACHER}",
             "color": "emerald", "percentage": 80}
        ] + [
            {"id": f"speaker_{i+2}", "role": "Student", "name": s, "color": "slate"}
            for i, s in enumerate(students)
        ]
    }
    with open(session_dir / "speakers.json", "w") as f:
        json.dump(speakers, f, indent=2)


def run_pipeline(audio_path, session_id, students=None, skip_transcription=False):
    students = students or DEFAULT_STUDENTS
    session_dir = ensure_session_dir(session_id)
    blocks_dir = session_dir / "audio_blocks_5min_cleaned"
    cache_dir = session_dir / "transcript_cache"

    print(f"\n{'='*70}")
    print(f"  PIPELINE COMPONENTE A — Clase {session_id}")
    print(f"{'='*70}\n")

    # 1. Fragmentar (no aplica con --skip-transcription: se reutiliza el cache existente)
    blocks_info = []
    info_file = blocks_dir / "blocks_5min_info.json"
    if skip_transcription:
        if not any(cache_dir.glob("block_*.json")):
            print("❌ Skip-transcripción pero no existe transcript_cache previo.")
            sys.exit(1)
    elif info_file.exists() and not audio_path:
        with open(info_file) as f:
            blocks_info = json.load(f)
        print(f"📂 Usando bloques existentes: {len(blocks_info)}")
    else:
        if not audio_path:
            print("❌ No hay bloques previos y no se pasó audio fuente.")
            sys.exit(1)
        blocks_info = fragment_audio(audio_path, blocks_dir)

    # 2. Transcribir
    if skip_transcription:
        print("\n⏭  Skip transcripción (usando cache existente)")
        all_blocks = []
        for f in sorted(cache_dir.glob("block_*.json")):
            with open(f, encoding="utf-8") as fh:
                all_blocks.append(json.load(fh))
    else:
        all_blocks = transcribe_all_blocks(blocks_info, blocks_dir, cache_dir, students)

    if not all_blocks:
        print("❌ No hay transcripciones para procesar.")
        sys.exit(1)

    # 3. Construir analysis.json
    print(f"\n📝 Construyendo analysis.json...")
    analysis = build_analysis_json(all_blocks, session_dir, students)
    with open(session_dir / "analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"   ✅ {len(analysis['full_transcription'])} segments, "
          f"{len(analysis['teacher_questions'])} teacher questions, "
          f"{len(analysis['student_contributions'])} contributions")

    write_metadata_and_speakers(session_dir, students, len(analysis["full_transcription"]))

    # 4 y 5: scoring y construcción se hacen llamando a los scripts existentes
    # con session_id parametrizable. Esos scripts ya existen pero hardcodean la fecha.
    # Mejor invocarlos como módulos pasando session_id por env var.
    print(f"\n🎯 Aplicando rúbrica 1–6 (score_with_rubric.py)...")
    env = os.environ.copy()
    env["SESSION_ID"] = session_id
    subprocess.run([sys.executable, str(REPO_ROOT / "backend" / "score_with_rubric.py")], env=env, check=True)

    print(f"\n📊 Generando JSON + Excel (build_component_a.py)...")
    subprocess.run([sys.executable, str(REPO_ROOT / "backend" / "build_component_a.py")], env=env, check=True)

    print(f"\n{'='*70}")
    print(f"  ✅ CLASE {session_id} PROCESADA")
    print(f"{'='*70}")
    print(f"  📁 {session_dir.relative_to(REPO_ROOT)}/")
    print(f"     ├── analysis.json")
    print(f"     ├── component_a.json")
    print(f"     ├── manual_scores_1_6.json")
    print(f"     └── Component_A_{session_id}.xlsx")


def main():
    parser = argparse.ArgumentParser(description="Procesa una clase completa")
    parser.add_argument("audio_path", nargs="?", help="Ruta al audio fuente (.m4a/.mp4/.wav)")
    parser.add_argument("session_id", help="ID de sesión (formato YYYY-MM-DD)")
    parser.add_argument("--skip-transcription", action="store_true",
                        help="Saltar transcripción (usar cache existente)")
    parser.add_argument("--students", help="Lista de alumnos separados por coma (override default)")
    args = parser.parse_args()

    students = args.students.split(",") if args.students else DEFAULT_STUDENTS
    run_pipeline(args.audio_path, args.session_id, students, args.skip_transcription)


if __name__ == "__main__":
    main()
