from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Response
from services.gcp_service import (
    upload_file_to_gcs,
    get_data_from_bq,
    upload_dataframe_to_bq,
    delete_data_from_bq,
    get_credentials,
    CREDENTIALS_PATH,
    PROJECT_ID,
    USE_GCP,
)

import os
import sys
import io
import pandas as pd
import numpy as np
from typing import Any, Dict
from logger_config import setup_logger

logger = setup_logger("data_routes")

router = APIRouter()

# Tambahkan path ke folder Machine_Learning (RetailML) agar kita bisa memanggil engine untuk preview
# Coba jalur produksi (Docker)
ML_PATH_DOCKER = "/app/RetailML"
# Coba jalur development (Local)
ML_PATH_LOCAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "RetailML"))

if os.path.exists(ML_PATH_DOCKER):
    ML_PATH = ML_PATH_DOCKER
else:
    ML_PATH = ML_PATH_LOCAL

if ML_PATH not in sys.path:
    sys.path.append(ML_PATH)

from column_mapper_lokal import standardize_dataframe
import engine.column_mapper_core as core

# Import auth utilities (robust import to work when running from repo root or inside Back_end)
try:
    from Back_end.auth import create_access_token, require_role
except Exception:
    try:
        from auth import create_access_token, require_role
    except Exception:
        from .auth import create_access_token, require_role


def _sanitize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in rec.items():
        if pd.isna(v):
            out[k] = None
        elif isinstance(v, (pd.Timestamp,)):
            out[k] = v.isoformat()
        elif isinstance(v, (np.integer,)):
            out[k] = int(v)
        elif isinstance(v, (np.floating,)):
            out[k] = float(v)
        else:
            out[k] = v
    return out


# Endpoint POST untuk menerima file dari Frontend
def _resolve_role_credentials(role: str) -> tuple[str, str]:
    if role == "admin":
        username = os.getenv("AUTH_ADMIN_USERNAME", os.getenv("AUTH_USERNAME", "admin"))
        password = os.getenv("AUTH_ADMIN_PASSWORD", os.getenv("AUTH_PASSWORD", "admin"))
    else:
        username = os.getenv("AUTH_USER_USERNAME", "user")
        password = os.getenv("AUTH_USER_PASSWORD", "user")
    return username, password


@router.post("/api/upload")
async def upload_data(file: UploadFile = File(...), current_user: dict = Depends(require_role("user"))):
    contents = await file.read()

    # 1) Parse CSV (Hanya 5 baris pertama untuk preview)
    try:
        df_raw = pd.read_csv(io.BytesIO(contents), nrows=5)
    except Exception:
        raise HTTPException(status_code=400, detail="Format CSV tidak terbaca")

    # 2) Jalankan mesin ML untuk standarisasi (hanya pada 5 baris)
    df_clean = standardize_dataframe(df_raw, filename=file.filename)

    # 3) Buat mapping result dengan memanfaatkan fungsi map internal
    mapping_result: Dict[str, Any] = {}
    for col in df_raw.columns:
        try:
            mapped = core._map_column(col, df_raw[col])
            mapping_result[col] = mapped
        except Exception:
            mapping_result[col] = None

    # 4) Upload raw file ke GCS beserta metadatanya agar diolah oleh Cloud Function
    try:
        uploader = current_user.get("username", "unknown")
        upload_file_to_gcs(contents, file.filename, metadata={"uploaded_by": uploader})
    except Exception as e:
        logger.error(f"GCS upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal mengirim file ke Cloud Storage: {str(e)}")

    # (Backend tidak lagi mengirim data ke BigQuery. Tugas itu diserahkan 100% ke Cloud Function)

    # 5) Siapkan response sesuai API_CONTRACT
    # Hitung jumlah baris asli berdasarkan karakter newline (dikurangi 1 untuk header)
    total_lines = contents.count(b'\n')
    actual_rows = total_lines - 1 if total_lines > 0 else 0
    
    metadata = {"total_rows_processed": actual_rows, "source_file": file.filename}
    preview_data_raw = df_clean.to_dict(orient="records") # Kembalikan seluruh 5 baris preview
    preview_data = [_sanitize_record(r) for r in preview_data_raw]

    return {
        "status": "success",
        "message": f"File {file.filename} berhasil diproses dan dikirim ke Data Warehouse.",
        "metadata": metadata,
        "mapping_result": mapping_result,
        "preview_data": preview_data,
    }


# Endpoint GET untuk memberikan data ke Frontend
@router.get("/api/data")
async def get_data(current_user: dict = Depends(require_role("admin"))):
    data = get_data_from_bq()
    total = len(data) if isinstance(data, list) else 0
    return {"status": "success", "total_records": total, "data": data}


# Endpoint DELETE untuk menghapus data secara permanen dari BigQuery (Hanya Admin)
@router.delete("/api/data/{product_id}")
async def delete_data(product_id: str, response: Response, current_user: dict = Depends(require_role("admin"))):
    try:
        result = delete_data_from_bq(product_id)
        if result["success"]:
            if result["affected_rows"] == 0:
                response.status_code = 404
                return {
                    "status": "not_found",
                    "message": f"Tidak ada data dengan product_id '{product_id}' yang ditemukan untuk dihapus.",
                    "deleted_count": 0,
                    "deleted_items": []
                }
            
            return {
                "status": "success", 
                "message": f"Berhasil menghapus {result['affected_rows']} baris data dengan product_id '{product_id}' secara permanen.",
                "deleted_count": result["affected_rows"],
                "deleted_items": result["deleted_items"]
            }
        else:
            raise HTTPException(status_code=500, detail="Penghapusan gagal")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghapus data: {str(e)}")


# Endpoint ringan untuk cek kredensial GCP — hanya refresh token, tidak menjalankan query
@router.get("/api/gcp-check")
async def gcp_check(current_user: dict = Depends(require_role("admin"))):
    info = {"credentials_path": CREDENTIALS_PATH, "use_gcp": bool(USE_GCP), "project_id": PROJECT_ID}
    creds = get_credentials()
    if not creds:
        return {"status": "not-configured", "detail": "GCP credentials not available or failed to load", **info}

    try:
        # Refresh token untuk memvalidasi kredensial (ringan, tidak mengeksekusi resource GCP)
        from google.auth.transport.requests import Request as AuthRequest

        creds.refresh(AuthRequest())
        sa_email = getattr(creds, "service_account_email", None)
        return {"status": "success", "detail": "Credentials valid (token refreshed)", "service_account": sa_email, **info}
    except Exception as e:
        return {"status": "error", "detail": str(e), **info}


# Simple login endpoint — gunakan ENV vars `AUTH_USERNAME` dan `AUTH_PASSWORD` untuk dev
@router.post("/api/auth/login")
async def login(req: Request):
    body = await req.json()
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")

    admin_user, admin_pass = _resolve_role_credentials("admin")
    user_user, user_pass = _resolve_role_credentials("user")

    if username == admin_user and password == admin_pass:
        role = "admin"
    elif password == user_pass:
        role = "user"
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=username, role=role)
    return {"access_token": token, "token_type": "bearer", "role": role, "username": username}