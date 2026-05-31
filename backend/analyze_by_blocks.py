#!/usr/bin/env python3
"""
Analiza el audio de 60 minutos en bloques de 15 minutos con Gemini
"""

import os
import json
import google.generativeai as genai
from pathlib import Path
import subprocess

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY no está configurada")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

AUDIO_FILE = "/Users/santi/clase-analytics/data/clases/2026-04-07/audio_unificado.m4a"
OUTPUT_DIR = Path("/Users/santi/clase-analytics/data/clases/2026-04-07")
TEMP_DIR = Path("/tmp/audio_blocks")
TEMP_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("🎵 ANÁLISIS POR BLOQUES - Audio de 60 minutos")
print("=" * 80)

# Configurar bloques de 15 minutos
blocks = [
    {"name": "Bloque 1", "start": "00:00:00", "end": "00:15:00"},
    {"name": "Bloque 2", "start": "00:15:00", "end": "00:30:00"},
    {"name": "Bloque 3", "start": "00:30:00", "end": "00:45:00"},
    {"name": "Bloque 4", "start": "00:45:00", "end": "01:00:00"},
]

all_results = {
    "teacher_questions": [],
    "student_contributions": []
}

model = genai.GenerativeModel("gemini-2.0-flash")

for block in blocks:
    print(f"\n{'=' * 80}")
    print(f"📍 {block['name']}: {block['start']} - {block['end']}")
    print('=' * 80)
    
    # Extraer segmento de audio
    block_file = TEMP_DIR / f"block_{block['name'].replace(' ', '_').lower()}.m4a"
    print(f"1️⃣  Extrayendo segmento...")
    
    cmd = [
        'ffmpeg', '-i', AUDIO_FILE,
        '-ss', block['start'],
        '-to', block['end'],
        '-c', 'copy',
        str(block_file),
        '-y'
    ]
    
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"✅ Archivo extraído: {block_file}")
    
    # Subir a Gemini
    print(f"2️⃣  Subiendo a Gemini...")
    try:
        audio_file = genai.upload_file(str(block_file))
        print(f"✅ Archivo subido")
        
        # Esperar a que se procese
        import time
        while audio_file.state.name == "PROCESSING":
            print("⏳ Procesando...")
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)
        
        if audio_file.state.name != "ACTIVE":
            print(f"⚠️  Estado: {audio_file.state}")
            continue
        
        # Analizar
        print(f"3️⃣  Analizando contenido...")
        response = model.generate_content([
            audio_file,
            f"""Analiza este segmento de audio (minutos {block['start']} a {block['end']}) e identifica:

1. PREGUNTAS DEL PROFESOR (Dr. Ileana)
   - Timestamp aproximado dentro de este segmento
   - Pregunta completa
   - Si hay respuesta de estudiante (quién y qué dice)

2. PREGUNTAS O CONTRIBUCIONES DE ESTUDIANTES
   - Timestamp
   - Estudiante (Aryang o Grace)
   - Tipo: pregunta_voluntaria o respuesta_a_profesor
   - Contenido completo

IMPORTANTE: Solo reporta participaciones de Aryang o Grace (otros estudiantes no incluir)

Formato JSON:
{{
  "teacher_questions": [
    {{
      "timestamp": "HH:MM:SS",
      "question": "...",
      "student_response": {{
        "student": "Aryang|Grace",
        "response": "...",
        "quality_score": "A-E"
      }}
    }}
  ],
  "student_contributions": [
    {{
      "timestamp": "HH:MM:SS",
      "student": "Aryang|Grace",
      "type": "question_to_teacher|response",
      "content": "...",
      "quality_score": "A-E"
    }}
  ]
}}

Devuelve SOLO JSON válido, sin texto adicional."""
        ])
        
        print(f"✅ Análisis completado")
        
        # Parsear respuesta
        try:
            # Limpiar la respuesta
            response_text = response.text
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1].replace('json', '').strip()
            
            block_data = json.loads(response_text)
            
            # Agregar al resultado total
            all_results["teacher_questions"].extend(block_data.get("teacher_questions", []))
            all_results["student_contributions"].extend(block_data.get("student_contributions", []))
            
            print(f"✨ {len(block_data.get('teacher_questions', []))} preguntas + {len(block_data.get('student_contributions', []))} contribuciones")
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Error al parsear JSON: {e}")
            print(f"Respuesta: {response.text[:200]}")
        
        # Limpiar archivo temporal
        block_file.unlink()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        continue

# Guardar resultados completos
print(f"\n{'=' * 80}")
print("💾 GUARDANDO RESULTADOS COMPLETOS")
print('=' * 80)

output_file = OUTPUT_DIR / "qa_analysis_blocks.json"
with open(output_file, 'w') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"\n✅ ANÁLISIS COMPLETADO")
print(f"📁 Archivo guardado: {output_file}")
print(f"\n📊 Resumen:")
print(f"  - Preguntas del profesor: {len(all_results['teacher_questions'])}")
print(f"  - Contribuciones de estudiantes: {len(all_results['student_contributions'])}")
print(f"  - Total: {len(all_results['teacher_questions']) + len(all_results['student_contributions'])}")

# Limpiar directorio temporal
import shutil
shutil.rmtree(TEMP_DIR)

