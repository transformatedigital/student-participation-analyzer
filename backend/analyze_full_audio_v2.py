#!/usr/bin/env python3
"""
Análisis completo del audio de 60 minutos con Gemini
Versión 2 - Con mejor manejo de errores
"""

import os
import json
import google.generativeai as genai
from pathlib import Path
import subprocess
import time

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY no configurada")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

AUDIO_FILE = "/Users/santi/clase-analytics/data/clases/2026-04-07/audio_unificado.m4a"
OUTPUT_DIR = Path("/Users/santi/clase-analytics/data/clases/2026-04-07")

print("=" * 80)
print("🎵 ANÁLISIS COMPLETO - Audio 60 minutos con Gemini")
print("=" * 80)

try:
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    print("\n1️⃣  Subiendo archivo de audio a Gemini...")
    audio_file = genai.upload_file(AUDIO_FILE)
    print(f"✅ Archivo: {audio_file.name}")
    
    # Esperar procesamiento
    print("2️⃣  Esperando que Gemini procese el archivo...")
    max_attempts = 30
    attempts = 0
    while audio_file.state.name == "PROCESSING" and attempts < max_attempts:
        print(f"   ⏳ Estado: {audio_file.state.name} ({attempts+1}/{max_attempts})")
        time.sleep(5)
        audio_file = genai.get_file(audio_file.name)
        attempts += 1
    
    if audio_file.state.name != "ACTIVE":
        print(f"❌ Estado final: {audio_file.state.name}")
        exit(1)
    
    print(f"✅ Archivo listo")
    
    # Análisis
    print("\n3️⃣  Analizando participaciones (Q&A)...")
    response = model.generate_content([
        audio_file,
        """Eres un experto analizando una clase universitaria de 60 minutos.

Tu tarea: Identifica TODAS las preguntas del profesor (Dr. Ileana) y TODAS las respuestas/contribuciones de estudiantes (Aryang y Grace).

Para cada PREGUNTA DEL PROFESOR:
- Timestamp exacto (HH:MM:SS)
- Texto completo de la pregunta
- Si hay respuesta: quién responde, qué dice, y calificación (A-E)

Para cada PARTICIPACIÓN DE ESTUDIANTE (Aryang o Grace):
- Timestamp
- Nombre del estudiante
- Tipo: pregunta_voluntaria o respuesta_a_profesor
- Texto completo
- Calificación de calidad (A-E)

IMPORTANTE:
- Solo incluir Aryang y Grace (no otros estudiantes)
- Incluir TODAS las participaciones, sin omitir ninguna
- Timestamps con formato HH:MM:SS
- Calificaciones: A=Excelente, B=Bueno, C=Satisfactorio, D=Insuficiente, E=Deficiente

Responde en JSON:
{
  "teacher_questions": [
    {
      "timestamp": "HH:MM:SS",
      "question": "...",
      "student_response": {
        "student": "Aryang|Grace",
        "response": "...",
        "quality_score": "A|B|C|D|E"
      }
    }
  ],
  "student_contributions": [
    {
      "timestamp": "HH:MM:SS",
      "student": "Aryang|Grace",
      "type": "pregunta_voluntaria|respuesta",
      "content": "...",
      "quality_score": "A|B|C|D|E"
    }
  ]
}"""
    ])
    
    print("✅ Respuesta recibida")
    
    # Parsear respuesta
    print("\n4️⃣  Procesando respuesta...")
    response_text = response.text
    
    # Limpiar JSON si está envuelto en ```
    if '```json' in response_text:
        response_text = response_text.split('```json')[1].split('```')[0].strip()
    elif '```' in response_text:
        response_text = response_text.split('```')[1].split('```')[0].strip()
    
    data = json.loads(response_text)
    
    print(f"✅ JSON procesado")
    print(f"   - Preguntas del profesor: {len(data.get('teacher_questions', []))}")
    print(f"   - Contribuciones de estudiantes: {len(data.get('student_contributions', []))}")
    
    # Guardar
    output_file = OUTPUT_DIR / "qa_analysis_complete.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ ANÁLISIS COMPLETO")
    print(f"📁 Guardado en: {output_file}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

