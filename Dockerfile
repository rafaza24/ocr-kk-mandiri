FROM python:3.11-slim

# Install Tesseract OCR + bahasa Indonesia + Inggris
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-ind \
        tesseract-ocr-eng && \
    rm -rf /var/lib/apt/lists/*

# Set direktori kerja
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy kode aplikasi saja
COPY app.py .

# Jalankan gunicorn dengan PORT dari Railway ($PORT)
CMD sh -c "gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --timeout 120 --workers 1"
