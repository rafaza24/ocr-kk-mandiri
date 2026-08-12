FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

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

CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app
