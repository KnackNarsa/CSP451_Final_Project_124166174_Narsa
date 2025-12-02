# applications/backend/Dockerfile

FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Copy backend code
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Expose app port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
