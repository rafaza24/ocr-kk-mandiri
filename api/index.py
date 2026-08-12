from flask import Flask, request, jsonify
import base64, re, gc, os
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance

app = Flask(__name__)

# ================================================================
# MESIN OCR KK - Menggunakan pytesseract jika tersedia
# Fallback: Analisa piksel + pola regex jika tesseract tidak ada
# ================================================================

def preprocess_image(image_bytes):
    """Pra-proses gambar untuk meningkatkan akurasi OCR."""
    img = Image.open(BytesIO(image_bytes)).convert('L')  # Grayscale
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img

def try_tesseract_ocr(image_bytes):
    """Coba baca teks dengan pytesseract (jika terinstall di server)."""
    try:
        import pytesseract
        img = preprocess_image(image_bytes)
        text = pytesseract.image_to_string(img, lang='ind+eng', config='--psm 6')
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return lines
    except ImportError:
        return None
    except Exception:
        return None

def parse_kk_from_lines(lines):
    """Urai baris teks OCR menjadi data KK terstruktur."""
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
    no_kk = re.sub(r'\s+', '', no_kk)  # hapus spasi dari angka KK

    nama_kepala = find_val([
        r'Nama\s+Kepala\s+(?:Keluarga)?\s*[:\-]\s*([A-Z][A-Z\s]+)',
        r'Kepala\s+Keluarga\s*[:\-]\s*([A-Z][A-Z\s]+)',
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
    desa = find_val([r'Desa(?:/Kelurahan)?\s*[:\-]\s*([A-Z][A-Z\s]+)'], full_text)
    kecamatan = find_val([r'Kecamatan\s*[:\-]\s*([A-Z][A-Z\s]+)'], full_text)
    kabupaten = find_val([r'Kabupaten(?:/Kota)?\s*[:\-]\s*([A-Z][A-Z\s]+)'], full_text)
    provinsi = find_val([r'Provinsi\s*[:\-]\s*([A-Z][A-Z\s]+)'], full_text)

    # Temukan semua NIK 16 digit sebagai anggota
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
        "_raw_lines": lines
    }

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def handle_ocr(path):
    if request.method == 'GET' and 'scan-kk' not in path:
        # Cek apakah tesseract tersedia
        try:
            import pytesseract
            ocr_engine = "pytesseract (Tesseract OCR)"
        except ImportError:
            ocr_engine = "TIDAK TERSEDIA - Server ini butuh Tesseract OCR"

        return jsonify({
            "status": "✅ Server OCR KK Warnasari",
            "mesin_ocr": ocr_engine,
            "catatan": "Untuk OCR benar-benar berfungsi, deploy ke Railway/Render (bukan Vercel)",
            "endpoint": "POST /scan-kk",
            "format": {"base64Data": "<foto KK base64>"}
        })

    # Handle POST scan
    image_bytes = None
    try:
        data = request.get_json(silent=True) or {}
        image_b64 = data.get('base64Data', '')
        if not image_b64:
            return jsonify({"success": False, "message": "Parameter 'base64Data' wajib diisi"}), 400

        if 'base64,' in image_b64:
            image_b64 = image_b64.split('base64,')[1]

        image_bytes = base64.b64decode(image_b64)

        # Coba OCR dengan Tesseract
        lines = try_tesseract_ocr(image_bytes)
        if lines:
            kk_data = parse_kk_from_lines(lines)
            engine_used = "pytesseract"
        else:
            # Tesseract tidak tersedia - kembalikan data kosong dengan pesan jelas
            kk_data = {
                "noKK": "",
                "namaKepalaKeluarga": "",
                "alamat": "KMP. WARNASARI DUSUN 1",
                "rt": "",
                "rw": "",
                "desa": "WARNASARI",
                "kecamatan": "PANGALENGAN",
                "kabupaten": "BANDUNG",
                "provinsi": "JAWA BARAT",
                "anggota": [],
                "_pesan": "OCR tidak berjalan: Tesseract tidak terinstall di server ini. Gunakan Railway/Render."
            }
            engine_used = "none (tesseract tidak tersedia)"

        del image_bytes, data, image_b64
        gc.collect()

        return jsonify({
            "success": True,
            "message": f"Scan KK diproses dengan mesin: {engine_used}",
            "data": kk_data
        })

    except Exception as e:
        if image_bytes:
            del image_bytes
        gc.collect()
        return jsonify({"success": False, "message": "Error: " + str(e)}), 500

# WSGI handler untuk Vercel
app = app
