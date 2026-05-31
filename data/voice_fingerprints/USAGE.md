# Voice Fingerprints - Guía de Uso

## Archivos Generados

- `voice_fingerprints_v1.0.json` - Huella digital maestra
- `fingerprints_summary.txt` - Resumen legible

## Hablantes Registrados

- Aryang
- Chilaka
- Grace
- Ileana
- Ileana 2
- Mega
- Sthepen


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
