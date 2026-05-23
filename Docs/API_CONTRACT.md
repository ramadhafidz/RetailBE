# API Contract (Frontend React <-> Backend FastAPI)
**Base URL:** `http://localhost:8000`

Dokumen ini mendefinisikan struktur Request dan Response antara antarmuka React dan FastAPI Backend. Semua respon wajib menggunakan format JSON standar.

## 1. Upload & Process Data
**Endpoint:** `POST /api/upload`
**Description:** Menerima file CSV mentah dari React, memprosesnya dengan modul ML (Schema Matching), melakukan data cleansing, dan mengirimkannya ke pipeline/Storage.

**Request:**
- Content-Type: `multipart/form-data`
- Body Payload: 
  - `file`: (File binary CSV, format bebas)

**Response (200 OK - Success):**
```json
{
  "status": "success",
  "message": "File cabang_cilegon.csv berhasil diproses dan dikirim ke Data Warehouse.",
  "metadata": {
    "total_rows_processed": 150,
    "source_file": "cabang_cilegon.csv"
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
      "category": "Makanan"
    }
  ]
}
```

**Response (400 / 500 - Error):**
```json
{
  "status": "error",
  "message": "Gagal memproses file: Format CSV tidak terbaca atau AI gagal menemukan kolom target."
}
```

## 2. Fetch Dashboard Data
**Endpoint:** `GET /api/data`
**Description:** Mengambil 100 baris data terbaru dari BigQuery untuk ditampilkan di tabel Frontend.

**Request:** (No Body)

**Response (200 OK):**
```
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
       "source_file": "cabang_cilegon.csv",
       "processed_at": "2026-05-04T10:00:00Z"
    }
  ]
}
```