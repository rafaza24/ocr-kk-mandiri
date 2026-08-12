# 🤖 Mesin OCR AI Kartu Keluarga (KK) Mandiri

Proyek ini adalah mesin **Vision OCR Artificial Intelligence (AI)** mandiri berbasis Deep Learning yang khusus dilatih untuk membaca dokumen **Kartu Keluarga (KK) Indonesia**.

100% Bebas dari ketergantungan API pihak ketiga (seperti Google Gemini/OpenAI), 100% Gratis pemakaian, dan 100% Data Privat.

---

## 📁 Struktur Direktori Proyek

```
mesin-ocr-kk-ai/
├── dataset/
│   ├── images/              # Folder 50+ gambar KK sintetis buatan generator (.png)
│   └── annotations.json     # Label Ground-Truth JSON lengkap untuk pelatihan AI
├── models/                  # Folder penyimpanan bobot model fine-tuned (.pth / .onnx)
├── scripts/
│   ├── generate_synthetic_kk_dataset.py  # Generator dataset KK otomatis
│   └── server_ocr_api.py                 # REST API server (Flask/PyTorch)
└── README.md                # Panduan proyek
```

---

## 🚀 Panduan Penggunaan & Pelatihan

### 1. Membuat Dataset Gambar Sintetis Tambahan
Untuk membuat gambar Kartu Keluarga simulasi secara otomatis tanpa melanggar privasi warga:
```bash
python3 scripts/generate_synthetic_kk_dataset.py
```
*Script ini otomatis membuat gambar KK sintetis beresolusi tinggi di `dataset/images/` beserta kuncinya di `annotations.json`.*

### 2. Menjalankan Server API Lokal
Untuk menjalankan server OCR AI buatan sendiri di port 5000:
```bash
python3 scripts/server_ocr_api.py
```

### 3. Mengintegrasikan ke Google Apps Script (Warnasari Data)
Ganti pemanggilan `scanKKWithAI` di `Code.gs` dengan memanggil URL server mandiri Anda:
```javascript
function scanKKMandiri(base64Data) {
  var url = "https://server-ocr-desa-anda.com/scan-kk"; // atau IP VPS Anda
  var payload = JSON.stringify({ base64Data: base64Data });
  var options = {
    method: "post",
    contentType: "application/json",
    payload: payload,
    muteHttpExceptions: true
  };
  var response = UrlFetchApp.fetch(url, options);
  return JSON.parse(response.getContentText());
}
```
