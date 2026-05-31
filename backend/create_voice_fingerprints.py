#!/usr/bin/env python3
"""
Sistema de Huella Digital de Voz (Voice Fingerprinting)
Extrae características de voz y crea embeddings para identificación de speaker.
"""

import json
import os
import sys
from pathlib import Path
import subprocess
import numpy as np
from collections import defaultdict

try:
    import librosa
    import librosa.display
except ImportError:
    print("Instalando librosa...")
    os.system("pip install librosa soundfile numpy scikit-learn")
    import librosa

import warnings
warnings.filterwarnings('ignore')

print("🎤 SISTEMA DE HUELLA DIGITAL DE VOZ")
print("=" * 60)

# Paths
voice_examples_dir = Path("/Users/santi/clase-analytics/data/voice examples")
output_dir = Path("/Users/santi/clase-analytics/data/voice_fingerprints")
output_dir.mkdir(exist_ok=True)

# Get all voice files
voice_files = sorted(voice_examples_dir.glob("*.m4a"))
print(f"\n📁 Encontrados {len(voice_files)} ejemplos de voz:\n")

for f in voice_files:
    print(f"   ✓ {f.name}")

print("\n" + "=" * 60)
print("🔍 EXTRAYENDO CARACTERÍSTICAS DE VOZ")
print("=" * 60 + "\n")

fingerprints = {}
voice_features = defaultdict(dict)

def extract_audio_features(audio_path, sr=16000):
    """Extrae características detalladas de voz"""
    try:
        # Cargar audio
        y, sr = librosa.load(str(audio_path), sr=sr)

        # Características básicas
        duration = librosa.get_duration(y=y, sr=sr)

        # MFCC (Mel-Frequency Cepstral Coefficients) - muy importante para voz
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)

        # Chroma (tonalidad)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)

        # Espectral features
        spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spec_centroid_mean = np.mean(spec_centroid)
        spec_centroid_std = np.std(spec_centroid)

        spec_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spec_rolloff_mean = np.mean(spec_rolloff)

        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = np.mean(zero_crossing_rate)

        # RMS Energy
        rms = librosa.feature.rms(y=y)[0]
        rms_mean = np.mean(rms)
        rms_std = np.std(rms)

        # Tempogram (ritmo)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        return {
            'duration': float(duration),
            'mfcc_mean': mfcc_mean.tolist(),
            'mfcc_std': mfcc_std.tolist(),
            'chroma_mean': chroma_mean.tolist(),
            'spectral_centroid_mean': float(spec_centroid_mean),
            'spectral_centroid_std': float(spec_centroid_std),
            'spectral_rolloff_mean': float(spec_rolloff_mean),
            'zero_crossing_rate_mean': float(zcr_mean),
            'rms_mean': float(rms_mean),
            'rms_std': float(rms_std),
            'onset_strength_mean': float(np.mean(onset_env))
        }
    except Exception as e:
        print(f"   ❌ Error procesando {audio_path.name}: {e}")
        return None

# Procesar cada archivo de voz
for voice_file in voice_files:
    speaker_name = voice_file.stem
    print(f"🎤 {speaker_name}:")

    # Información del archivo
    file_size_mb = voice_file.stat().st_size / (1024 * 1024)
    print(f"   Archivo: {voice_file.name} ({file_size_mb:.2f} MB)")

    # Extraer características
    features = extract_audio_features(voice_file)

    if features:
        voice_features[speaker_name] = features

        # Crear fingerprint compacto
        fingerprint = {
            'speaker': speaker_name,
            'file': voice_file.name,
            'file_size_mb': file_size_mb,
            'duration': features['duration'],
            'features': {
                'mfcc_mean': features['mfcc_mean'],
                'mfcc_std': features['mfcc_std'],
                'spectral_centroid_mean': features['spectral_centroid_mean'],
                'spectral_centroid_std': features['spectral_centroid_std'],
                'spectral_rolloff_mean': features['spectral_rolloff_mean'],
                'rms_mean': features['rms_mean'],
                'rms_std': features['rms_std'],
                'zero_crossing_rate_mean': features['zero_crossing_rate_mean']
            }
        }

        fingerprints[speaker_name] = fingerprint

        print(f"   ✓ Duración: {features['duration']:.2f}s")
        print(f"   ✓ MFCC mean: {np.mean(features['mfcc_mean']):.4f}")
        print(f"   ✓ Spectral centroid: {features['spectral_centroid_mean']:.2f} Hz")
        print(f"   ✓ RMS energy: {features['rms_mean']:.4f}")
        print()

print("\n" + "=" * 60)
print("💾 GENERANDO HUELLA DIGITAL MAESTRA")
print("=" * 60 + "\n")

# Crear archivo de huella digital
voice_fingerprints_data = {
    'metadata': {
        'created': '2026-04-29',
        'version': '1.0',
        'model': 'Voice Fingerprinting v1.0',
        'description': 'Digital voice fingerprints for speaker identification',
        'total_speakers': len(fingerprints),
        'total_samples': len(voice_files),
        'sr': 16000,
        'features': [
            'mfcc_mean', 'mfcc_std', 'spectral_centroid_mean',
            'spectral_centroid_std', 'spectral_rolloff_mean',
            'rms_mean', 'rms_std', 'zero_crossing_rate_mean'
        ]
    },
    'speakers': fingerprints,
    'raw_features': voice_features
}

# Guardar
output_file = output_dir / "voice_fingerprints_v1.0.json"
with open(output_file, 'w') as f:
    json.dump(voice_fingerprints_data, f, indent=2)

print(f"✅ Huella digital guardada: {output_file}")
print(f"   Tamaño: {output_file.stat().st_size / 1024:.1f} KB")

# Crear archivo de resumen
summary_file = output_dir / "fingerprints_summary.txt"
with open(summary_file, 'w') as f:
    f.write("RESUMEN DE HUELLA DIGITAL DE VOZ\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Fecha: 2026-04-29\n")
    f.write(f"Total de Hablantes: {len(fingerprints)}\n")
    f.write(f"Total de Muestras: {len(voice_files)}\n\n")

    f.write("HABLANTES REGISTRADOS:\n")
    f.write("-" * 60 + "\n")
    for speaker, fp in fingerprints.items():
        f.write(f"\n{speaker.upper()}\n")
        f.write(f"  Archivo: {fp['file']}\n")
        f.write(f"  Duración: {fp['duration']:.2f} segundos\n")
        f.write(f"  Características extraídas: {len(fp['features'])} tipos\n")
        f.write(f"  MFCC promedio: {np.mean(fp['features']['mfcc_mean']):.4f}\n")
        f.write(f"  Centroide espectral: {fp['features']['spectral_centroid_mean']:.2f} Hz\n")
        f.write(f"  Energía RMS: {fp['features']['rms_mean']:.4f}\n")

print(f"✅ Resumen guardado: {summary_file}")

# Mostrar resumen
print("\n" + "=" * 60)
print("📊 HABLANTES REGISTRADOS EN LA HUELLA DIGITAL")
print("=" * 60 + "\n")

for speaker, fp in fingerprints.items():
    print(f"🎤 {speaker.upper()}")
    print(f"   Duración: {fp['duration']:.2f}s")
    print(f"   Centroide Espectral: {fp['features']['spectral_centroid_mean']:.2f} Hz")
    print(f"   Energía RMS: {fp['features']['rms_mean']:.4f}")
    print()

# Crear archivo para futuros análisis
print("\n" + "=" * 60)
print("✅ HUELLA DIGITAL LISTA PARA USO FUTURO")
print("=" * 60)

usage_file = output_dir / "USAGE.md"
with open(usage_file, 'w') as f:
    f.write("""# Voice Fingerprints - Guía de Uso

## Archivos Generados

- `voice_fingerprints_v1.0.json` - Huella digital maestra
- `fingerprints_summary.txt` - Resumen legible

## Hablantes Registrados

""")
    for speaker in sorted(fingerprints.keys()):
        f.write(f"- {speaker}\n")

    f.write("""

## Cómo Usar

```python
import json

# Cargar huella digital
with open('voice_fingerprints_v1.0.json') as f:
    fingerprints = json.load(f)

# Ver hablantes disponibles
speakers = fingerprints['speakers'].keys()
print(speakers)

# Acceder a características de un hablante
aryang_features = fingerprints['speakers']['Aryang']['features']
```

## Características por Hablante

Cada hablante tiene 8 características extraídas:

1. **MFCC Mean** - Coeficientes cepstrales de frecuencia de mel (promedio)
2. **MFCC Std** - Desviación estándar de MFCC
3. **Spectral Centroid Mean** - Centro de masa espectral
4. **Spectral Centroid Std** - Variabilidad del centroide
5. **Spectral Rolloff Mean** - Umbral espectral
6. **RMS Mean** - Energía RMS promedio
7. **RMS Std** - Variabilidad de energía
8. **Zero Crossing Rate Mean** - Tasa de cruce de cero

## Próximos Pasos

1. Usar estas características para entrenar clasificador
2. Procesar nuevos audios con el modelo
3. Identificar speakers en bloques de 5 minutos
4. Generar análisis de participación automático
""")

print(f"\n✅ Guía de uso: {usage_file}")

print("\n" + "=" * 60)
print("🎉 COMPLETADO: HUELLA DIGITAL DE VOZ LISTA")
print("=" * 60)
print(f"""
Ubicación: {output_dir}

Archivos generados:
  ✅ voice_fingerprints_v1.0.json (datos completos)
  ✅ fingerprints_summary.txt (resumen)
  ✅ USAGE.md (guía de uso)

Puedes usar esta huella digital para:
  🎯 Identificar speakers en nuevos audios
  🎯 Analizar bloques de 5 minutos
  🎯 Generar reporte de participación automático
  🎯 Entrenar clasificadores de voz
""")
