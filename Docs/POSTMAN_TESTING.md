# 🚀 Panduan Pengujian API Backend (Postman)

Dokumen ini menjelaskan langkah demi langkah cara menggunakan **Postman** untuk menguji Backend (`RetailBE`) secara lokal, dan bagaimana cara memastikan pengunggahan file Anda **berhasil memicu Google Cloud Functions (ML Engine)**.

---

## ⚙️ Persiapan Awal
Sebelum membuka Postman, pastikan Backend Anda menyala dan siap terkoneksi ke Google Cloud:

1. Pastikan Anda memiliki file kredensial Service Account (berformat JSON) yang diletakkan di dalam folder `RetailBE` (misalnya dengan nama `credentials.json`).
2. Pastikan file `.env` sudah ada.
3. Jalankan server backend di terminal Anda:
   ```bash
   # Jalankan via Docker
   docker-compose up -d --build
   
   # ATAU jalankan manual dengan Uvicorn
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 🗝️ Langkah 1: Login & Dapatkan Token (Auth)
Backend ini dilindungi oleh autentikasi JWT. Anda harus *login* untuk mendapatkan token akses sebelum bisa mengunggah file.

- **Method**: `POST`
- **URL**: `http://localhost:8000/api/auth/login`
- **Headers**:
  - `Content-Type`: `application/json`
- **Body** (pilih tab *raw* lalu ubah *Text* menjadi *JSON*):
  ```json
  {
      "username": "user",
      "password": "user"
  }
  ```
  *(Catatan: Endpoint upload secara spesifik meminta otorisasi sebagai "user", jadi kita menggunakan kredensial standar user ini).*

**Tindakan**: 
Klik **Send**. Anda akan menerima respons berisi `access_token`. **Salin (Copy) teks token tersebut (tanpa tanda kutip)**.

---

## 📤 Langkah 2: Mengunggah CSV & Memicu Cloud Functions
Ini adalah inti pengujiannya. Backend akan menerima CSV Anda, lalu mengunggah *raw file* tersebut ke GCS Bucket (`retail-data-raw-izz`), yang mana secara otomatis akan "membangunkan" Cloud Function Anda.

- **Method**: `POST`
- **URL**: `http://localhost:8000/api/upload`
- **Headers**:
  - Pada tab **Authorization**, pilih tipe **Bearer Token**.
  - Masukkan (Paste) token yang Anda salin dari Langkah 1 ke kolom **Token**.
- **Body**:
  - Pilih tab **form-data**.
  - Di kolom *Key* baris pertama, ketik **`file`**.
  - Di dalam sel *Key* tersebut (saat kursor diarahkan), akan muncul tombol *dropdown* bertuliskan `Text`. Klik dan ubah menjadi **`File`**.
  - Di kolom *Value*, klik tombol **Select Files** lalu pilih file CSV mentah apa pun dari komputer Anda (Anda bisa menggunakan CSV dari folder `sample_data` di repo ML).

**Tindakan**:
Klik **Send**. 

**Hasil yang Diharapkan di Postman**:
```json
{
    "status": "success",
    "message": "File nama_file.csv berhasil diproses dan dikirim ke Data Warehouse.",
    "metadata": { ... }
}
```

---

## 🕵️‍♂️ Langkah 3: Verifikasi Cloud Function (GCP)
Apakah Cloud Function Anda benar-benar berjalan? Mari kita buktikan:

1. Buka Dasbor Google Cloud, cari **Cloud Run**, dan pilih fungsi **`retail-ml-engine`** Anda.
2. Buka tab **Logs** (Log).
3. Jika *setup* berhasil, Anda akan melihat log baru yang muncul tepat pada detik yang sama saat Anda menekan tombol *Send* di Postman. Log tersebut akan membuktikan bahwa fungsi ML Anda terbangun dan memproses CSV yang diunggah oleh Backend.

---

## 📥 Langkah 4: Cek Data Warehouse (Opsional)
Jika Anda ingin melihat apakah data sudah bersih dan masuk ke BigQuery:

1. Lakukan **Langkah 1** ulang, tapi kali ini ubah JSON-nya menjadi:
   ```json
   {
       "username": "admin",
       "password": "admin"
   }
   ```
2. Salin token admin tersebut.
3. Buat Request baru dengan **Method**: `GET`, **URL**: `http://localhost:8000/api/data`
4. Masukkan token admin di tab Authorization (Bearer Token).
5. Klik **Send**. Anda akan melihat tumpukan data bersih yang diambil langsung dari BigQuery!
