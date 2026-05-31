#!/usr/bin/env python3
"""
Full class analysis using Gemini 2.5 Flash with native audio understanding.
Captures: teacher questions + student responses + student voluntary contributions.
Excludes: teacher explanations, student fillers.
"""

import os, json, time
from pathlib import Path
import google.generativeai as genai

API_KEY   = os.environ.get("GEMINI_API_KEY", "")
AUDIO     = Path("/Users/santi/clase-analytics/data/clases/2026-03-31/audio_unificado.m4a")
OUT_FILE  = Path("/Users/santi/clase-analytics/data/clases/2026-03-31/analysis_full.json")
SPEAKERS  = {
    "Teacher":  "Dr. Ileana",
    "Student1": "Mega (Indonesia)",
    "Student2": "Grace (Congo)",
    "Student3": "Chilaka (Nigeria)",
    "Student4": "Aryang (Indonesia)",
    "Student5": "Sthepen (Rwanda)",
}

PROMPT = """
You are analyzing a graduate-level class recording (167 minutes, 5 speakers).

SPEAKERS:
- Teacher: Dr. Ileana
- Students: Mega (Indonesia), Grace (Congo), Chilaka (Nigeria), Aryang (Indonesia), Sthepen (Rwanda)

YOUR TASK — extract TWO things only:

════════════════════════════════════════════
PART 1 — TEACHER QUESTIONS TO CLASS
════════════════════════════════════════════
Every time the teacher asks a question (directed to the class or a specific student):
- Record the question with timestamp
- Record which student responded (if any)
- Record exactly what the student said in response
- Skip teacher explanations that contain no question

════════════════════════════════════════════
PART 2 — STUDENT VOLUNTARY CONTRIBUTIONS
════════════════════════════════════════════
Every time a student speaks without being explicitly asked (voluntary questions to teacher, unsolicited comments, spontaneous responses):
- Record timestamp, student name, and what they said

════════════════════════════════════════════
EXCLUDE COMPLETELY:
════════════════════════════════════════════
- Teacher explanations/lectures with no question
- Student fillers: "umm", "huh", "yeah", "ok", single-word acknowledgments
- Laughter, non-verbal sounds

════════════════════════════════════════════
EVALUATION SCALE (apply to every student utterance):
════════════════════════════════════════════
A - Excellent: Extended abstract thinking, synthesis, creates new framework, connects multiple concepts (SOLO: Extended Abstract / Bloom: Create/Evaluate)
B - Very Good: Relational answer, connects concepts, shows full understanding (SOLO: Relational / Bloom: Analyze/Apply)
C - Good: Multistructural, lists several relevant facts, partial understanding (SOLO: Multistructural / Bloom: Apply/Understand)
D - Acceptable: Unistructural, one relevant point, basic answer (SOLO: Unistructural / Bloom: Remember/Understand)
E - Weak: Prestructural, irrelevant, off-topic, or non-substantive (SOLO: Prestructural / Bloom: None)

════════════════════════════════════════════
OUTPUT FORMAT — JSON only, no extra text:
════════════════════════════════════════════
{
  "session": {
    "date": "March 31, 2026",
    "duration_minutes": 167,
    "course": "Graduate Seminar"
  },
  "teacher_questions": [
    {
      "id": 1,
      "timestamp": "HH:MM:SS",
      "question": "exact teacher question text",
      "directed_to": "student name or 'class'",
      "student_response": {
        "student": "name",
        "response": "exact student response text",
        "quality_score": "A|B|C|D|E",
        "quality_label": "Excellent|Very Good|Good|Acceptable|Weak",
        "rationale": "one sentence explanation"
      }
    }
  ],
  "student_contributions": [
    {
      "id": 1,
      "timestamp": "HH:MM:SS",
      "student": "name",
      "type": "question_to_teacher|voluntary_response|unsolicited_comment",
      "content": "exact student text",
      "quality_score": "A|B|C|D|E",
      "quality_label": "Excellent|Very Good|Good|Acceptable|Weak",
      "rationale": "one sentence explanation"
    }
  ],
  "per_student_summary": {
    "Mega": {
      "responses_to_teacher": 0,
      "voluntary_contributions": 0,
      "avg_quality": "A|B|C|D|E",
      "quality_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    }
  }
}
"""

def main():
    if not API_KEY:
        print("❌ GEMINI_API_KEY not set. Run: export GEMINI_API_KEY='your-key'")
        return

    genai.configure(api_key=API_KEY)

    print("📤 Uploading audio to Gemini...")
    print(f"   File: {AUDIO.name}  ({AUDIO.stat().st_size / 1e6:.1f} MB)")

    audio_file = genai.upload_file(str(AUDIO), mime_type="audio/mp4")
    print(f"   Upload complete: {audio_file.name}")

    # Wait for processing
    print("⏳ Waiting for Gemini to process audio...")
    while audio_file.state.name == "PROCESSING":
        time.sleep(5)
        audio_file = genai.get_file(audio_file.name)
        print("   ...", end="", flush=True)

    if audio_file.state.name != "ACTIVE":
        print(f"\n❌ File processing failed: {audio_file.state.name}")
        return

    print("\n✅ Audio ready. Sending analysis request...")

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        [audio_file, PROMPT],
        generation_config={"response_mime_type": "application/json", "max_output_tokens": 65536}
    )

    print("✅ Response received. Parsing JSON...")

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    # Save raw always for inspection
    raw_file = OUT_FILE.parent / "analysis_full_raw.txt"
    with open(raw_file, "w") as f:
        f.write(raw)
    print(f"   Raw response saved → {raw_file}  ({len(raw)} chars)")

    # Parse with repair fallback
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON parse error at char {e.pos}, attempting repair...")
        cut = raw[:e.pos]
        open_b = cut.count('{') - cut.count('}')
        open_k = cut.count('[') - cut.count(']')
        repaired = cut + ('}' * open_b) + (']' * open_k)
        for _ in range(5):
            try:
                data = json.loads(repaired)
                print("   ✅ JSON repaired")
                break
            except:
                repaired += '}'
        else:
            print("   ❌ Could not repair — check analysis_full_raw.txt")
            return

    # Stats
    tq  = data.get("teacher_questions", [])
    sc  = data.get("student_contributions", [])
    print(f"\n📊 RESULTS:")
    print(f"   Teacher questions captured:      {len(tq)}")
    print(f"   Student contributions captured:  {len(sc)}")

    # Per-student breakdown
    from collections import defaultdict, Counter
    student_q  = defaultdict(int)
    student_sc = defaultdict(int)
    student_grades = defaultdict(list)

    for q in tq:
        resp = q.get("student_response", {})
        if resp and resp.get("student"):
            student_q[resp["student"]] += 1
            student_grades[resp["student"]].append(resp.get("quality_score",""))
    for c in sc:
        student_sc[c["student"]] += 1
        student_grades[c["student"]].append(c.get("quality_score",""))

    print(f"\n   {'Student':15} {'Responses':>10} {'Contributions':>15} {'Grades':>20}")
    print(f"   {'-'*60}")
    all_students = set(list(student_q.keys()) + list(student_sc.keys()))
    for st in sorted(all_students):
        grades = student_grades[st]
        dist = Counter(grades)
        grade_str = "  ".join(f"{g}:{dist[g]}" for g in "ABCDE" if dist[g])
        print(f"   {st:15} {student_q[st]:>10} {student_sc[st]:>15}   {grade_str}")

    # Save
    with open(OUT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Full analysis saved → {OUT_FILE}")

    # Also update main analysis.json with the full data
    try:
        with open(Path("/Users/santi/clase-analytics/data/clases/2026-03-31/analysis.json")) as f:
            old = json.load(f)
        old["teacher_questions_full"]      = tq
        old["student_contributions_full"]  = sc
        old["per_student_summary"]         = data.get("per_student_summary", {})
        old["analysis_rules"] = {
            "method": "Gemini 2.5 Flash full-audio analysis",
            "filter": "Only teacher questions + student responses/contributions. Fillers excluded.",
            "scale": "A-E based on SOLO Taxonomy + Bloom's + Socratic Seminar Rubric"
        }
        with open(Path("/Users/santi/clase-analytics/data/clases/2026-03-31/analysis.json"), "w") as f:
            json.dump(old, f, indent=2, ensure_ascii=False)
        print("✅ analysis.json also updated with full results")
    except Exception as e:
        print(f"⚠️  Could not update analysis.json: {e}")

if __name__ == "__main__":
    main()
