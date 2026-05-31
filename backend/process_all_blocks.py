#!/usr/bin/env python3
"""
Procesa todos los bloques de audio de 10 minutos con Google Gemini
para extraer preguntas y respuestas de toda la clase.
"""

import json
import os
import sys
import time
import re
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    print("Instalando google-generativeai...")
    os.system("pip install google-generativeai")
    import google.generativeai as genai

# Configure Gemini API
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("❌ Error: GOOGLE_API_KEY no está configurada")
    sys.exit(1)

genai.configure(api_key=api_key)
print(f"✅ API de Google Gemini configurada")

# Paths
blocks_dir = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/audio_blocks_10min")
output_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis_full_blocks.json")
blocks_info_file = blocks_dir / "blocks_info.json"

# Load blocks info
with open(blocks_info_file, 'r') as f:
    blocks_info = json.load(f)

print(f"\n📊 Procesando {len(blocks_info)} bloques de audio (10 minutos cada uno)...\n")

all_questions = []
all_contributions = []
all_block_results = []

def upload_and_analyze(audio_file_path, block_num, start_time, end_time, start_seconds):
    """Upload audio block to Gemini and analyze it"""

    print(f"📤 Block {block_num}: Subiendo ({start_time} - {end_time})...", flush=True)

    try:
        # Upload to Gemini
        audio_file = genai.upload_file(path=audio_file_path, mime_type="audio/mp4")
        print(f"   ✓ Archivo subido, procesando...", flush=True)

        # Wait for processing
        while audio_file.state.name == "PROCESSING":
            time.sleep(1)
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            print(f"   ❌ Error al procesar bloque {block_num}")
            genai.delete_file(audio_file.name)
            return None

        # Analyze with Gemini
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""Analiza este segmento de audio de una clase universitaria.
TIEMPO EN LA CLASE: Minutos {start_time} a {end_time} (de una clase de 69 minutos)

INSTRUCCIONES CRÍTICAS:
1. Extrae TODAS las preguntas directas de la profesora (Dra. Ileana)
2. Extrae TODAS las respuestas de estudiantes (Aryang, Grace, otros)
3. Extrae TODAS las preguntas de estudiantes a la profesora
4. Extrae TODAS las contribuciones significativas de estudiantes

FORMATO REQUERIDO - RESPONDE SOLO CON JSON VÁLIDO:
{{
  "block": {block_num},
  "time_range": "{start_time}-{end_time}",
  "teacher_questions": [
    {{
      "timestamp": "MM:SS",
      "question": "texto completo de la pregunta",
      "directed_to": "nombre del estudiante o 'Class'",
      "student_response": {{
        "student": "nombre de quien responde",
        "response": "respuesta del estudiante",
        "quality_score": "A-E"
      }}
    }}
  ],
  "student_contributions": [
    {{
      "timestamp": "MM:SS",
      "student": "nombre",
      "type": "question_to_teacher|voluntary_response|comment",
      "content": "texto completo",
      "quality_score": "A-E"
    }}
  ]
}}

NOTAS IMPORTANTES:
- Timestamps en formato MM:SS (relativo al inicio del bloque)
- Si no hay respuesta inmediata, usa respuesta vacía
- quality_score: A=Excelente, B=Bueno, C=Satisfactorio, D=Insuficiente, E=Deficiente
- Incluye incluso preguntas retóricas y respuestas cortas
- Los nombres de estudiantes son: Aryang, Grace, y posiblemente otros
- La profesora es: Dra. Ileana, Ileana, Dr. Ileana, o simplemente "Teacher"
"""

        response = model.generate_content([prompt, audio_file])
        response_text = response.text

        # Clean up uploaded file immediately
        genai.delete_file(audio_file.name)

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                block_data = json.loads(json_match.group())

                # Add absolute timestamps
                questions = block_data.get('teacher_questions', [])
                contributions = block_data.get('student_contributions', [])

                # Convert relative timestamps to absolute
                for q in questions:
                    rel_ts = q.get('timestamp', '00:00')
                    try:
                        parts = rel_ts.split(':')
                        rel_seconds = int(parts[0]) * 60 + int(parts[1])
                        abs_seconds = start_seconds + rel_seconds
                        abs_ts = f"{abs_seconds//60:02d}:{abs_seconds%60:02d}"
                        q['timestamp'] = abs_ts
                        q['block'] = block_num
                    except:
                        pass

                for c in contributions:
                    rel_ts = c.get('timestamp', '00:00')
                    try:
                        parts = rel_ts.split(':')
                        rel_seconds = int(parts[0]) * 60 + int(parts[1])
                        abs_seconds = start_seconds + rel_seconds
                        abs_ts = f"{abs_seconds//60:02d}:{abs_seconds%60:02d}"
                        c['timestamp'] = abs_ts
                        c['block'] = block_num
                    except:
                        pass

                print(f"   ✅ {len(questions)} preguntas + {len(contributions)} contribuciones")
                return {
                    'block': block_num,
                    'time_range': f"{start_time}-{end_time}",
                    'teacher_questions': questions,
                    'student_contributions': contributions
                }
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Error parsing JSON: {e}")
                return None
        else:
            print(f"   ⚠️  No JSON encontrado en respuesta")
            return None

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

# Process each block
for block_info in blocks_info:
    block_num = block_info['block']
    block_file = blocks_dir / block_info['file']
    start_time = block_info['start_time']
    end_time = block_info['end_time']
    start_seconds = block_info['start']

    if not block_file.exists():
        print(f"⚠️  Archivo no encontrado: {block_file}")
        continue

    result = upload_and_analyze(str(block_file), block_num, start_time, end_time, start_seconds)

    if result:
        all_block_results.append(result)

        # Merge into combined lists
        all_questions.extend(result.get('teacher_questions', []))
        all_contributions.extend(result.get('student_contributions', []))

    # Delay between API calls
    time.sleep(3)

# Sort by timestamp
def parse_timestamp(ts):
    try:
        parts = ts.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except:
        return 0

all_questions.sort(key=lambda x: parse_timestamp(x.get('timestamp', '00:00')))
all_contributions.sort(key=lambda x: parse_timestamp(x.get('timestamp', '00:00')))

# Re-ID after sorting
for i, q in enumerate(all_questions, 1):
    q['id'] = i

for i, c in enumerate(all_contributions, 1):
    c['id'] = i

print(f"\n📊 RESUMEN FINAL:")
print(f"  - Total preguntas: {len(all_questions)}")
print(f"  - Total contribuciones: {len(all_contributions)}")
print(f"  - Bloques procesados: {len(all_block_results)}")

# Save combined results
output_data = {
    'session_id': '2026-04-07',
    'total_duration': '69:24',
    'blocks_analyzed': len(all_block_results),
    'teacher_questions': all_questions,
    'student_contributions': all_contributions,
    'per_student_summary': {
        'Dr. Ileana': {'questions_asked': sum(1 for q in all_questions)},
        'Aryang': {'responses': sum(1 for q in all_questions if q.get('student_response', {}).get('student') == 'Aryang'),
                  'contributions': sum(1 for c in all_contributions if c.get('student') == 'Aryang')},
        'Grace': {'responses': sum(1 for q in all_questions if q.get('student_response', {}).get('student') == 'Grace'),
                 'contributions': sum(1 for c in all_contributions if c.get('student') == 'Grace')}
    },
    'block_results': all_block_results
}

with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n✅ Análisis completo guardado en:")
print(f"   {output_file}")
print(f"\n✅ ¡Análisis de 60 minutos completado exitosamente!")
