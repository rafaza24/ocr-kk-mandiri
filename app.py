from flask import Flask, request, jsonify
import base64, json, os, re
from io import BytesIO
from PIL import Image
import easyocr

app = Flask(__name__)

# Inisialisasi model EasyOCR (open-source, 100% lokal, tanpa API pihak ketiga)
# Model diunduh sekali saat server pertama kali start, lalu berjalan lokal
print("⏳ Memuat model EasyOCR (Bahasa Indonesia + Inggris)...")
reader = easyocr.Reader(['id', 'en'], gpu=False)
print("✅ Model EasyOCR siap digunakan!")

# ================================================================
# Parser Teks KK dari Hasil OCR
# ================================================================

def parse_kk_from_text(raw_text_lines):
    """
    Mengurai hasil teks OCR mentah menjadi data KK terstruktur (JSON).
    """
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

    alamat = find_value([
        r'Alamat[:\s]+(.+)',
        r'Jl\.\s*(.+)',
        r'Dusun\s+(.+)'
    ], full_text)

    rt = find_value([r'RT[:\s/]+([0-9]+)'], full_text)
    rw = find_value([r'RW[:\s/]+([0-9]+)'], full_text)
    desa = find_value([r'Desa[/Kel]?[:\s]+([A-Z\s]+)'], full_text)
    kecamatan = find_value([r'Kecamatan[:\s]+([A-Z\s]+)'], full_text)
    kabupaten = find_value([r'Kabupaten[/Kota]?[:\s]+([A-Z\s]+)'], full_text)
    provinsi = find_value([r'Provinsi[:\s]+([A-Z\s]+)'], full_text)

    # Deteksi NIK anggota (16 digit angka)
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
        "kabupaten": kabupaten,
        "provinsi": provinsi,
        "anggota": anggota,
        "_raw_ocr_text": raw_text_lines  # Teks mentah OCR untuk debugging
    }

# ================================================================
# Endpoint API
# ================================================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "✅ Server OCR KK Mandiri (100% Open Source) Berjalan!",
        "model": "EasyOCR - Bahasa Indonesia + Inggris",
        "privasi": "Data TIDAK dikirim ke pihak ketiga. 100% diproses di server ini.",
        "endpoint": "POST /scan-kk",
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/scan-kk', methods=['POST'])
def scan_kk():
    try:
        data = request.get_json()
        if not data or 'base64Data' not in data:
            return jsonify({"success": False, "message": "Parameter 'base64Data' tidak ditemukan"}), 400

        image_base64 = data['base64Data']
        if 'base64,' in image_base64:
            image_base64 = image_base64.split('base64,')[1]

        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')

        # Jalankan OCR dengan model EasyOCR lokal (100% privat, tanpa internet)
        results = reader.readtext(image_bytes, detail=0, paragraph=False)

        # Urai teks hasil OCR menjadi data KK terstruktur
        kk_data = parse_kk_from_text(results)

        return jsonify({
            "success": True,
            "message": "Scan KK berhasil! Diproses 100% di server lokal open-source.",
            "data": kk_data
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
