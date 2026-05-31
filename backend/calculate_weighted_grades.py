#!/usr/bin/env python3
"""
Calcula calificaciones ponderadas considerando:
- Tipo de participación (respuestas 50%, preguntas 30%, comentarios 20%)
- Bonus por cantidad de participaciones
"""

import json
from pathlib import Path
from collections import defaultdict

# Rutas
analysis_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis.json")
output_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/weighted_grades.json")

# Cargar datos
with open(analysis_file, 'r', encoding='utf-8') as f:
    analysis = json.load(f)

# Mapeo de letras a números
grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}
reverse_grade_map = {5: 'A', 4: 'B', 3: 'C', 2: 'D', 1: 'E'}

# Estructura: {student: {type: [grades]}}
student_data = defaultdict(lambda: defaultdict(list))

# Procesar participaciones de estudiantes
student_contributions = analysis.get('student_contributions', [])
for contrib in student_contributions:
    student = contrib.get('student', 'Unknown')
    contrib_type = contrib.get('type', 'comment')
    quality = contrib.get('quality_score', 'C')

    # Normalizar tipos
    if contrib_type == 'question_to_teacher':
        contrib_type = 'question'
    elif contrib_type == 'voluntary_response':
        contrib_type = 'response'
    else:
        contrib_type = 'comment'

    if quality in grade_map:
        student_data[student][contrib_type].append(grade_map[quality])

# Procesar respuestas a preguntas del profesor
teacher_questions = analysis.get('teacher_questions', [])
for question in teacher_questions:
    student_response = question.get('student_response', {})
    if student_response and student_response.get('student'):
        student = student_response['student']
        quality = student_response.get('quality_score', 'C')

        if quality in grade_map:
            student_data[student]['response'].append(grade_map[quality])

# Calcular promedios ponderados
weighted_results = {}

for student, types in student_data.items():
    response_grades = types.get('response', [])
    question_grades = types.get('question', [])
    comment_grades = types.get('comment', [])

    # Promedios por tipo
    avg_response = sum(response_grades) / len(response_grades) if response_grades else 0
    avg_question = sum(question_grades) / len(question_grades) if question_grades else 0
    avg_comment = sum(comment_grades) / len(comment_grades) if comment_grades else 0

    # Ponderación: Respuestas 50%, Preguntas 30%, Comentarios 20%
    weights = {
        'response': (0.50, len(response_grades)),
        'question': (0.30, len(question_grades)),
        'comment': (0.20, len(comment_grades))
    }

    total_weight = 0
    weighted_sum = 0
    total_participations = len(response_grades) + len(question_grades) + len(comment_grades)

    if avg_response > 0:
        weighted_sum += avg_response * 0.50
        total_weight += 0.50
    if avg_question > 0:
        weighted_sum += avg_question * 0.30
        total_weight += 0.30
    if avg_comment > 0:
        weighted_sum += avg_comment * 0.20
        total_weight += 0.20

    # Calcular promedio ponderado
    if total_weight > 0:
        weighted_avg = weighted_sum / total_weight
    else:
        weighted_avg = 3.0

    # Bonus por cantidad de participaciones (pequeño ajuste)
    # Si participa mucho (>40), +0.1; si participa poco (<5), -0.1
    quantity_bonus = 0
    if total_participations >= 40:
        quantity_bonus = 0.15
    elif total_participations >= 20:
        quantity_bonus = 0.1
    elif total_participations < 5:
        quantity_bonus = -0.2

    final_grade = min(5, max(1, weighted_avg + quantity_bonus))
    final_letter = reverse_grade_map[round(final_grade)]

    weighted_results[student] = {
        'weighted_average': round(weighted_avg, 2),
        'quantity_bonus': round(quantity_bonus, 2),
        'final_grade': round(final_grade, 2),
        'final_letter': final_letter,
        'total_participations': total_participations,
        'responses': len(response_grades),
        'questions': len(question_grades),
        'comments': len(comment_grades),
        'avg_response': round(avg_response, 2),
        'avg_question': round(avg_question, 2),
        'avg_comment': round(avg_comment, 2),
        'breakdown': {
            'responses': response_grades,
            'questions': question_grades,
            'comments': comment_grades
        }
    }

# Guardar resultados
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(weighted_results, f, indent=2, ensure_ascii=False)

print("✅ Weighted grades calculated:")
print("=" * 70)

# Ordenar por calificación final (descendente)
sorted_students = sorted(weighted_results.items(),
                        key=lambda x: x[1]['final_grade'],
                        reverse=True)

for student, data in sorted_students:
    print(f"\n📊 {student}")
    print(f"   Participations: {data['total_participations']} (R:{data['responses']}, Q:{data['questions']}, C:{data['comments']})")
    print(f"   Breakdown: R={data['avg_response']}, Q={data['avg_question']}, C={data['avg_comment']}")
    print(f"   Weighted Avg: {data['weighted_average']}")
    print(f"   Quantity Bonus: {data['quantity_bonus']:+.2f}")
    print(f"   Final Grade: {data['final_grade']} ({data['final_letter']})")

print("\n" + "=" * 70)
print(f"✅ Results saved to: {output_file}")
