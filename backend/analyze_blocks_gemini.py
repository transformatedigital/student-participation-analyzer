#!/usr/bin/env python3
"""
Procesa bloques de audio de 10 minutos con Gemini para extraer Q&A.
Combina resultados de todos los bloques en un análisis completo.
"""

import json
import os
import sys
from pathlib import Path
import time
import google.generativeai as genai

# Configure Gemini API
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("Error: ANTHROPIC_API_KEY no está configurada")
    sys.exit(1)

# Use Gemini (Google's API)
try:
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Note: Using ANTHROPIC_API_KEY with genai might not work directly")
    print("Trying to use it anyway...")

# Paths
blocks_dir = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/audio_blocks_10min")
output_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/qa_analysis_by_blocks.json")
blocks_info_file = blocks_dir / "blocks_info.json"

# Load blocks info
with open(blocks_info_file, 'r') as f:
    blocks_info = json.load(f)

print(f"Procesando {len(blocks_info)} bloques de audio...\n")

all_questions = []
all_contributions = []
questions_id = 1
contributions_id = 1

def upload_and_analyze(audio_file_path, block_num, start_time, end_time):
    """Upload audio block to Gemini and analyze it"""
    global questions_id, contributions_id

    print(f"📤 Subiendo bloque {block_num} ({start_time} - {end_time})...", flush=True)

    try:
        # Upload to Gemini
        audio_file = genai.upload_file(path=audio_file_path)

        # Wait for processing
        print(f"   ⏳ Procesando con Gemini...", flush=True)
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            print(f"   ❌ Error al procesar bloque {block_num}")
            return None

        # Analyze with Gemini
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""Analiza este segmento de audio de una clase (minuto {start_time} - {end_time}).

TAREA IMPORTANTE: Extrae EXACTAMENTE lo siguiente:

1. PREGUNTAS DE LA PROFESORA (Dr. Ileana):
   - Busca TODAS las preguntas directas que la profesora hace a los estudiantes
   - Incluye la pregunta completa, el timestamp, a quién va dirigida, y la respuesta del estudiante si existe

2. CONTRIBUCIONES DE ESTUDIANTES:
   - Preguntas que hacen los estudiantes a la profesora
   - Comentarios o contribuciones voluntarias significativas
   - Respuestas largas a preguntas de la profesora (más de 1-2 palabras)

Para cada item, proporciona:
- timestamp (formato MM:SS relativo al inicio del bloque {start_time})
- texto completo
- quién habla
- si es respuesta, quién responde
- tipo: "teacher_question", "student_question", "student_response", "voluntary_contribution"

IMPORTANTE: Los timestamps deben ser RELATIVOS al inicio del bloque (00:00 al inicio de {start_time}).

Responde SOLO en JSON con esta estructura:
{{
  "block": {block_num},
  "start_time": "{start_time}",
  "end_time": "{end_time}",
  "teacher_questions": [
    {{"timestamp": "MM:SS", "question": "...", "directed_to": "...", "student_response": "..."}}
  ],
  "student_contributions": [
    {{"timestamp": "MM:SS", "student": "...", "type": "...", "content": "..."}}
  ]
}}
"""

        response = model.generate_content([prompt, audio_file])

        # Clean up uploaded file
        genai.delete_file(audio_file.name)

        # Parse response
        response_text = response.text

        # Try to extract JSON
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            block_data = json.loads(json_match.group())
            print(f"   ✅ Bloque {block_num}: {len(block_data.get('teacher_questions', []))} preguntas + {len(block_data.get('student_contributions', []))} contribuciones")
            return block_data
        else:
            print(f"   ⚠️  No se pudo extraer JSON del bloque {block_num}")
            return None

    except Exception as e:
        print(f"   ❌ Error procesando bloque {block_num}: {e}")
        return None

# Process each block
results = []
for block_info in blocks_info:
    block_num = block_info['block']
    block_file = blocks_dir / block_info['file']
    start_time = block_info['start_time']
    end_time = block_info['end_time']

    if not block_file.exists():
        print(f"⚠️  Archivo no encontrado: {block_file}")
        continue

    result = upload_and_analyze(str(block_file), block_num, start_time, end_time)
    if result:
        results.append(result)

        # Merge into combined lists
        for q in result.get('teacher_questions', []):
            q['block'] = block_num
            q['block_start_time'] = start_time
            all_questions.append(q)

        for c in result.get('student_contributions', []):
            c['block'] = block_num
            c['block_start_time'] = start_time
            all_contributions.append(c)

    # Small delay between requests
    time.sleep(2)

print(f"\n📊 Resumen Final:")
print(f"  - Preguntas totales: {len(all_questions)}")
print(f"  - Contribuciones totales: {len(all_contributions)}")

# Save combined results
output_data = {
    'session_id': '2026-04-07',
    'total_duration': '69:24',
    'blocks_processed': len(results),
    'teacher_questions': all_questions,
    'student_contributions': all_contributions,
    'block_results': results
}

with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n✅ Análisis guardado en: {output_file}")
