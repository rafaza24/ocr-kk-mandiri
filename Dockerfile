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

EXPOSE 5000

# Jalankan gunicorn yang bind ke port 5000 dan 8080 sekaligus
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-b", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "app:app"]
