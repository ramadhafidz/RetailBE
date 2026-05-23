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

## 🕵️‍♂️ Langkah 3: Cara Melacak Data (Tracing End-to-End)

Setelah Anda menekan tombol *Send* di Postman pada Endpoint `/api/upload` dan mendapat balasan "success", Anda bisa melacak perjalanan asinkron data Anda langsung di Dasbor Google Cloud:

### A. Cek Google Cloud Storage (Bucket)
1. Buka [Cloud Storage Buckets](https://console.cloud.google.com/storage/browser).
2. Klik bucket **`retail-data-raw-izz`**.
3. Anda akan melihat file CSV mentah Anda di sana! Jika Anda mengeklik file tersebut dan menggulir ke bagian bawah, Anda akan melihat **Custom Metadata** berisi `{"uploaded_by": "user"}` yang dititipkan oleh Backend.

### B. Cek Google Cloud Functions (ML Engine)
1. Buka [Cloud Run Services](https://console.cloud.google.com/run) (karena fungsi Anda berbasis Gen 2).
2. Klik layanan **`retail-ml-engine`**, lalu buka tab **Logs**.
3. Cari *log* yang waktunya bersamaan dengan saat Anda menekan tombol di Postman. Anda akan melihat *log* proses mesin ML Anda berteriak: *"Ada file baru masuk!"* dan *"Mengirim data bersih ke BigQuery..."*. Ini membuktikan *Eventarc Trigger* bekerja sempurna!

### C. Cek BigQuery (Data Warehouse)
1. Buka [BigQuery SQL Workspace](https://console.cloud.google.com/bigquery).
2. Di panel penjelajah sebelah kiri, cari *Project* Anda, rentangkan dataset `retail_warehouse`, dan klik tabel `integrated_retail_data`.
3. Buka tab **Preview** (Pratinjau) atau jalankan perintah SQL ini:
   ```sql
   SELECT * FROM `datawarehouse-493606.retail_warehouse.integrated_retail_data` LIMIT 10
   ```
4. **Selesai!** Data CSV yang tadinya berantakan sekarang sudah rapi, terstandarisasi, dan siap dikonsumsi. Jangan lupa untuk mengecek apakah kolom `uploaded_by` sudah terisi dengan benar!
