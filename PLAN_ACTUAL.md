# Plan Actual de Procesamiento - Audio Limpio + Identificación de Voz

## 📍 Estado Actual

### Audio Procesado
- **Original:** `audio_unificado.m4a` (69:24) 
- **Recortado:** `audio_unificado_trimmed.m4a` (59:30) ✅
  - Recorte: Hasta minuto 59:30 (cortó contenido irrelevante del minuto 61:31+)
  - Ubicación: `/Users/santi/clase-analytics/data/clases/2026-04-07/`

### Bloques de Audio
- **Formato:** 5 minutos cada uno (más precisión que 10 minutos)
- **Total:** 12 bloques
- **Ubicación:** `/Users/santi/clase-analytics/data/clases/2026-04-07/audio_blocks_5min_cleaned/`

---

## 🎤 Próximo Paso: Huella Vocal (Voice Fingerprinting)

### Necesario del Usuario:
Proporcionar 6 archivos de voz (~30 segundos cada uno):
1. `Aryang.m4a` - Huella vocal de Aryang
2. `Grace.m4a` - Huella vocal de Grace
3. `Dr_Ileana.m4a` - Huella vocal de Dra. Ileana
4. `Speaker_4.m4a` - Otros participantes
5. `Speaker_5.m4a`
6. `Speaker_6.m4a`

### Qué Haremos:
1. Extraer características de voz de cada huella
2. Crear modelo de identificación de speaker
3. Procesar cada bloque de 5 minutos con identificación automática
4. Extraer Q&A con nombres correctos basados en voz
5. Generar análisis final con 59:30 minutos de contenido limpio

---

## 📋 Archivos Relevantes

```
/Users/santi/clase-analytics/data/clases/2026-04-07/
├── audio_unificado.m4a              (original, 69:24)
├── audio_unificado_trimmed.m4a      (recortado, 59:30) ✅
├── audio_blocks_5min_cleaned/       (12 bloques de 5 min) ✅
│   ├── block_01_00000_00300.m4a
│   ├── block_02_00300_00600.m4a
│   ├── ... (12 total)
│   └── blocks_5min_info.json
├── analysis.json                     (actual, con 7 bloques de 10min)
└── Case_7_de_abril.html              (tabla, 185 participaciones)
```

---

## ✅ Checklist

- [x] Audio revisado y recortado a 59:30
- [x] Copia recortada creada y guardada
- [x] Bloques de 5 minutos creados (12 totales)
- [ ] 6 huellas vocales proporcionadas por usuario
- [ ] Modelo de identificación de speaker entrenado
- [ ] Procesamiento de bloques con Gemini + speaker detection
- [ ] Integración final de análisis
- [ ] Actualización de plataforma con datos limpios

---

## 🔄 Flujo Próximo

1. Usuario proporciona 6 archivos de voz
2. Entrenamos modelo de identificación
3. Procesamos 12 bloques con Gemini + speaker ID
4. Combinamos Q&A con identificación de speaker correcta
5. Generamos análisis final limpio y preciso
