#!/usr/bin/env python3
"""
Regenera el dashboard con calificaciones ponderadas correctas para TODOS los estudiantes.
"""

import json
from pathlib import Path
from collections import defaultdict

# Rutas
analysis_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis.json")
weighted_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/weighted_grades.json")
transcript_dir = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/transcript_cache")

# Cargar todos los datos
with open(analysis_file, 'r', encoding='utf-8') as f:
    analysis = json.load(f)

with open(weighted_file, 'r', encoding='utf-8') as f:
    weighted = json.load(f)

# Obtener todos los speakers de los bloques
all_speakers = defaultdict(int)
student_types = defaultdict(lambda: defaultdict(int))

for block_file in sorted(transcript_dir.glob("block_*.json")):
    with open(block_file, 'r', encoding='utf-8') as f:
        block = json.load(f)
        for u in block.get('utterances', []):
            speaker = u.get('speaker', '').upper()
            utype = u.get('type', '')

            if speaker and speaker not in ('UNKNOWN', 'ILEANG', '', 'ILEANA'):
                all_speakers[speaker] += 1

                # Mapear tipos de utterance
                if 'response' in utype:
                    student_types[speaker]['response'] += 1
                elif 'question' in utype:
                    student_types[speaker]['question'] += 1
                else:
                    student_types[speaker]['comment'] += 1

# Normalizar nombres
name_map = {
    'ARYANG': 'Aryang',
    'GRACE': 'Grace',
    'STHEPEN': 'Sthepen',
    'CHILAKA': 'Chilaka',
    'MEGA': 'Mega'
}

print("✅ STUDENT PARTICIPATION SUMMARY:")
print("=" * 70)
print(f"\n{'Student':<15} {'Total':<8} {'Responses':<12} {'Questions':<12} {'Comments':<12} {'Grade'}")
print("-" * 70)

for speaker_upper in sorted(all_speakers.keys(), key=lambda x: all_speakers[x], reverse=True):
    speaker = name_map.get(speaker_upper, speaker_upper)
    total = all_speakers[speaker_upper]
    resp = student_types[speaker_upper].get('response', 0)
    ques = student_types[speaker_upper].get('question', 0)
    comm = student_types[speaker_upper].get('comment', 0)

    # Obtener calificación ponderada si existe
    weighted_data = weighted.get(speaker, {})
    if weighted_data:
        grade = f"{weighted_data.get('final_grade', 3.0)} ({weighted_data.get('final_letter', 'C')})"
    else:
        grade = "No evaluation"

    print(f"{speaker:<15} {total:<8} {resp:<12} {ques:<12} {comm:<12} {grade}")

print("\n" + "=" * 70)
print("\n📊 COMPARISON: Transcription vs Analysis")
print("-" * 70)

analysis_students = set()
for c in analysis.get('student_contributions', []):
    student = c.get('student', '')
    if student and student not in ('Class', 'Student', 'Unnamed', 'Unknown'):
        analysis_students.add(student)

for q in analysis.get('teacher_questions', []):
    resp = q.get('student_response', {})
    if resp and resp.get('student'):
        analysis_students.add(resp.get('student'))

transcript_students = {name_map.get(s, s) for s in all_speakers.keys()}

print(f"\nIn TRANSCRIPTION (from blocks): {sorted(transcript_students)}")
print(f"In ANALYSIS.JSON: {sorted(analysis_students)}")
print(f"\nMISSING from analysis: {sorted(transcript_students - analysis_students)}")

print("\n" + "=" * 70)
