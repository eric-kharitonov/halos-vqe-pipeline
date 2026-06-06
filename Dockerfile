# HALOS — single-service deploy.
# Builds the React/Vite frontend, then serves it (plus the FastAPI /api routes and
# the real Qiskit VQE/QAOA + ESMFold pipeline) from one Python container.

# ---- Stage 1: build the React/Vite frontend ----
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python backend that serves the built SPA + API ----
FROM python:3.13-slim AS app
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY backend/ backend/
COPY data/ data/
COPY --from=frontend /app/frontend/dist frontend/dist

WORKDIR /app/backend
ENV PORT=8000
# Render injects $PORT; bind to it. Shell form so ${PORT} expands.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
