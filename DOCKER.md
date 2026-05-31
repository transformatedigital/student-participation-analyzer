# Docker Setup - Clase Analytics

Ejecutar la aplicación completa con Docker es mucho más fácil que configurar Node.js y Python manualmente.

## Requisitos

- Docker instalado ([descargar](https://www.docker.com/products/docker-desktop))
- Docker Compose (incluido en Docker Desktop)

## Opción 1: Docker Compose (Recomendado) ⭐

La forma más fácil. Ejecuta un comando y todo está listo.

### 1. Abre una terminal

```bash
cd /Users/santi/clase-analytics
```

### 2. Inicia los servicios

```bash
docker-compose up --build
```

**Primera vez:** Tarda 2-3 minutos (descarga imágenes, instala dependencias)

Deberías ver:
```
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend-1  | ▲ Next.js 14.0.0
frontend-1  | - Local: http://localhost:3000
```

### 3. Abre en navegador

```
http://localhost:3000
```

### 4. Detener

Presiona `Ctrl + C` en la terminal.

---

## Opción 2: Docker Individual (Si prefieres más control)

### Backend

```bash
cd /Users/santi/clase-analytics

# Construir imagen
docker build -f Dockerfile.backend -t clase-analytics-backend .

# Ejecutar
docker run -p 8000:8000 -v $(pwd)/data:/app/data clase-analytics-backend
```

### Frontend (En otra terminal)

```bash
cd /Users/santi/clase-analytics

# Construir imagen
docker build -f Dockerfile.frontend -t clase-analytics-frontend .

# Ejecutar
docker run -p 3000:3000 clase-analytics-frontend
```

---

## Troubleshooting

### Puerto 3000 ya está en uso

```bash
# Usa otro puerto
docker run -p 3001:3000 clase-analytics-frontend
# Luego abre http://localhost:3001
```

### Puerto 8000 ya está en uso

```bash
docker run -p 8001:8000 clase-analytics-backend
# Actualiza la URL del API en las variables de entorno
```

### Limpiar todo

```bash
# Detener contenedores
docker-compose down

# Eliminar imágenes
docker rmi clase-analytics-backend clase-analytics-frontend

# Iniciar de nuevo
docker-compose up --build
```

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo frontend
docker-compose logs -f frontend
```

---

## Archivos Docker

- `docker-compose.yml` — Orquesta backend + frontend
- `Dockerfile.backend` — Imagen de FastAPI
- `Dockerfile.frontend` — Imagen de Next.js

---

## Notas

- Los datos en `/data` se montan como volumen, así que persisten entre reinicios
- El frontend se comunica con el backend a través de `http://localhost:8000`
- Cada vez que ejecutas `docker-compose up --build`, reconstruye las imágenes

¡Listo! Ahora puedes probar la aplicación sin configurar Node.js o Python en tu máquina. 🎉
