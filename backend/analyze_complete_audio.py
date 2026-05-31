#!/usr/bin/env python3
"""
Analiza el audio COMPLETO (60 minutos) de la clase 7 de abril
Usando Gemini API para transcripción y análisis Q&A
"""

import os
import json
import google.generativeai as genai
from pathlib import Path

# Configurar API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY no está configurada")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Rutas
AUDIO_FILE = "/Users/santi/clase-analytics/data/clases/2026-04-07/audio_unificado.m4a"
OUTPUT_DIR = Path("/Users/santi/clase-analytics/data/clases/2026-04-07")

print("=" * 80)
print("📊 ANÁLISIS COMPLETO DE AUDIO - Clase 7 de Abril (60 minutos)")
print("=" * 80)

if not Path(AUDIO_FILE).exists():
    print(f"❌ Error: Archivo no encontrado: {AUDIO_FILE}")
    exit(1)

print(f"\n📁 Archivo de audio: {AUDIO_FILE}")
print(f"⏱️  Duración esperada: ~60 minutos\n")

# Paso 1: Transcripción
print("Paso 1️⃣  - Transcribiendo audio completo...")
try:
    audio_file = genai.upload_file(AUDIO_FILE)
    print(f"✅ Archivo subido a Gemini")
    
    # Esperar a que se procese
    import time
    while audio_file.state.name == "PROCESSING":
        print("⏳ Procesando archivo...")
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)
    
    if audio_file.state.name != "ACTIVE":
        print(f"❌ Error al procesar archivo: {audio_file.state}")
        exit(1)
    
    print("✅ Archivo procesado exitosamente")
    
    # Transcribir
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([
        audio_file,
        """Por favor, transcribe el audio completo de esta clase de 60 minutos.
        Incluye:
        1. Timestamp aproximado para cada sección (cada 5-10 minutos)
        2. Quién está hablando (Profesor/Estudiante)
        3. El texto palabra por palabra
        
        Formato esperado:
        [HH:MM:SS] - Speaker: "Texto de lo que dice"
        """
    ])
    
    transcription_full = response.text
    print("✅ Transcripción completada")
    
    # Guardar transcripción
    with open(OUTPUT_DIR / "transcription_complete_60min.txt", 'w') as f:
        f.write(transcription_full)
    print(f"✅ Transcripción guardada")
    
except Exception as e:
    print(f"❌ Error en transcripción: {e}")
    exit(1)

# Paso 2: Análisis Q&A
print("\n\nPaso 2️⃣  - Analizando preguntas y respuestas...")
try:
    response = model.generate_content([
        audio_file,
        """Analiza esta clase de 60 minutos e identifica:

1. PREGUNTAS DEL PROFESOR (Dr. Ileana)
   - Timestamp
   - Pregunta completa
   - A quién la dirige
   - Respuesta de estudiante (si la hay)
   
2. CONTRIBUCIONES DE ESTUDIANTES
   - Timestamp
   - Estudiante que habla
   - Tipo: pregunta_voluntaria, respuesta, contribución
   - Contenido completo
   
Formato JSON:
{{
  "teacher_questions": [
    {{
      "timestamp": "HH:MM:SS",
      "question": "...",
      "directed_to": "Aryang|Grace|Todos",
      "student_response": {{
        "student": "...",
        "response": "...",
        "quality_score": "A-E"
      }}
    }}
  ],
  "student_contributions": [
    {{
      "timestamp": "HH:MM:SS",
      "student": "Aryang|Grace",
      "type": "question_to_teacher|contribution",
      "content": "...",
      "quality_score": "A-E"
    }}
  ]
}}
"""
    ])
    
    qa_analysis = response.text
    print("✅ Análisis Q&A completado")
    
    # Guardar análisis
    with open(OUTPUT_DIR / "qa_analysis_complete_60min.json", 'w') as f:
        f.write(qa_analysis)
    print(f"✅ Análisis guardado")
    
except Exception as e:
    print(f"❌ Error en análisis Q&A: {e}")
    exit(1)

# Resumen
print("\n" + "=" * 80)
print("✅ ANÁLISIS COMPLETO FINALIZADO")
print("=" * 80)
print("\n📁 Archivos generados:")
print(f"  1. transcription_complete_60min.txt")
print(f"  2. qa_analysis_complete_60min.json")
print("\n✨ Próximo paso: Integrar estos datos al analysis.json principal")

