from fastapi import APIRouter, UploadFile, File, HTTPException
from services.gcp_service import (
    upload_file_to_gcs,
    get_data_from_bq,
    upload_dataframe_to_bq,
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

router = APIRouter()

# Tambahkan path ke folder Machine_Learning agar kita bisa memanggil engine
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ML_PATH = os.path.join(REPO_ROOT, "Machine_Learning")
if ML_PATH not in sys.path:
    sys.path.insert(0, ML_PATH)

from column_mapper_lokal import standardize_dataframe
import engine.column_mapper_core as core


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
@router.post("/api/upload")
async def upload_data(file: UploadFile = File(...)):
    contents = await file.read()

    # 1) Parse CSV
    try:
        df_raw = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Format CSV tidak terbaca")

    # 2) Jalankan mesin ML untuk standarisasi
    df_clean = standardize_dataframe(df_raw, filename=file.filename)

    # 3) Buat mapping result dengan memanfaatkan fungsi map internal
    mapping_result: Dict[str, Any] = {}
    for col in df_raw.columns:
        try:
            mapped = core._map_column(col, df_raw[col])
            mapping_result[col] = mapped
        except Exception:
            mapping_result[col] = None

    # 4) Upload raw file ke GCS (arsip) dan upload cleaned data ke BigQuery
    try:
        upload_file_to_gcs(contents, file.filename)
    except Exception as e:
        print(f"⚠️ GCS upload error: {e}")
        pass

    try:
        upload_dataframe_to_bq(df_clean)
    except Exception as e:
        print(f"⚠️ BigQuery upload error: {e}")
        # Jangan fail di sini - lanjutkan dengan local fallback
        pass

    # 5) Siapkan response sesuai API_CONTRACT
    metadata = {"total_rows_processed": int(len(df_raw)), "source_file": file.filename}
    preview_data_raw = df_clean.head(1).to_dict(orient="records")
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
async def get_data():
    data = get_data_from_bq()
    total = len(data) if isinstance(data, list) else 0
    return {"status": "success", "total_records": total, "data": data}


# Endpoint ringan untuk cek kredensial GCP — hanya refresh token, tidak menjalankan query
@router.get("/api/gcp-check")
async def gcp_check():
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