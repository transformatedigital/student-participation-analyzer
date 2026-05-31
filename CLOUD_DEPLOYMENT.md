# Cloud Deployment Options - Clase Analytics

Si no quieres usar Docker localmente, puedes desplegar a la nube **gratis** (o muy barato).

## 🚀 Opción 1: Render (La más fácil) ⭐⭐⭐

Render tiene **free tier generoso** y es super fácil.

### Pasos

1. **Crea cuenta en [render.com](https://render.com)**
2. **Conecta tu repositorio GitHub**
   - Haz un push de este proyecto a GitHub
3. **Crea dos servicios Web:**
   - **Backend:**
     - Build Command: `pip install -r backend/requirements.txt`
     - Start Command: `cd backend && python main.py`
   - **Frontend:**
     - Build Command: `cd frontend && npm install && npm run build`
     - Start Command: `cd frontend && npm start`
4. **Variables de entorno:**
   - En frontend: `NEXT_PUBLIC_API_URL=https://tu-backend-url.onrender.com`

**Costo:** Gratis (Tier gratuito con limitaciones)

---

## 🚀 Opción 2: Vercel (Para el Frontend) + Railway (Backend)

### Frontend en Vercel
1. Ve a [vercel.com](https://vercel.com)
2. Importa tu repositorio
3. Establece root directory a `frontend/`
4. Deploy

**Costo:** Gratis

### Backend en Railway
1. Ve a [railway.app](https://railway.app)
2. Conecta GitHub
3. Selecciona este repositorio
4. Deploy

**Costo:** $5/mes (incluye mucho)

---

## 🚀 Opción 3: Google Cloud Run (Más profesional)

Ideal si ya tienes una cuenta de Google Cloud.

### Requisitos
- Cuenta Google Cloud
- Facturación activada (pero hay free tier)
- gcloud CLI instalado

### Deploy

```bash
# Construir imagen
docker build -t gcr.io/tu-proyecto/clase-analytics .

# Enviar a Google Container Registry
docker push gcr.io/tu-proyecto/clase-analytics

# Deploy a Cloud Run
gcloud run deploy clase-analytics \
  --image gcr.io/tu-proyecto/clase-analytics \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 3000 \
  --memory 512Mi
```

**Costo:** Gratis hasta 2M de solicitudes/mes

---

## 🚀 Opción 4: Docker Hub + Linode/DigitalOcean

### Pasos

1. **Subir a Docker Hub:**
```bash
docker login
docker tag clase-analytics-frontend tu-usuario/clase-analytics-frontend
docker push tu-usuario/clase-analytics-frontend
```

2. **Crear servidor en DigitalOcean ($5/mes)**
   - Crear Droplet (Ubuntu 22.04)
   - SSH into the server
   - Instalar Docker
   - Ejecutar: `docker run tu-usuario/clase-analytics-frontend`

**Costo:** $5/mes (servidor)

---

## Comparativa Rápida

| Servicio | Costo | Facilidad | Rendimiento |
|----------|-------|-----------|------------|
| **Render** | Gratis | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Vercel + Railway** | Gratis + $5 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Google Cloud Run** | Gratis | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **DigitalOcean** | $5/mes | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **AWS Lambda + API Gateway** | Gratis (primeros 12 meses) | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Mi Recomendación 💡

### Para Probar Rápido → **Render**
- Gratis
- Setup super simple (1 click)
- Ideal para demostración

### Para Producción → **Google Cloud Run o Vercel + Railway**
- Mejor escalabilidad
- Mejor rendimiento
- Mejor soporte

---

## Próximos Pasos

1. **Si quieres localhost:** Usa Docker Compose (ver `DOCKER.md`)
2. **Si quieres cloud gratis:** Crea cuenta en Render y sigue pasos arriba
3. **Si necesitas más:** Usa Google Cloud Run

¿Cuál prefieres? 🚀
