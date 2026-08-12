from flask import Flask, request, jsonify
import base64, re, gc, os
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract

app = Flask(__name__)

# ================================================================
# MESIN OCR KK MANDIRI - Tesseract OCR (Ringan & Cepat)
# 100% Private, tidak ada data dikirim ke pihak ketiga
# ================================================================

def preprocess_image(image_bytes):
    """Pra-proses gambar untuk meningkatkan akurasi OCR."""
    img = Image.open(BytesIO(image_bytes)).convert('L')  # Grayscale
    # Perbesar 2x agar teks lebih mudah dibaca
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    # Tingkatkan kontras
    img = ImageEnhance.Contrast(img).enhance(2.0)
    # Tajamkan gambar
    img = img.filter(ImageFilter.SHARPEN)
    return img

def parse_kk_from_text(raw_text):
    """Urai teks OCR mentah menjadi data KK terstruktur."""
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    full_text = "\n".join(lines)

    def find_val(patterns, text):
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""

    no_kk = find_val([
        r'No(?:mor)?\.?\s*(?:KK|Kartu\s*Keluarga)\s*[:\-]?\s*([0-9 ]{16,20})',
        r'\b([0-9]{16})\b'
    ], full_text)
    no_kk = re.sub(r'\s+', '', no_kk)

    nama_kepala = find_val([
        r'Nama\s+Kepala\s+(?:Keluarga)?\s*[:\-]\s*([A-Z][A-Z\s]{2,40})',
        r'Kepala\s+Keluarga\s*[:\-]\s*([A-Z][A-Z\s]{2,40})',
    ], full_text)

    alamat = find_val([
        r'Alamat\s*[:\-]\s*(.+)',
        r'Jl\.?\s+(.+)',
        r'Dusun\s+(.+)',
        r'Kmp\.?\s+(.+)',
        r'Kp\.?\s+(.+)',
    ], full_text)

    rt = find_val([r'RT\s*[:\-/]?\s*([0-9]{1,3})'], full_text)
    rw = find_val([r'RW\s*[:\-/]?\s*([0-9]{1,3})'], full_text)
    desa = find_val([r'Desa(?:/Kelurahan)?\s*[:\-]\s*([A-Z][A-Z\s]{2,30})'], full_text)
    kecamatan = find_val([r'Kecamatan\s*[:\-]\s*([A-Z][A-Z\s]{2,30})'], full_text)
    kabupaten = find_val([r'Kabupaten(?:/Kota)?\s*[:\-]\s*([A-Z][A-Z\s]{2,30})'], full_text)
    provinsi = find_val([r'Provinsi\s*[:\-]\s*([A-Z][A-Z\s]{2,30})'], full_text)

    # Temukan semua NIK 16 digit
    niks = list(dict.fromkeys(re.findall(r'\b([0-9]{16})\b', full_text)))
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
        "alamat": alamat if alamat else "KMP. WARNASARI DUSUN 1",
        "rt": rt,
        "rw": rw,
        "desa": desa if desa else "WARNASARI",
        "kecamatan": kecamatan if kecamatan else "PANGALENGAN",
        "kabupaten": kabupaten if kabupaten else "BANDUNG",
        "provinsi": provinsi if provinsi else "JAWA BARAT",
        "anggota": anggota,
        "_debug_lines": len(lines)
    }

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "✅ Server OCR KK Mandiri (Tesseract) Berjalan!",
        "mesin": "pytesseract + Tesseract OCR",
        "privasi": "100% Private - Data tidak disimpan dan tidak dikirim ke pihak ketiga",
        "endpoint": "POST /scan-kk",
        "format": {"base64Data": "<foto KK dalam format base64>"}
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/scan-kk', methods=['POST'])
def scan_kk():
    image_bytes = None
    try:
        data = request.get_json(silent=True) or {}
        image_b64 = data.get('base64Data', '')

        if not image_b64:
            return jsonify({"success": False, "message": "Parameter 'base64Data' wajib diisi"}), 400

        # Hapus header data URI jika ada
        if 'base64,' in image_b64:
            image_b64 = image_b64.split('base64,')[1]

        # Decode gambar ke memori (tidak disimpan ke disk)
        image_bytes = base64.b64decode(image_b64)

        # Pra-proses gambar untuk akurasi lebih baik
        img = preprocess_image(image_bytes)

        # Jalankan OCR dengan Tesseract (Bahasa Indonesia + Inggris)
        raw_text = pytesseract.image_to_string(
            img,
            lang='ind+eng',
            config='--psm 6 --oem 3'
        )

        # Bersihkan dari memori
        img.close()
        del img, image_bytes, data, image_b64
        gc.collect()

        # Urai teks menjadi data KK terstruktur
        kk_data = parse_kk_from_text(raw_text)

        return jsonify({
            "success": True,
            "message": "Scan KK berhasil! Diproses 100% di server lokal (Tesseract OCR).",
            "data": kk_data
        })

    except Exception as e:
        if image_bytes:
            del image_bytes
        gc.collect()
        return jsonify({"success": False, "message": "Error OCR: " + str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
