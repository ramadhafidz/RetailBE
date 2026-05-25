from google.cloud import storage, bigquery
from google.oauth2 import service_account
import os
import json
import pandas as pd
from typing import List, Dict, Any

from logger_config import setup_logger
logger = setup_logger("gcp_service")

# Cari credential dari env, atau file umum di folder kerja
DEFAULT_CREDENTIAL_FILES = ["credentials.json", "credential.json"]
env_path = os.getenv("GCP_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if env_path:
    CREDENTIALS_PATH = env_path
else:
    # pilih file credential yang ada (prioritas credentials.json lalu credential.json)
    found = next((p for p in DEFAULT_CREDENTIAL_FILES if os.path.exists(p)), None)
    CREDENTIALS_PATH = found or DEFAULT_CREDENTIAL_FILES[0]
PROJECT_ID = "datawarehouse-493606"
USE_GCP = os.path.exists(CREDENTIALS_PATH)
if not USE_GCP:
    # Pastikan USE_GCP False by default jika file/config tidak ada, beri peringatan
    if os.getenv("GCP_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.warning(f"GCP_CREDENTIALS_PATH set but file not found at {CREDENTIALS_PATH}")

def get_credentials():
    """Get GCP credentials jika tersedia, return None otherwise"""
    if not USE_GCP:
        return None
    try:
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        return credentials
    except Exception as e:
        logger.error(f"Tidak bisa load credentials - {e}")
        return None

def upload_file_to_gcs(file_bytes, filename, metadata: dict = None):
    """Upload file ke GCS. Wajib berhasil agar Cloud Function terpanggil."""
    if not USE_GCP:
        error_msg = f"GCP tidak dikonfigurasi (credential tidak ditemukan). Upload {filename} dibatalkan."
        logger.error(error_msg)
        raise Exception(error_msg)
    
    try:
        client = storage.Client(credentials=get_credentials(), project=PROJECT_ID)
        bucket = client.bucket("retail-data-raw-izz")
        blob = bucket.blob(filename)
        if metadata:
            blob.metadata = metadata
        blob.upload_from_string(file_bytes)
        logger.info(f"File {filename} uploaded to GCS")
        return True
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        raise e

def upload_dataframe_to_bq(df: pd.DataFrame):
    """Fallback lokal jika BigQuery tidak disetup"""
    
    if not USE_GCP:
        # Tulis ke file lokal sebagai fallback
        local_path = "processed_data_local.csv"
        df.to_csv(local_path, mode='a', index=False, header=not os.path.exists(local_path))
        logger.info(f"Data saved locally to {local_path} (appended)")
        return
        
    try:
        client = bigquery.Client(credentials=get_credentials(), project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.retail_warehouse.integrated_retail_data"
        
        if get_credentials() is None:
            logger.warning("GCP tidak configured - saving data locally instead")
            local_path = "processed_data_local.csv"
            df.to_csv(local_path, mode='a', index=False, header=not os.path.exists(local_path))
            return
            
        # Konversi tipe data object (string) yang mungkin bermasalah saat upload ke BQ
        df = df.astype(str)
            
        job = client.load_table_from_dataframe(df, table_id)
        job.result()  # Tunggu sampai selesai
        logger.info("Data uploaded to BigQuery")
    except Exception as e:
        logger.error(f"BigQuery upload failed: {e}")
        raise e

def get_data_from_bq(limit=100) -> List[Dict[str, Any]]:
    """Fallback mengambil data dari lokal CSV jika GCP tidak disetup"""
    
    if not USE_GCP or get_credentials() is None:
        logger.warning("GCP tidak configured - trying to read from local file")
        try:
            local_path = "processed_data_local.csv"
            if os.path.exists(local_path):
                df = pd.read_csv(local_path)
                return df.tail(limit).to_dict(orient="records")
            logger.warning("Tidak ada local data file - returning empty list")
            return []
        except Exception:
            return []
            
    try:
        client = bigquery.Client(credentials=get_credentials(), project=PROJECT_ID)
        # Menggunakan _latest view untuk mencegah pengiriman data duplikat ke Frontend
        query = f"SELECT * FROM `{PROJECT_ID}.retail_warehouse.integrated_retail_data_latest` LIMIT {limit}"
        query_job = client.query(query)
        results = query_job.result()
        logger.info("Data fetched from BigQuery")
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Failed to fetch data from BigQuery: {e}", exc_info=True)
        return []