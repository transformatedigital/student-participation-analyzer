# 📊 Integración de Análisis de Participación - 7 de Abril 2026

## Estado Actual ✅

### Datos Disponibles
- **Total de Participaciones:** 21 registros
- **Preguntas de Profesora:** 17
- **Contribuciones de Estudiantes:** 4
- **Cobertura Temporal:** 00:00:23 a 00:17:34 (17+ minutos)

### Participantes Identificados
1. **Dra. Ileana** - Instructora (85% del tiempo de clase)
2. **Aryang** - Estudiante de Indonesia (8% del tiempo)
3. **Grace** - Estudiante de Congo (1% del tiempo)

---

## Componentes Integrados

### 1. Frontend React Component
**Archivo:** `frontend/src/app/clases/[sessionId]/participacion/page.tsx`

**Características:**
- ✅ Tabla interactiva de participaciones
- ✅ Estadísticas en cards (Total, Preguntas, Contribuciones, Estudiantes)
- ✅ Calificación AI automática (A-E)
- ✅ Campo de entrada para calificaciones manuales
- ✅ Código de colores por tipo de participación
- ✅ Exportación a CSV con evaluaciones
- ✅ Interfaz responsive y moderna

### 2. Página HTML Standalone
**Archivo:** `data/clases/2026-04-07/Case_7_de_abril.html`

**Características:**
- ✅ Tabla completa de 21 participaciones
- ✅ Búsqueda en tiempo real
- ✅ Estadísticas visuales
- ✅ Interfaz profesional
- ✅ Exportación CSV funcional
- ✅ No requiere servidor (puro HTML/JS)

### 3. API Backend
**Archivo:** `backend/main.py`

**Endpoints:**
- `GET /api/clases/{session_id}/participacion`
  - Retorna teacher_questions, student_contributions, per_student_summary
- `GET /api/clases/{session_id}/timeline`
  - Retorna participation_timeline y full_transcription
- `GET /api/clases/{session_id}/transcripcion`
  - Retorna segmentos de transcripción completos

### 4. Datos Estructurados
**Archivo:** `data/clases/2026-04-07/analysis.json`

**Contenido:**
```json
{
  "session": {...},
  "participation_timeline": [401 entries, 40+ minutos],
  "full_transcription": [56 segments],
  "teacher_questions": [17 items with responses],
  "student_contributions": [4 items],
  "per_student_summary": {
    "Dr. Ileana": {...},
    "Aryang": {...},
    "Grace": {...}
  }
}
```

---

## Cómo Usar

### En la Plataforma Web
1. Navega a `/clases/2026-04-07/participacion`
2. Verás una tabla con todas las participaciones
3. Ingresa tus calificaciones manuales (A-E) en la columna derecha
4. Haz clic en "📥 Descargar CSV" para exportar los datos

### Archivo HTML Standalone
1. Abre `data/clases/2026-04-07/Case_7_de_abril.html` en navegador
2. Usa la búsqueda para filtrar por nombre, timestamp o contenido
3. Ingresa calificaciones manuales
4. Descarga CSV con el botón

### Consultar API
```bash
# Obtener datos de participación
curl http://localhost:8000/api/clases/2026-04-07/participacion

# Obtener timeline
curl http://localhost:8000/api/clases/2026-04-07/timeline

# Obtener transcripción
curl http://localhost:8000/api/clases/2026-04-07/transcripcion
```

---

## Estructura de Datos de Pregunta

```json
{
  "id": 1,
  "timestamp": "00:05:15",
  "question": "So, sorry, uh who make the adaptation, the ICE or the Soft Itech?",
  "directed_to": "Aryang",
  "student_response": {
    "student": "Dr. Ileana",
    "response": "Together.",
    "quality_score": "D",
    "quality_label": "Acceptable",
    "rationale": "The teacher answers their own question..."
  }
}
```

---

## Estructura de Datos de Contribución

```json
{
  "id": 0,
  "timestamp": "00:00:23",
  "student": "Aryang",
  "type": "voluntary_response",
  "content": "Okay, so because, uh, for the for the Microsoft Copilot...",
  "quality_score": "B",
  "quality_label": "Good",
  "rationale": "Aryang provides initial response with some elaboration..."
}
```

---

## Próximos Pasos (Opcional)

### Expansión a 60 Minutos
Para capturar todas las participaciones de toda la clase:

1. **Dividir Audio en Bloques:** ✅ Ya creado (7 bloques de 10 minutos)
   - Ubicación: `data/clases/2026-04-07/audio_blocks_10min/`

2. **Procesar con Gemini:** 
   - Requiere clave API de Google Gemini
   - Script preparado: `backend/analyze_blocks_gemini.py`

3. **Combinar Resultados:**
   - Script: `backend/expand_qa_analysis.py`

### Mejoras Futuras
- [ ] Análisis de participación de todos los 69 minutos
- [ ] Gráficos de distribución de participación
- [ ] Análisis de temas de discusión
- [ ] Reporte de progreso académico por estudiante
- [ ] Comparación con otras clases

---

## Archivos Generados

```
data/clases/2026-04-07/
├── analysis.json                          [Análisis principal]
├── Case_7_de_abril.html                   [Tabla HTML standalone]
├── audio_blocks_10min/                    [Bloques de 10 minutos]
│   ├── block_01_00000_00600.m4a
│   ├── block_02_00600_01200.m4a
│   ├── ... (7 bloques totales)
│   └── blocks_info.json
└── ...
```

---

**Fecha de Generación:** 29 de Abril de 2026  
**Duración Total de Clase:** 69 minutos y 24 segundos  
**Datos Procesados:** Gemini API + Análisis Local
