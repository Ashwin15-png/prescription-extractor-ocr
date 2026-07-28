# Production Dockerfile for Prescription Extractor API
FROM python:3.12-slim AS base

# Install system dependencies for Tesseract OCR and OpenCV (libgl1 replaces obsolete libgl1-mesa-glx in Debian Bookworm/Trixie)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app ./backend/app
COPY frontend/web ./frontend/web
COPY seed_data.py .
COPY gunicorn.conf.py .

# Ensure upload directory exists with proper permissions
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# Environment defaults
ENV ENV=production \
    DEBUG=False \
    PORT=8000 \
    TESSERACT_CMD=/usr/bin/tesseract

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "backend.app.main:app"]
