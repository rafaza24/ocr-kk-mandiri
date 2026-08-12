FROM python:3.11-slim

# Install Tesseract OCR + paket bahasa Indonesia & Inggris
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-ind \
        tesseract-ocr-eng \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy kode aplikasi
COPY app.py .

# Script startup yang bind ke $PORT, 5000, dan 8080 secara bersamaan
RUN printf '#!/bin/sh\nPORT_VAL="${PORT:-5000}"\nexec gunicorn --bind 0.0.0.0:${PORT_VAL} --bind 0.0.0.0:5000 --bind 0.0.0.0:8080 --timeout 120 --workers 1 app:app\n' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
