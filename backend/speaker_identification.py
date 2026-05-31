#!/usr/bin/env python3
"""
Identificador de Speakers usando Huella Digital de Voz
Compara características de nuevos audios con la huella digital entrenada.
"""

import json
import os
from pathlib import Path
import numpy as np

try:
    import librosa
except ImportError:
    os.system("pip install librosa")
    import librosa

print("🎤 IDENTIFICADOR DE SPEAKERS")
print("=" * 70)

# Cargar huella digital
fingerprints_file = Path("/Users/santi/clase-analytics/data/voice_fingerprints/voice_fingerprints_v1.0.json")
with open(fingerprints_file) as f:
    fingerprints_data = json.load(f)

speakers_fingerprints = fingerprints_data['speakers']

print(f"\n✅ Huella digital cargada: {fingerprints_file.name}")
print(f"   Hablantes disponibles: {list(speakers_fingerprints.keys())}")

def extract_features_from_audio(audio_path, sr=16000):
    """Extrae las mismas características usadas en fingerprinting"""
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
        return None

def euclidean_distance(feat1, feat2):
    """Calcula distancia euclidiana entre características"""
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
    """Identifica el speaker más probable de un audio"""
    features = extract_features_from_audio(audio_path)

    if features is None:
        return None

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
        'all_scores': scores,
        'top_3': [(sp, s['confidence']) for sp, s in sorted_scores[:3]]
    }

print("\n" + "=" * 70)
print("🧪 PRUEBA: IDENTIFICACIÓN EN BLOQUES DE 5 MINUTOS")
print("=" * 70)

blocks_dir = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/audio_blocks_5min_cleaned")

if blocks_dir.exists():
    block_files = sorted(blocks_dir.glob("block_*.m4a"))[:3]

    print(f"\nProcesando {len(block_files)} bloques de prueba...\n")

    results = []

    for block_file in block_files:
        print(f"📊 {block_file.name}:")

        result = identify_speaker(block_file)

        if result:
            speaker = result['speaker']
            confidence = result['confidence']

            print(f"   🎤 Identificado: {speaker}")
            print(f"   📈 Confianza: {confidence:.1f}%")

            print(f"   Top 3:")
            for i, (sp, conf) in enumerate(result['top_3'], 1):
                print(f"      {i}. {sp}: {conf:.1f}%")

            results.append({
                'block': block_file.name,
                'speaker': speaker,
                'confidence': confidence
            })
        print()

    test_results = {
        'model': 'Voice Fingerprinting Identification v1.0',
        'timestamp': '2026-04-29',
        'note': 'Ileana con doble validación (2 muestras) por dominancia en grabaciones',
        'test_blocks': len(block_files),
        'results': results
    }

    test_file = Path("/Users/santi/clase-analytics/data/voice_fingerprints/test_identification_results.json")
    with open(test_file, 'w') as f:
        json.dump(test_results, f, indent=2)

    print("=" * 70)
    print(f"✅ Resultados de prueba: {test_file.name}")
else:
    print(f"⚠️ Carpeta no encontrada: {blocks_dir}")

print("\n" + "=" * 70)
print("🎉 IDENTIFICADOR LISTO PARA PROCESAR AUDIOS")
print("=" * 70)
