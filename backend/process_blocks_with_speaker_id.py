#!/usr/bin/env python3
"""
Procesa todos los bloques de 5 minutos con:
1. Identificación automática de speaker usando voice fingerprinting
2. Extracción de Q&A con Google Gemini
3. Combinación de resultados en análisis completo
"""

import json
import os
import sys
import time
import re
from pathlib import Path
import numpy as np

try:
    import google.generativeai as genai
except ImportError:
    print("Instalando google-generativeai...")
    os.system("pip install google-generativeai")
    import google.generativeai as genai

try:
    import librosa
except ImportError:
    print("Instalando librosa...")
    os.system("pip install librosa soundfile")
    import librosa

# Configure Gemini API
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("❌ Error: GOOGLE_API_KEY no está configurada")
    sys.exit(1)

genai.configure(api_key=api_key)
print(f"✅ API de Google Gemini configurada\n")

# Paths
blocks_dir = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/audio_blocks_5min_cleaned")
fingerprints_file = Path("/Users/santi/clase-analytics/data/voice_fingerprints/voice_fingerprints_v1.0.json")
output_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis_with_speaker_id.json")
blocks_info_file = blocks_dir / "blocks_5min_info.json"

print("=" * 70)
print("🎤 PROCESAMIENTO INTEGRADO: IDENTIFICACIÓN + Q&A EXTRACTION")
print("=" * 70 + "\n")

# Load voice fingerprints
with open(fingerprints_file) as f:
    fingerprints_data = json.load(f)
speakers_fingerprints = fingerprints_data['speakers']

print(f"✅ Huella digital cargada: {fingerprints_file.name}")
print(f"   Hablantes disponibles: {list(speakers_fingerprints.keys())}\n")

# Load blocks info
with open(blocks_info_file) as f:
    blocks_info = json.load(f)

print(f"📊 Total bloques para procesar: {len(blocks_info)}\n")

# ============ SPEAKER IDENTIFICATION FUNCTIONS ============

def extract_features_from_audio(audio_path, sr=16000):
    """Extrae características de audio para identificación"""
    try:
        y, sr = librosa.load(str(audio_path), sr=sr)

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)

        spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spec_centroid_mean = np.mean(spec_centroid)
        spec_centroid_std = np.std(spec_centroid)

        spec_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spec_rolloff_mean = np.mean(spec_rolloff)

        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = np.mean(zero_crossing_rate)

        rms = librosa.feature.rms(y=y)[0]
        rms_mean = np.mean(rms)
        rms_std = np.std(rms)

        return {
            'mfcc_mean': mfcc_mean.tolist(),
            'mfcc_std': mfcc_std.tolist(),
            'spectral_centroid_mean': float(spec_centroid_mean),
            'spectral_centroid_std': float(spec_centroid_std),
            'spectral_rolloff_mean': float(spec_rolloff_mean),
            'rms_mean': float(rms_mean),
            'rms_std': float(rms_std),
            'zero_crossing_rate_mean': float(zcr_mean)
        }
    except Exception as e:
        print(f"   ⚠️  Error extrayendo características: {e}")
        return None

def euclidean_distance(feat1, feat2):
    """Calcula distancia euclidiana"""
    dist = 0
    for key in feat1.keys():
        if isinstance(feat1[key], list):
            v1 = np.array(feat1[key])
            v2 = np.array(feat2[key])
            dist += np.sum((v1 - v2) ** 2)
        else:
            dist += (feat1[key] - feat2[key]) ** 2
    return np.sqrt(dist)

def identify_speaker(audio_path):
    """Identifica el speaker de un bloque de audio"""
    features = extract_features_from_audio(audio_path)

    if features is None:
        return {
            'speaker': 'Unknown',
            'confidence': 0,
            'top_3': []
        }

    scores = {}

    for speaker, fingerprint in speakers_fingerprints.items():
        fp_features = fingerprint['features']

        comp_features = {}
        for key in features.keys():
            if isinstance(fp_features[key], list):
                comp_features[key] = np.array(fp_features[key])
            else:
                comp_features[key] = fp_features[key]

        distance = euclidean_distance(features, comp_features)
        confidence = max(0, 100 - (distance / 10))

        scores[speaker] = {
            'distance': float(distance),
            'confidence': float(confidence)
        }

    sorted_scores = sorted(scores.items(), key=lambda x: x[1]['confidence'], reverse=True)
    best_match = sorted_scores[0]
    speaker_name = best_match[0]
    confidence = best_match[1]['confidence']

    return {
        'speaker': speaker_name,
        'confidence': confidence,
        'top_3': [(sp, s['confidence']) for sp, s in sorted_scores[:3]]
    }

# ============ GEMINI Q&A EXTRACTION FUNCTIONS ============

def upload_and_analyze(audio_file_path, block_num, start_time, end_time, start_seconds, speaker_id):
    """Sube bloque a Gemini y analiza con identificación de speaker"""

    print(f"📤 Block {block_num}: Subiendo ({start_time} - {end_time}, {speaker_id['speaker']})...", flush=True)

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
TIEMPO EN LA CLASE: Minutos {start_time} a {end_time} (clase de 59:30 minutos total)
HABLANTE IDENTIFICADO: {speaker_id['speaker']} (confianza: {speaker_id['confidence']:.1f}%)

INSTRUCCIONES CRÍTICAS:
1. Extrae TODAS las preguntas directas de la profesora (Dra. Ileana, Ileana, Dr. Ileana)
2. Extrae TODAS las respuestas de estudiantes (Aryang, Grace, Chilaka, Mega, Sthepen, etc.)
3. Extrae TODAS las preguntas de estudiantes a la profesora
4. Extrae TODAS las contribuciones significativas de estudiantes
5. Usa el nombre del hablante identificado para contextualizar

FORMATO REQUERIDO - RESPONDE SOLO CON JSON VÁLIDO:
{{
  "block": {block_num},
  "time_range": "{start_time}-{end_time}",
  "identified_speaker": "{speaker_id['speaker']}",
  "speaker_confidence": {speaker_id['confidence']:.1f},
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
- Los nombres de estudiantes son: Aryang, Grace, Chilaka, Mega, Sthepen
- La profesora es: Dra. Ileana o variantes
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
                    'identified_speaker': speaker_id['speaker'],
                    'speaker_confidence': speaker_id['confidence'],
                    'speaker_top_3': speaker_id['top_3'],
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

# ============ MAIN PROCESSING LOOP ============

print("=" * 70)
print("🔄 PROCESANDO BLOQUES CON IDENTIFICACIÓN DE SPEAKER")
print("=" * 70 + "\n")

all_questions = []
all_contributions = []
all_block_results = []
speaker_timeline = []

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

    # Step 1: Identify speaker
    print(f"\n[Block {block_num}] Identificando speaker...")
    speaker_id = identify_speaker(str(block_file))
    print(f"   🎤 {speaker_id['speaker']} ({speaker_id['confidence']:.1f}% confianza)")

    # Add to timeline
    duration = block_info['end'] - block_info['start']
    speaker_timeline.append({
        'block': block_num,
        'time_range': f"{start_time}-{end_time}",
        'speaker': speaker_id['speaker'],
        'confidence': speaker_id['confidence'],
        'duration_seconds': duration
    })

    # Step 2: Extract Q&A with Gemini
    result = upload_and_analyze(str(block_file), block_num, start_time, end_time, start_seconds, speaker_id)

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

# Generate per-student summary
per_student = {}
for q in all_questions:
    student_resp = q.get('student_response', {})
    if student_resp and student_resp.get('student'):
        student = student_resp['student']
        if student not in per_student:
            per_student[student] = {
                'responses_count': 0,
                'contributions_count': 0,
                'quality_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
            }
        per_student[student]['responses_count'] += 1
        quality = student_resp.get('quality_score', 'C')
        if quality in per_student[student]['quality_distribution']:
            per_student[student]['quality_distribution'][quality] += 1

for c in all_contributions:
    student = c.get('student')
    if student:
        if student not in per_student:
            per_student[student] = {
                'responses_count': 0,
                'contributions_count': 0,
                'quality_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
            }
        per_student[student]['contributions_count'] += 1
        quality = c.get('quality_score', 'C')
        if quality in per_student[student]['quality_distribution']:
            per_student[student]['quality_distribution'][quality] += 1

print(f"\n" + "=" * 70)
print(f"📊 RESUMEN FINAL:")
print(f"=" * 70)
print(f"  - Total preguntas: {len(all_questions)}")
print(f"  - Total contribuciones: {len(all_contributions)}")
print(f"  - Bloques procesados: {len(all_block_results)}")
print(f"  - Hablantes identificados: {len(speaker_timeline)}")
print(f"  - Estudiantes únicos: {len(per_student)}\n")

print("Resumen por speaker:")
for item in speaker_timeline:
    print(f"  - {item['time_range']}: {item['speaker']} ({item['confidence']:.1f}%)")

# Save comprehensive analysis
output_data = {
    'session_id': '2026-04-07',
    'total_duration': '59:30',
    'blocks_analyzed': len(all_block_results),
    'processing_method': 'Voice Fingerprinting + Gemini 2.5-flash',
    'created_at': '2026-04-29',
    'teacher_questions': all_questions,
    'student_contributions': all_contributions,
    'speaker_timeline': speaker_timeline,
    'per_student_summary': per_student,
    'block_results': all_block_results
}

with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n✅ Análisis completo guardado en:")
print(f"   {output_file}")
print(f"\n✅ ¡Procesamiento completado exitosamente!")
print("=" * 70)
