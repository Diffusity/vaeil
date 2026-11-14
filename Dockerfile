FROM node:24-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run typecheck && npm run build

FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VAEIL_FRONTEND_DIR=/app/frontend/dist
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .
COPY --from=frontend /build/frontend/dist ./frontend/dist
RUN useradd --create-home app
USER app
EXPOSE 10000
CMD ["sh", "-c", "exec python -m uvicorn vaeil.web:create_app --factory --host 0.0.0.0 --port ${PORT:-10000}"]
