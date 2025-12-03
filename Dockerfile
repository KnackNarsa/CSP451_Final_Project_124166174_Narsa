# Production Dockerfile for Cloudmart (API + frontend)
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Install backend dependencies
COPY applications/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend FastAPI app
COPY applications/backend/app ./app

# Copy frontend files
COPY applications/frontend/src ./static

# Runtime Stage

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY applications/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /build/app ./app
COPY --from=builder /build/static ./static

ENV PORT=80
EXPOSE 80


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]