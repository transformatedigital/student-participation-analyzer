#!/usr/bin/env python3
"""Second pass: extract only Q&A from April 7 (already uploaded file)."""
import os, json, time
from pathlib import Path
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY","")
BASE    = Path("/Users/santi/clase-analytics/data/clases/2026-04-07")
AUDIO   = BASE / "audio_unificado.m4a"

PROMPT = """
You are analyzing a 69-minute graduate seminar.

SPEAKERS: Dr. Ileana (Teacher), Mega (Indonesia), Grace (Congo), Chilaka (Nigeria), Aryang (Indonesia), Sthepen (Rwanda)

TASK — Extract ONLY two things, be EXHAUSTIVE (capture every single instance):

1. TEACHER QUESTIONS: Every time Dr. Ileana asks a question to a student or the class.
   For each: timestamp, exact question, who responded, exact response, quality A-E.

2. STUDENT CONTRIBUTIONS: Every time a student speaks voluntarily (not just filler words).
   Skip: "yeah", "uh", "ok", single-word acknowledgments.

QUALITY SCALE:
A = Extended abstract, synthesis, new framework (Bloom: Create/Evaluate)
B = Relational, connects concepts, full understanding (Bloom: Analyze)
C = Multistructural, partial understanding, lists facts (Bloom: Apply)
D = Unistructural, one point, basic clarification (Bloom: Remember)
E = Prestructural, off-topic, irrelevant

Return ONLY this JSON (no markdown, no extra text):
{
  "teacher_questions": [
    {
      "id": 1,
      "timestamp": "HH:MM:SS",
      "question": "exact text",
      "directed_to": "student name or class",
      "student_response": {
        "student": "name",
        "response": "exact text",
        "quality_score": "A|B|C|D|E",
        "quality_label": "Excellent|Very Good|Good|Acceptable|Weak",
        "rationale": "one sentence"
      }
    }
  ],
  "student_contributions": [
    {
      "id": 1,
      "timestamp": "HH:MM:SS",
      "student": "name",
      "type": "question_to_teacher|voluntary_response",
      "content": "exact text",
      "quality_score": "A|B|C|D|E",
      "quality_label": "Excellent|Very Good|Good|Acceptable|Weak",
      "rationale": "one sentence"
    }
  ]
}
"""

def extract_records(raw, field):
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
        elif c == ']' and depth == 0 and cur is None: break
    return records

def valid_ts(ts, max_secs=4200):
    try:
        p=ts.split(":"); h,m,s=int(p[0]),int(p[1]),int(p[2])
        return 0<=s<=59 and 0<=h*3600+m*60+s<=max_secs
    except: return False

def main():
    if not API_KEY: print("❌ No API key"); return
    genai.configure(api_key=API_KEY)

    print(f"📤 Uploading {AUDIO.name}...")
    af = genai.upload_file(str(AUDIO), mime_type="audio/mp4")
    while af.state.name == "PROCESSING":
        time.sleep(4); af = genai.get_file(af.name); print(".", end="", flush=True)
    print(f"\n✅ Ready: {af.name}")

    model = genai.GenerativeModel("gemini-2.5-flash")
    resp  = model.generate_content(
        [af, PROMPT],
        generation_config={"response_mime_type":"application/json","max_output_tokens":65536}
    )
    raw = resp.text.strip()
    if raw.startswith("```"): raw = raw.split("\n",1)[1].rsplit("```",1)[0]
    (BASE/"analysis_qa_raw.txt").write_text(raw)
    print(f"✅ Response: {len(raw)} chars")

    try:
        data = json.loads(raw)
    except:
        print("⚠️  Extracting field by field...")
        data = {
            "teacher_questions":     extract_records(raw,"teacher_questions"),
            "student_contributions": extract_records(raw,"student_contributions"),
        }

    tq = [r for r in data.get("teacher_questions",[])     if valid_ts(r.get("timestamp",""))]
    sc = [r for r in data.get("student_contributions",[]) if valid_ts(r.get("timestamp",""))]

    print(f"  teacher_questions:      {len(tq)}")
    print(f"  student_contributions:  {len(sc)}")

    from collections import Counter, defaultdict
    stats = defaultdict(lambda:{"responses":0,"contributions":0,"grades":[]})
    for q in tq:
        r = q.get("student_response") or {}
        if r.get("student"):
            stats[r["student"]]["responses"]+=1
            stats[r["student"]]["grades"].append(r.get("quality_score",""))
    for c in sc:
        if c.get("student"):
            stats[c["student"]]["contributions"]+=1
            stats[c["student"]]["grades"].append(c.get("quality_score",""))

    print(f"\n  {'Student':12} {'Responses':>10} {'Voluntary':>10}  Grades")
    print(f"  {'-'*55}")
    for st in ["Grace","Mega","Chilaka","Aryang","Sthepen"]:
        s = stats.get(st,{"responses":0,"contributions":0,"grades":[]})
        dist = Counter(s["grades"])
        gstr = "  ".join(f"{g}:{dist[g]}" for g in "ABCDE" if dist.get(g,0)>0)
        print(f"  {st:12} {s['responses']:>10} {s['contributions']:>10}  {gstr or '—'}")

    # Merge into existing analysis.json
    with open(BASE/"analysis.json") as f: existing = json.load(f)
    existing["teacher_questions"]      = tq
    existing["student_contributions"]  = sc
    existing["per_student_summary"]    = {
        st: {
            "responses_to_teacher": s["responses"],
            "voluntary_contributions": s["contributions"],
            "quality_distribution": {g: Counter(s["grades"]).get(g,0) for g in "ABCDE"},
            "avg_quality": sorted(s["grades"])[len(s["grades"])//2] if s["grades"] else "—"
        } for st,s in stats.items()
    }
    with open(BASE/"analysis.json","w") as f: json.dump(existing, f, indent=2, ensure_ascii=False)

    with open(BASE/"metadata.json") as f: meta = json.load(f)
    meta["teacher_questions_count"]      = len(tq)
    meta["student_contributions_count"]  = len(sc)
    with open(BASE/"metadata.json","w") as f: json.dump(meta, f, indent=2)

    print("\n✅ analysis.json + metadata.json updated")

if __name__ == "__main__":
    main()
