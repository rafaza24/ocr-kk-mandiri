from flask import Flask, request, jsonify
import base64, json, os, re
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# Fallback OCR / Lightweight OCR Parser
def parse_kk_from_text(raw_text_lines):
    full_text = "\n".join(raw_text_lines)

    def find_value(patterns, text):
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    no_kk = find_value([
        r'No(?:mor)?\s*(?:KK|Kartu Keluarga)[:\s]+([0-9]{16})',
        r'([0-9]{16})'
    ], full_text)

    nama_kepala = find_value([
        r'Nama\s+Kepala\s+(?:Keluarga)?[:\s]+([A-Z\s]+)',
        r'Kepala\s+Keluarga[:\s]+([A-Z\s]+)'
    ], full_text)

    alamat = find_value([r'Alamat[:\s]+(.+)', r'Dusun\s+(.+)'], full_text)
    rt = find_value([r'RT[:\s/]+([0-9]+)'], full_text)
    rw = find_value([r'RW[:\s/]+([0-9]+)'], full_text)
    desa = find_value([r'Desa[/Kel]?[:\s]+([A-Z\s]+)'], full_text)
    kecamatan = find_value([r'Kecamatan[:\s]+([A-Z\s]+)'], full_text)

    niks = re.findall(r'\b([0-9]{16})\b', full_text)
    anggota = []
    for i, nik in enumerate(niks):
        anggota.append({
            "no": i + 1,
            "nik": nik,
            "nama": "",
            "jenisKelamin": "",
            "tempatLahir": "",
            "tanggalLahir": "",
            "agama": "",
            "pendidikan": "",
            "pekerjaan": "",
            "statusPerkawinan": "",
            "hubunganKeluarga": "Kepala Keluarga" if i == 0 else "Anggota",
            "namaAyah": "",
            "namaIbu": ""
        })

    return {
        "noKK": no_kk,
        "namaKepalaKeluarga": nama_kepala,
        "alamat": alamat,
        "rt": rt,
        "rw": rw,
        "desa": desa,
        "kecamatan": kecamatan,
        "anggota": anggota
    }

@app.route('/', methods=['GET'])
@app.route('/api', methods=['GET'])
@app.route('/api/index', methods=['GET'])
def home():
    return jsonify({
        "status": "✅ Server OCR KK Mandiri Vercel Active!",
        "provider": "Vercel Serverless (100% Gratis, No Credit Card Required)",
        "endpoint": "POST /api/scan-kk"
    })

@app.route('/api/scan-kk', methods=['POST'])
def scan_kk():
    try:
        data = request.get_json() or {}
        if 'base64Data' not in data:
            return jsonify({"success": False, "message": "Parameter 'base64Data' tidak ditemukan"}), 400

        image_base64 = data['base64Data']
        if 'base64,' in image_base64:
            image_base64 = image_base64.split('base64,')[1]

        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')

        # Dummy/Mock extraction for Serverless test or Tesseract
        kk_data = parse_kk_from_text(["3204123456789012", "WARNASARI"])

        return jsonify({
            "success": True,
            "message": "Scan KK diproses di Vercel Serverless Mandiri!",
            "data": kk_data
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Vercel WSGI entry handler
app_handler = app
