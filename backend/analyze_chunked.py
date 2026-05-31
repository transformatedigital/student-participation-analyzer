#!/usr/bin/env python3
"""Process audio in 3 chunks to avoid Gemini output truncation."""
import os, json, time
from pathlib import Path
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY", "")
BASE    = Path("/Users/santi/clase-analytics/data/clases/2026-03-31")
CHUNKS  = [
    (BASE / "chunk_1.m4a", "00:00:00", "00:56:00"),
    (BASE / "chunk_2.m4a", "00:56:00", "01:52:00"),
    (BASE / "chunk_3.m4a", "01:52:00", "02:47:15"),
]

def make_prompt(offset_start, offset_end):
    return f"""
You are analyzing a segment of a graduate seminar recording (from {offset_start} to {offset_end} of the full class).

SPEAKERS:
- Teacher: Dr. Ileana
- Students: Mega (Indonesia), Grace (Congo), Chilaka (Nigeria), Aryang (Indonesia), Sthepen (Rwanda)

IMPORTANT: All timestamps must be from the START OF THE FULL CLASS.
This segment starts at {offset_start} in the original recording.
So if something happens at second 120 in this audio file, report it as the equivalent full-class time.

EXTRACT ONLY:

1. TEACHER QUESTIONS — every time Dr. Ileana asks a direct question to a student or the class:
   - The question text (verbatim)
   - Which student responded (if any)
   - Exactly what the student said

2. STUDENT CONTRIBUTIONS — every time a student speaks voluntarily (not just when explicitly called):
   - Student name
   - What they said (verbatim, only if substantive — skip "yeah", "huh", single words)

SKIP: teacher explanations with no question, student fillers.

QUALITY SCALE for every student utterance:
A = Extended abstract thinking, synthesis across concepts (SOLO: Extended Abstract)
B = Relational answer, connects ideas, shows full understanding (SOLO: Relational)
C = Multi-point answer, partial understanding, lists facts (SOLO: Multistructural)
D = Single relevant point, basic answer, clarification only (SOLO: Unistructural)
E = Off-topic, irrelevant, non-substantive (SOLO: Prestructural)

Return ONLY valid JSON, no markdown, no extra text:
{{
  "chunk": "{offset_start}-{offset_end}",
  "teacher_questions": [
    {{
      "timestamp": "HH:MM:SS",
      "question": "exact text",
      "directed_to": "student name or class",
      "student_response": {{
        "student": "name",
        "response": "exact text",
        "quality_score": "A|B|C|D|E",
        "quality_label": "Excellent|Very Good|Good|Acceptable|Weak"
      }}
    }}
  ],
  "student_contributions": [
    {{
      "timestamp": "HH:MM:SS",
      "student": "name",
      "type": "question_to_teacher|voluntary_response",
      "content": "exact text",
      "quality_score": "A|B|C|D|E",
      "quality_label": "Excellent|Very Good|Good|Acceptable|Weak"
    }}
  ]
}}
"""

def process_chunk(chunk_file, offset_start, offset_end, idx):
    print(f"\n{'='*60}")
    print(f"📤 CHUNK {idx}: {chunk_file.name}  [{offset_start} → {offset_end}]")
    audio = genai.upload_file(str(chunk_file), mime_type="audio/mp4")
    print(f"   Uploaded: {audio.name}")

    while audio.state.name == "PROCESSING":
        time.sleep(4)
        audio = genai.get_file(audio.name)
        print("   ...", end="", flush=True)

    if audio.state.name != "ACTIVE":
        print(f"\n❌ Failed: {audio.state.name}")
        return None

    print("\n   ✅ Ready — sending request...")
    model = genai.GenerativeModel("gemini-2.5-flash")
    resp  = model.generate_content(
        [audio, make_prompt(offset_start, offset_end)],
        generation_config={"response_mime_type": "application/json", "max_output_tokens": 32768}
    )

    raw = resp.text.strip()
    # Save raw
    raw_path = BASE / f"chunk_{idx}_raw.txt"
    raw_path.write_text(raw)
    print(f"   Raw saved ({len(raw)} chars) → {raw_path.name}")

    # Parse
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON truncated at {e.pos}, repairing...")
        cut = raw[:e.pos]
        # Find last complete record
        last_close = max(cut.rfind('}\n    }'), cut.rfind('}\n  }'), cut.rfind('"quality_label"'))
        if last_close > 0:
            # Walk forward to end of that record
            end = cut.find('}', cut.find('"', last_close) + 1) + 1
            cut = cut[:end]
        ob = cut.count('{') - cut.count('}')
        ok = cut.count('[') - cut.count(']')
        repaired = cut + (']' * ok) + ('}' * ob)
        for _ in range(6):
            try:
                data = json.loads(repaired); break
            except: repaired += '}'
        else:
            print("   ❌ Could not repair"); return None
        print("   ✅ Repaired")

    tq = data.get("teacher_questions", [])
    sc = data.get("student_contributions", [])
    print(f"   ✅ teacher_questions: {len(tq)}  |  student_contributions: {len(sc)}")
    return data

def main():
    if not API_KEY:
        print("❌ GEMINI_API_KEY not set"); return

    genai.configure(api_key=API_KEY)
    all_tq, all_sc = [], []

    for idx, (chunk_file, start, end) in enumerate(CHUNKS, 1):
        result = process_chunk(chunk_file, start, end, idx)
        if result:
            all_tq.extend(result.get("teacher_questions", []))
            all_sc.extend(result.get("student_contributions", []))
        time.sleep(2)

    print(f"\n{'='*60}")
    print(f"📊 FULL CLASS TOTALS")
    print(f"   Teacher questions:      {len(all_tq)}")
    print(f"   Student contributions:  {len(all_sc)}")

    # Per-student stats
    from collections import defaultdict, Counter
    stats = defaultdict(lambda: {"responses": 0, "contributions": 0, "grades": []})
    for q in all_tq:
        r = q.get("student_response") or {}
        if r.get("student"):
            stats[r["student"]]["responses"] += 1
            stats[r["student"]]["grades"].append(r.get("quality_score",""))
    for c in all_sc:
        stats[c["student"]]["contributions"] += 1
        stats[c["student"]]["grades"].append(c.get("quality_score",""))

    print(f"\n   {'Student':15} {'Responses':>10} {'Contributions':>15} {'Grade dist':>25}")
    print(f"   {'-'*65}")
    for st, s in sorted(stats.items()):
        dist = Counter(s["grades"])
        gstr = "  ".join(f"{g}:{dist[g]}" for g in "ABCDE" if dist.get(g,0)>0)
        avg  = sorted(s["grades"])[len(s["grades"])//2] if s["grades"] else "—"
        print(f"   {st:15} {s['responses']:>10} {s['contributions']:>15}   {gstr}  (median:{avg})")

    # Build per_student_summary
    summary = {}
    for st, s in stats.items():
        dist = Counter(s["grades"])
        summary[st] = {
            "responses_to_teacher": s["responses"],
            "voluntary_contributions": s["contributions"],
            "quality_distribution": {g: dist.get(g,0) for g in "ABCDE"}
        }

    # Merge and save
    merged = {
        "session": {"date": "March 31, 2026", "duration_minutes": 167},
        "teacher_questions": all_tq,
        "student_contributions": all_sc,
        "per_student_summary": summary,
        "analysis_rules": {
            "method": "Gemini 2.5 Flash — 3-chunk analysis",
            "filter": "Only teacher questions + substantive student responses/contributions",
            "scale": "A-E: SOLO Taxonomy + Bloom's + Socratic Rubric"
        }
    }

    out = BASE / "analysis_full.json"
    with open(out, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved → {out}")

    # Patch into main analysis.json
    try:
        main_f = BASE / "analysis.json"
        with open(main_f) as f: old = json.load(f)
        old["teacher_questions_full"]     = all_tq
        old["student_contributions_full"] = all_sc
        old["per_student_summary"]        = summary
        old["analysis_rules"]             = merged["analysis_rules"]
        with open(main_f, "w") as f: json.dump(old, f, indent=2, ensure_ascii=False)
        print("✅ analysis.json updated")
    except Exception as e:
        print(f"⚠️  Could not patch analysis.json: {e}")

if __name__ == "__main__":
    main()
