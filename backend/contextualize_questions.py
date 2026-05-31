#!/usr/bin/env python3
"""
Re-organiza las preguntas contestadas usando el CONTEXTO de la transcripción.

Cada pregunta del profesor en la transcripción suele quedar como un fragmento
suelto ("Right?", "The university?"). Este script toma la ventana de diálogo
alrededor de cada pregunta contestada y deja que Gemini la reformule en:
  - una pregunta clara y contextualizada (qué estaba preguntando realmente)
  - la respuesta del alumno consolidada y legible

El responder y el puntaje 1–6 NO se inventan: salen de component_a.json (rúbrica).

Uso:
    python3 backend/contextualize_questions.py <session_id>
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "clases"

WINDOW_BEFORE = 5   # utterances de contexto previo
WINDOW_AFTER = 5    # utterances posteriores (para capturar respuesta completa)


def load_env() -> None:
    if os.getenv("GOOGLE_API_KEY") and not os.getenv("GOOGLE_API_KEY").startswith('"'):
        return
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


def build_context_blocks(session_dir: Path) -> list[dict]:
    """Para cada pregunta contestada, arma su ventana de transcripción."""
    analysis = json.loads((session_dir / "analysis.json").read_text(encoding="utf-8"))
    ca = json.loads((session_dir / "component_a.json").read_text(encoding="utf-8"))
    ft = analysis.get("full_transcription", [])
    prep_rows = ca.get("preparation", {}).get("rows", [])

    answered = [r for r in prep_rows if r.get("responder")]

    blocks = []
    for r in answered:
        ts = r.get("timestamp")
        # localizar el índice de la pregunta en la transcripción
        idx = next((i for i, u in enumerate(ft)
                    if u.get("timestamp") == ts and u.get("type") == "teacher_question"), None)
        if idx is None:
            idx = next((i for i, u in enumerate(ft) if u.get("timestamp") == ts), None)
        if idx is None:
            window = []
        else:
            lo = max(0, idx - WINDOW_BEFORE)
            hi = min(len(ft), idx + WINDOW_AFTER + 1)
            window = ft[lo:hi]
        blocks.append({
            "timestamp": ts,
            "responder": r["responder"],
            "score": r["scores"].get(r["responder"]),
            "raw_question": r.get("question", ""),
            "context": [
                {"t": u.get("timestamp"), "spk": u.get("speaker"),
                 "type": u.get("type"), "text": u.get("text", "")}
                for u in window
            ],
        })
    return blocks


def contextualize(blocks: list[dict]) -> list[dict]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    payload = []
    for i, b in enumerate(blocks):
        ctx = "\n".join(f'    [{u["t"]}] {u["spk"]} ({u["type"]}): {u["text"]}'
                        for u in b["context"])
        payload.append(
            f'#{i} | timestamp {b["timestamp"]} | responder {b["responder"]}\n'
            f'  PREGUNTA_CRUDA: "{b["raw_question"]}"\n'
            f'  CONTEXTO:\n{ctx}'
        )
    listado = "\n\n".join(payload)

    prompt = f"""Eres asistente de una profesora universitaria (Ileana) en un seminario en inglés
sobre comercialización de tecnología (GTC/ICP). Abajo hay varias preguntas que ella hizo;
cada una viene con su transcripción de contexto (lo que se dijo antes y después).

Las preguntas crudas suelen ser fragmentos sin sentido por sí solos ("Right?", "The university?").
Tu trabajo es, USANDO EL CONTEXTO, reescribir cada una de forma clara y autocontenida:

Para cada item devuelve:
- "question_clear": la pregunta reformulada en inglés, clara y con el contexto necesario para
  entenderse sola (qué estaba preguntando realmente la profesora sobre el tema). No inventes
  información que no esté en el contexto.
- "answer_clear": la respuesta del alumno consolidada y legible en inglés (junta las
  intervenciones de respuesta si están partidas; corrige muletillas pero respeta el sentido).
- "topic": tema en 2-4 palabras (inglés).
- "is_substantive": true si es una pregunta de valor académico sobre el tema; false si es
  solo confirmación/logística/muletilla.

Mantén el mismo orden e índice.

ITEMS:
{listado}

RESPONDE ÚNICAMENTE CON JSON VÁLIDO:
{{
  "items": [
    {{"index": 0, "question_clear": "...", "answer_clear": "...", "topic": "...", "is_substantive": true}}
  ]
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[types.Part.from_text(text=prompt)],
    )
    text = response.text.strip()
    m = re.search(r'```json\s*([\s\S]*?)\s*```', text) or re.search(r'```\s*([\s\S]*?)\s*```', text)
    if m:
        text = m.group(1)
    else:
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            text = m.group()
    return json.loads(text).get("items", [])


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python3 backend/contextualize_questions.py <session_id>")
        sys.exit(1)
    sid = sys.argv[1]
    session_dir = DATA_DIR / sid
    load_env()

    blocks = build_context_blocks(session_dir)
    print(f"📥 {len(blocks)} preguntas contestadas en {sid}")
    print("🤖 Reorganizando con contexto (Gemini)...\n")

    # Batching: clases grandes truncan la respuesta de Gemini. Procesamos por lotes.
    BATCH_SIZE = 30
    by_idx = {}
    for start in range(0, len(blocks), BATCH_SIZE):
        batch = blocks[start:start + BATCH_SIZE]
        if len(blocks) > BATCH_SIZE:
            print(f"   lote {start//BATCH_SIZE + 1}: preguntas {start+1}-{start+len(batch)}")
        items = contextualize(batch)
        for pos, it in enumerate(items):
            local = it.get("index", pos)
            by_idx[start + local] = it  # remapear índice local → global

    questions = []
    print("=" * 80)
    for i, b in enumerate(blocks):
        it = by_idx.get(i, {})
        sc = b["score"] if b["score"] is not None else "—"
        mark = "⭐" if it.get("is_substantive") else "·"
        print(f"{mark} #{i+1}  ⏱ {b['timestamp']}  [{it.get('topic','?')}]  👤 {b['responder']}  🔢 {sc}")
        print(f"   ❓ {it.get('question_clear', b['raw_question'])}")
        print(f"   💬 {it.get('answer_clear', '')}")
        print()
        questions.append({
            "timestamp": b["timestamp"],
            "topic": it.get("topic", ""),
            "question": it.get("question_clear", b["raw_question"]),
            "raw_question": b["raw_question"],
            "answered_by": b["responder"],
            "score": b["score"],
            "response_text": it.get("answer_clear", ""),
            "is_substantive": bool(it.get("is_substantive", False)),
        })

    out = {
        "session": sid,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "count": len(questions),
        "questions": questions,
    }
    out_file = session_dir / "value_questions.json"
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 Guardado: {out_file.relative_to(REPO_ROOT)}  ({len(questions)} preguntas)")


if __name__ == "__main__":
    main()
