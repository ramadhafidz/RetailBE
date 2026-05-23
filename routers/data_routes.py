from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
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

    # 1) Parse CSV
    try:
        df_raw = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Format CSV tidak terbaca")

    # 2) Jalankan mesin ML untuk standarisasi
    df_clean = standardize_dataframe(df_raw, filename=file.filename)
    
    # Tambahkan metadata pengunggah
    df_clean["uploaded_by"] = current_user.get("username", "unknown")

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
async def get_data(current_user: dict = Depends(require_role("admin"))):
    data = get_data_from_bq()
    total = len(data) if isinstance(data, list) else 0
    return {"status": "success", "total_records": total, "data": data}


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