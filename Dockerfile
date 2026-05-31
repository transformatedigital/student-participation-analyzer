FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install Node for runtime (if needed)
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend/requirements.txt ./backend/
COPY backend/*.py ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy frontend build
COPY --from=frontend-build /app/frontend/.next ./frontend/.next
COPY frontend/public ./frontend/public
COPY frontend/package*.json ./frontend/

# Copy data
COPY data ./data

EXPOSE 8000 3000

# Start both services
CMD sh -c "cd backend && python main.py &" && cd frontend && npm install --production && npm start
