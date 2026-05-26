# Panduan Testing Backend dengan Postman

Dokumen ini berisi langkah demi langkah untuk mengetes endpoint FastAPI backend menggunakan Postman.

## 1. Pastikan backend sudah berjalan

Sebelum membuka Postman, jalankan backend terlebih dahulu.

Contoh perintah dari root project:

```bash
uvicorn Back_end.main:app --reload --host 0.0.0.0 --port 8000
```

Kalau backend sukses berjalan, base URL yang dipakai di Postman adalah:

```text
http://localhost:8000
```

## 2. Siapkan environment di Postman

1. Buka Postman.
2. Klik **Environments**.
3. Buat environment baru, misalnya `Local Backend`.
4. Tambahkan variable:
	 - `base_url` = `http://localhost:8000`
5. Simpan environment tersebut.
6. Pilih environment `Local Backend` di kanan atas Postman.

Dengan begitu, semua request bisa pakai `{{base_url}}`.

## 3. Testing endpoint `POST /api/upload`

## Authentication (Login)

Mulai versi dengan proteksi, beberapa endpoint memerlukan token Bearer dan role tertentu.

1. Buat request `POST {{base_url}}/api/auth/login` dengan body JSON:

```json
{
	"username": "admin",
	"password": "admin"
}
```

2. Jika sukses, response berisi `access_token`, `role`, dan `username`.

3. Untuk role `user`, gunakan:

```json
{
	"username": "user",
	"password": "user"
}
```

4. Di Postman, di tab **Authorization** pilih **Bearer Token** dan masukkan token tersebut, atau tambahkan header manual:

```
Authorization: Bearer <access_token>
```

Catatan: Default credential lokal adalah `admin`/`admin` untuk dashboard dan `user`/`user` untuk upload data. Untuk production, set `AUTH_ADMIN_*`, `AUTH_USER_*`, dan `AUTH_SECRET_KEY` di environment server.

### Trik Otomasi Token (Sangat Direkomendasikan)
Agar Anda tidak perlu menyalin (*copy-paste*) token secara manual setiap kali login, Anda bisa menyuruh Postman menyimpan token tersebut secara otomatis ke variabel Environment.

1. Buka *request* `POST /api/auth/login`.
2. Masuk ke tab **Tests** (atau **Scripts** -> **Post-response**).
3. Tempelkan kode JavaScript berikut:

```javascript
var jsonData = pm.response.json();

if (jsonData.access_token) {
    if (jsonData.role === "admin") {
        pm.environment.set("admin_token", jsonData.access_token);
    } else if (jsonData.role === "user") {
        pm.environment.set("user_token", jsonData.access_token);
    }
}
```

4. Tekan **Save** lalu **Send**. Token akan otomatis tersimpan.
5. Pada *request* lain (seperti Upload File), cukup masuk ke tab **Authorization** -> **Bearer Token**, dan isi kotaknya dengan `{{user_token}}` (untuk kasir) atau `{{admin_token}}` (untuk admin). Postman akan mengisinya otomatis!


Endpoint ini dipakai untuk upload file CSV, diproses oleh backend, lalu hasilnya dikirim ke pipeline/Data Warehouse.

### Langkah-langkah

1. Klik **New** > **HTTP Request**.
2. Ubah method menjadi **POST**.
3. Isi URL dengan:

```text
{{base_url}}/api/upload
```

4. Masuk ke tab **Body**.
5. Pilih opsi **form-data**.
6. Tambahkan key berikut:
	 - Key: `file`
	 - Type: `File`
	 - Pilih file CSV, misalnya `cabang_bogor.csv` dari folder `Machine_Learning/sample_data/`.
7. Pastikan tidak perlu mengisi header manual untuk `Content-Type`, karena Postman akan mengaturnya otomatis.
8. Klik **Send**.

### Response yang diharapkan

Kalau sukses, response biasanya berbentuk JSON seperti ini:

```json
{
	"status": "success",
	"message": "File cabang_bogor.csv berhasil diproses dan dikirim ke Data Warehouse.",
	"metadata": {
		"total_rows_processed": 100,
		"source_file": "cabang_bogor.csv"
	},
	"mapping_result": {
		"id_brg": "product_id",
		"nama": "product_name",
		"harga_jual": "price",
		"sisa_stok": "stock",
		"kategori_item": "category"
	},
	"preview_data": [
		{
			"product_id": "A001",
			"product_name": "Mie Gacoan Level 1",
			"price": 10000,
			"stock": 50,
			"category": "Makanan",
			"source_file": "cabang_bogor.csv",
			"processed_at": "2026-05-04T10:00:00Z"
		}
	]
}
```

### Cara cek hasilnya

- `status` harus bernilai `success`.
- `message` menjelaskan file berhasil diproses.
- `metadata.total_rows_processed` menunjukkan jumlah baris CSV yang dibaca.
- `mapping_result` menunjukkan mapping kolom asli ke kolom target.
- `preview_data` menampilkan contoh data hasil proses.

## 4. Testing endpoint `GET /api/data`

Endpoint ini dipakai untuk mengambil data terbaru dari BigQuery dan ditampilkan di frontend.

### Langkah-langkah

1. Klik **New** > **HTTP Request**.
2. Ubah method menjadi **GET**.
3. Isi URL dengan:

```text
{{base_url}}/api/data
```

4. Klik **Send**.

### Response yang diharapkan

```json
{
	"status": "success",
	"total_records": 100,
	"data": [
		{
			"product_id": "A001",
			"product_name": "Mie Gacoan Level 1",
			"price": 10000,
			"stock": 50,
			"category": "Makanan",
			"source_file": "cabang_bogor.csv",
			"processed_at": "2026-05-04T10:00:00Z"
		}
	]
}
```

### Cara cek hasilnya

- `status` harus bernilai `success`.
- `total_records` menunjukkan jumlah data yang dikembalikan.
- `data` berisi array record hasil query.

## 5. Testing endpoint `DELETE /api/data/{product_id}`

Endpoint ini dipakai oleh Admin untuk menghapus data secara permanen dari BigQuery.

### Langkah-langkah

1. Klik **New** > **HTTP Request**.
2. Ubah method menjadi **DELETE**.
3. Isi URL dengan (contoh menghapus ID `TGR-01` atau `null` untuk testing data):

```text
{{base_url}}/api/data/null
```

4. Pastikan Anda sudah login sebagai Admin dan memasukkan Token di tab **Authorization**.
5. Klik **Send**.

### Response yang diharapkan

```json
{
	"status": "success",
	"message": "Data dengan product_id 'null' berhasil dihapus secara permanen."
}
```

### Cara cek hasilnya

- `status` harus bernilai `success`.
- Panggil ulang `GET /api/data` dan pastikan barang tersebut tidak ada lagi di dalam senarai data.

## 6. Checklist testing cepat di Postman

Untuk memastikan semuanya sudah benar, cek poin berikut:

1. Backend sudah jalan di `http://localhost:8000`.
2. Environment Postman sudah punya variable `base_url`.
3. Request `POST /api/upload` menggunakan `form-data`.
4. Key file bernama `file` dan bertipe **File**.
5. Request `GET /api/data` memakai method `GET` tanpa body.
6. Response JSON sesuai dengan format di API contract.

## 6. Troubleshooting

### Jika upload gagal

- Pastikan file yang di-upload adalah CSV.
- Pastikan backend berjalan.
- Pastikan kredensial GCP tersedia jika endpoint benar-benar mengakses GCS/BigQuery.

### Jika response `500`

- Cek log terminal backend.
- Periksa file `Back_end/services/gcp_service.py`.
- Pastikan koneksi ke Google Cloud berhasil.

### Jika response kosong atau format salah

- Pastikan endpoint yang dipanggil adalah `/api/upload` atau `/api/data`.
- Pastikan backend terbaru sudah dijalankan ulang setelah perubahan kode.

## 7. Struktur singkat alur testing

Urutan testing yang paling aman:

1. Jalankan backend.
2. Test `POST /api/upload` pakai file CSV kecil dulu.
3. Lihat response `mapping_result` dan `preview_data`.
4. Test `GET /api/data` untuk cek data yang sudah masuk ke BigQuery.

## 8. Catatan penting

- Dokumentasi ini dibuat untuk testing manual lewat Postman.
- Kalau nanti mau otomatisasi, request yang sama bisa diekspor menjadi Postman Collection lalu dijalankan dengan Newman.

## 9. Cara Melacak Data di Google Cloud (Tracing End-to-End)

Setelah Anda berhasil mengunggah file (`/api/upload`), data tidak langsung muncul di `/api/data` karena ada proses latar belakang di Cloud. Berikut cara melacak perjalanannya:

### A. Cek Google Cloud Storage (Bucket)
1. Buka [Cloud Storage Buckets](https://console.cloud.google.com/storage/browser).
2. Klik bucket penampung (*raw bucket*) Anda.
3. Anda akan melihat file CSV mentah Anda! Jika Anda mengeklik file tersebut dan menggulir ke bagian bawah, Anda akan melihat **Custom Metadata** berisi `{"uploaded_by": "user"}` yang dititipkan oleh Backend.

### B. Cek Google Cloud Functions (ML Engine)
1. Buka [Cloud Run Services](https://console.cloud.google.com/run).
2. Klik layanan Cloud Run / Function mesin ML Anda, lalu buka tab **Logs**.
3. Cari *log* yang waktunya bersamaan dengan saat Anda menekan tombol di Postman. Anda akan melihat proses pembersihan ML berjalan. Ini membuktikan *Eventarc Trigger* bekerja sempurna!

### C. Cek BigQuery (Data Warehouse)
1. Buka [BigQuery SQL Workspace](https://console.cloud.google.com/bigquery).
2. Di panel penjelajah sebelah kiri, cari *Project* Anda, rentangkan dataset `retail_warehouse`, dan klik tabel `integrated_retail_data`.
3. Buka tab **Preview** (Pratinjau) atau jalankan SQL `SELECT * FROM ... LIMIT 10`.
4. Anda akan melihat data yang sudah dirapikan oleh ML. Jangan lupa mengecek kolom `uploaded_by`.
