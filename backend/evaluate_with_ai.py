#!/usr/bin/env python3
"""
Evalúa todas las participaciones usando Gemini con las rúbricas A y B.
Guarda resultados en ai_evaluations.json para usar en el dashboard.
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
    print("❌ GOOGLE_API_KEY not set")
    sys.exit(1)

client = genai.Client(api_key=api_key)

cache_dir   = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/transcript_cache")
analysis_f  = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis.json")
output_f    = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/ai_evaluations.json")

# ── Load participations (same logic as dashboard) ────────────────────────────
all_blocks = []
for f in sorted(cache_dir.glob("block_*.json")):
    with open(f, encoding="utf-8") as fh:
        all_blocks.append(json.load(fh))

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
                context = utterances[j].get("text", "")[:300]
                break
        ts = u.get("timestamp_abs", u.get("timestamp", ""))
        participations.append({
            "id": len(participations) + 1,
            "block": bnum,
            "timestamp": ts,
            "speaker": sp,
            "type": u["type"],
            "text": u.get("text", ""),
            "context": context,
        })

print(f"✅ {len(participations)} participations to evaluate\n")

# ── Rubric definitions ────────────────────────────────────────────────────────
RUBRIC_A = """RUBRIC A — Direct Response to Teacher Question:
A (5pts): Deep, reflective response with critical analysis and original connections beyond the question.
B (4pts): Clear, complete response connecting concepts, demonstrates solid understanding.
C (3pts): Correct response but limited in detail, depth, or elaboration.
D (2pts): Incomplete or partially correct, lacking connection to topic.
E (1pt):  Incorrect, irrelevant, or no response."""

RUBRIC_B = """RUBRIC B — Voluntary Contribution or Question:
A (5pts): Insightful contribution that advances discussion, introduces original thinking, or critically challenges ideas.
B (4pts): Meaningful contribution connecting ideas, clarifying question that deepens understanding, or builds on previous point.
C (3pts): Relevant participation showing topic awareness, though without significant depth or new insight.
D (2pts): Loosely related to topic, adds minimal value; surface-level or repetitive contribution.
E (1pt):  Off-topic, unclear, or does not add value to the class discussion."""

# ── Batch evaluation ──────────────────────────────────────────────────────────
BATCH_SIZE = 15
results = {}

# Load existing results to allow resume
if output_f.exists():
    with open(output_f, encoding="utf-8") as fh:
        existing = json.load(fh)
    results = {str(r["id"]): r for r in existing.get("evaluations", [])}
    print(f"📂 Resuming: {len(results)} already evaluated\n")

def build_batch_prompt(batch):
    lines = []
    for p in batch:
        rubric = "A" if p["type"] == "student_response" else "B"
        ctx = f'Context (Ileana said before): "{p["context"]}"' if p["context"] else "No prior context."
        lines.append(
            f'--- ID {p["id"]} | Speaker: {p["speaker"]} | Type: {p["type"]} | Use RUBRIC {rubric}\n'
            f'{ctx}\n'
            f'Student said: "{p["text"]}"'
        )

    items_text = "\n\n".join(lines)

    return f"""You are evaluating student participations from a university class using two rubrics.

{RUBRIC_A}

{RUBRIC_B}

Evaluate each participation below. For each one, assign:
- grade: exactly one letter A, B, C, D, or E
- rationale: one concise sentence (max 20 words) explaining why

RESPOND ONLY WITH VALID JSON — no text before or after:
{{
  "evaluations": [
    {{"id": 1, "grade": "B", "rationale": "Student connects the concept to a real application correctly."}},
    ...
  ]
}}

PARTICIPATIONS TO EVALUATE:

{items_text}"""

pending = [p for p in participations if str(p["id"]) not in results]
total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE

print(f"📊 Pending: {len(pending)} | Batches: {total_batches}\n")

for i in range(0, len(pending), BATCH_SIZE):
    batch = pending[i:i + BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    ids = [p["id"] for p in batch]
    print(f"🔄 Batch {batch_num}/{total_batches} — IDs {ids[0]}–{ids[-1]}...", flush=True)

    try:
        prompt = build_batch_prompt(batch)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()

        if "```json" in text:
            m = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if m: text = m.group(1)
        elif "```" in text:
            m = re.search(r'```\s*([\s\S]*?)\s*```', text)
            if m: text = m.group(1)

        data = json.loads(text)
        evals = data.get("evaluations", [])

        for e in evals:
            eid = str(e["id"])
            results[eid] = {
                "id": e["id"],
                "grade": e.get("grade", "C"),
                "rationale": e.get("rationale", "")
            }

        print(f"   ✅ {len(evals)} evaluated")

        # Save after every batch
        with open(output_f, "w", encoding="utf-8") as fh:
            json.dump({
                "total": len(results),
                "evaluations": list(results.values())
            }, fh, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"   ⚠️  Batch {batch_num} error: {e}")

    time.sleep(3)

print(f"\n✅ AI evaluations complete: {len(results)}/{len(participations)}")
print(f"   Saved to: {output_f}")
