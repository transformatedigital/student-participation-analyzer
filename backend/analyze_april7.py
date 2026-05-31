#!/usr/bin/env python3
"""
Full analysis of April 7 class (69 min, 1 chunk or 2 if needed).
Produces: transcription, participation timeline, Q&A table, per-student evaluation.
"""
import os, json, time, re
from pathlib import Path
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY", "")
BASE    = Path("/Users/santi/clase-analytics/data/clases/2026-04-07")
AUDIO   = BASE / "audio_unificado.m4a"

KNOWN_SPEAKERS = "Dr. Ileana (Teacher), Mega (Indonesia), Grace (Congo), Chilaka (Nigeria), Aryang (Indonesia), Sthepen (Rwanda)"

PROMPT = f"""
You are analyzing a 69-minute graduate seminar recording.

KNOWN SPEAKERS: {KNOWN_SPEAKERS}

Return a single JSON object with these 4 sections:

════════ 1. PARTICIPATION TIMELINE ════════
Every speaker turn in the ENTIRE recording (every time someone starts speaking).
This gives a minute-by-minute view of who spoke when.

════════ 2. FULL TRANSCRIPTION ════════
Every utterance verbatim, with speaker and timestamp.
Include ALL speech — teacher explanations, student responses, everything.

════════ 3. TEACHER QUESTIONS + STUDENT RESPONSES ════════
Only when Dr. Ileana asks a direct question:
- The question text
- Which student responded
- What they said
- Quality score A-E

════════ 4. STUDENT VOLUNTARY CONTRIBUTIONS ════════
Any time a student speaks without being explicitly asked.
Skip: "yeah", "huh", "ok", single-word fillers.

QUALITY SCALE:
A = Extended abstract synthesis, creates new framework (SOLO: Extended Abstract / Bloom: Create)
B = Relational, connects multiple concepts, full understanding (SOLO: Relational / Bloom: Analyze)
C = Multistructural, lists several facts, partial understanding (SOLO: Multistructural / Bloom: Apply)
D = Unistructural, one point, basic clarification (SOLO: Unistructural / Bloom: Remember)
E = Prestructural, off-topic, irrelevant, filler (SOLO: Prestructural)

Return ONLY valid JSON, no markdown:
{{
  "session": {{
    "date": "April 7, 2026",
    "duration_minutes": 69,
    "audio_file": "7 abrilLENA CLASE 3:00PM.m4a"
  }},
  "participation_timeline": [
    {{"timestamp": "HH:MM:SS", "speaker": "name", "duration_seconds": 5, "text_preview": "first 8 words..."}}
  ],
  "full_transcription": [
    {{"timestamp": "HH:MM:SS", "speaker": "name", "text": "exact words"}}
  ],
  "teacher_questions": [
    {{
      "id": 1,
      "timestamp": "HH:MM:SS",
      "question": "exact question",
      "directed_to": "student name or class",
      "student_response": {{
        "student": "name",
        "response": "exact text",
        "quality_score": "A|B|C|D|E",
        "quality_label": "Excellent|Very Good|Good|Acceptable|Weak",
        "rationale": "one sentence"
      }}
    }}
  ],
  "student_contributions": [
    {{
      "id": 1,
      "timestamp": "HH:MM:SS",
      "student": "name",
      "type": "question_to_teacher|voluntary_response",
      "content": "exact text",
      "quality_score": "A|B|C|D|E",
      "quality_label": "Excellent|Very Good|Good|Acceptable|Weak",
      "rationale": "one sentence"
    }}
  ],
  "per_student_summary": {{
    "Mega": {{"responses_to_teacher": 0, "voluntary_contributions": 0, "quality_distribution": {{"A":0,"B":0,"C":0,"D":0,"E":0}}, "avg_quality": "D"}},
    "Grace": {{"responses_to_teacher": 0, "voluntary_contributions": 0, "quality_distribution": {{"A":0,"B":0,"C":0,"D":0,"E":0}}, "avg_quality": "D"}},
    "Chilaka": {{"responses_to_teacher": 0, "voluntary_contributions": 0, "quality_distribution": {{"A":0,"B":0,"C":0,"D":0,"E":0}}, "avg_quality": "D"}},
    "Aryang": {{"responses_to_teacher": 0, "voluntary_contributions": 0, "quality_distribution": {{"A":0,"B":0,"C":0,"D":0,"E":0}}, "avg_quality": "D"}},
    "Sthepen": {{"responses_to_teacher": 0, "voluntary_contributions": 0, "quality_distribution": {{"A":0,"B":0,"C":0,"D":0,"E":0}}, "avg_quality": "D"}}
  }}
}}
"""

def extract_records(raw, field):
    """Extract complete JSON objects from a potentially truncated array."""
    start = raw.find(f'"{field}"')
    if start == -1: return []
    bracket = raw.find('[', start)
    if bracket == -1: return []
    records, depth, cur = [], 0, None
    for i in range(bracket, len(raw)):
        c = raw[i]
        if c == '{':
            if depth == 0: cur = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and cur is not None:
                try: records.append(json.loads(raw[cur:i+1]))
                except: pass
                cur = None
        elif c == ']' and depth == 0 and cur is None:
            break
    return records

def valid_ts(ts, max_secs=4200):
    try:
        p = ts.split(":")
        h,m,s = int(p[0]),int(p[1]),int(p[2])
        return 0 <= s <= 59 and 0 <= h*3600+m*60+s <= max_secs
    except: return False

def main():
    if not API_KEY:
        print("❌ GEMINI_API_KEY not set"); return

    genai.configure(api_key=API_KEY)

    print(f"📤 Uploading {AUDIO.name} ({AUDIO.stat().st_size/1e6:.1f} MB)...")
    af = genai.upload_file(str(AUDIO), mime_type="audio/mp4")
    print(f"   Uploaded: {af.name}")

    while af.state.name == "PROCESSING":
        time.sleep(4)
        af = genai.get_file(af.name)
        print("   ...", end="", flush=True)
    print()

    if af.state.name != "ACTIVE":
        print(f"❌ Failed: {af.state.name}"); return

    print("✅ Ready — sending analysis request...")
    model = genai.GenerativeModel("gemini-2.5-flash")
    resp  = model.generate_content(
        [af, PROMPT],
        generation_config={
            "response_mime_type": "application/json",
            "max_output_tokens": 65536
        }
    )

    raw = resp.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n",1)[1].rsplit("```",1)[0]

    # Save raw
    (BASE / "analysis_raw.txt").write_text(raw)
    print(f"✅ Response: {len(raw)} chars")

    # Parse — with fallback field-by-field extraction
    try:
        data = json.loads(raw)
        print("✅ JSON parsed cleanly")
    except json.JSONDecodeError as e:
        print(f"⚠️  Truncated at {e.pos} — extracting field by field...")
        data = {
            "session": {"date": "April 7, 2026", "duration_minutes": 69},
            "participation_timeline":  extract_records(raw, "participation_timeline"),
            "full_transcription":      extract_records(raw, "full_transcription"),
            "teacher_questions":       extract_records(raw, "teacher_questions"),
            "student_contributions":   extract_records(raw, "student_contributions"),
        }
        # Try to get per_student_summary
        ps_start = raw.find('"per_student_summary"')
        if ps_start > 0:
            try:
                ps_end = raw.find('\n  }', ps_start) + 4
                data["per_student_summary"] = json.loads('{' + raw[ps_start:ps_end] + '}').get("per_student_summary",{})
            except: pass

    # Filter bad timestamps (max 69m = 4140s, give 60s buffer)
    for field in ["participation_timeline","full_transcription","teacher_questions","student_contributions"]:
        before = len(data.get(field,[]))
        data[field] = [r for r in data.get(field,[]) if valid_ts(r.get("timestamp",""), 4200)]
        after = len(data[field])
        if before != after:
            print(f"   Filtered {before-after} bad timestamps from {field}")

    # Stats
    tl  = data.get("participation_timeline", [])
    tr  = data.get("full_transcription", [])
    tq  = data.get("teacher_questions", [])
    sc  = data.get("student_contributions", [])
    print(f"\n📊 RESULTS:")
    print(f"   Timeline entries:       {len(tl)}")
    print(f"   Transcription segments: {len(tr)}")
    print(f"   Teacher questions:      {len(tq)}")
    print(f"   Student contributions:  {len(sc)}")

    # Per-student breakdown
    from collections import defaultdict, Counter
    stats = defaultdict(lambda: {"responses":0,"contributions":0,"grades":[]})
    for q in tq:
        r = q.get("student_response") or {}
        if r.get("student") and r["student"] != "Dr. Ileana":
            stats[r["student"]]["responses"] += 1
            stats[r["student"]]["grades"].append(r.get("quality_score",""))
    for c in sc:
        if c.get("student"):
            stats[c["student"]]["contributions"] += 1
            stats[c["student"]]["grades"].append(c.get("quality_score",""))

    print(f"\n   {'Student':12} {'Responses':>10} {'Voluntary':>10}   Grades")
    print(f"   {'-'*55}")
    for st in ["Grace","Mega","Chilaka","Aryang","Sthepen"]:
        s = stats.get(st, {"responses":0,"contributions":0,"grades":[]})
        dist = Counter(s["grades"])
        gstr = "  ".join(f"{g}:{dist[g]}" for g in "ABCDE" if dist.get(g,0)>0)
        print(f"   {st:12} {s['responses']:>10} {s['contributions']:>10}   {gstr or '—'}")

    # Build per_student_summary if missing
    if "per_student_summary" not in data or not data["per_student_summary"]:
        data["per_student_summary"] = {
            st: {
                "responses_to_teacher": s["responses"],
                "voluntary_contributions": s["contributions"],
                "quality_distribution": {g: Counter(s["grades"]).get(g,0) for g in "ABCDE"},
                "avg_quality": sorted(s["grades"])[len(s["grades"])//2] if s["grades"] else "—"
            }
            for st, s in stats.items()
        }

    # Participation % by speaker from timeline
    if tl:
        spk_count = Counter(e.get("speaker","?") for e in tl)
        total = sum(spk_count.values())
        print(f"\n   Participation by speaker (timeline turns):")
        for spk, cnt in spk_count.most_common():
            print(f"     {spk:15} {cnt:4d} turns ({cnt/total*100:.0f}%)")

    # Update speakers.json with counts
    spk_map = {"Dr. Ileana":"speaker_1","Mega":"speaker_2","Grace":"speaker_3",
               "Chilaka":"speaker_4","Aryang":"speaker_5","Sthepen":"speaker_6"}
    with open(BASE/"speakers.json") as f: spk_data = json.load(f)
    if tl:
        for sp in spk_data["speakers"]:
            name = sp["name"]
            cnt  = Counter(e.get("speaker","") for e in tl).get(name, 0)
            sp["segments_count"] = cnt
            sp["percentage"] = round(cnt/len(tl)*100) if tl else 0
        with open(BASE/"speakers.json","w") as f: json.dump(spk_data, f, indent=2)

    # Save analysis
    data["analysis_rules"] = {
        "method": "Gemini 2.5 Flash — single-pass full audio",
        "filter": "Teacher questions + substantive student responses only",
        "scale": "A-E: SOLO Taxonomy + Bloom's + Socratic Rubric"
    }
    out = BASE / "analysis.json"
    with open(out,"w") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved → {out}")

    # Update status
    with open(BASE/"metadata.json") as f: meta = json.load(f)
    meta["status"] = "analyzed"
    meta["total_segments"] = len(tr)
    meta["teacher_questions_count"] = len(tq)
    meta["student_contributions_count"] = len(sc)
    with open(BASE/"metadata.json","w") as f: json.dump(meta, f, indent=2)
    print("✅ metadata.json updated")

if __name__ == "__main__":
    main()
