from google.cloud import storage, bigquery
from google.oauth2 import service_account
import os
import json

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
    # Jika env var diberikan tapi file tidak ada, beri peringatan
    if os.getenv("GCP_CREDENTIALS_PATH") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print(f"⚠️ GCP_CREDENTIALS_PATH set but file not found at {CREDENTIALS_PATH}")

def get_credentials():
    """Get GCP credentials jika tersedia, return None otherwise"""
    if not USE_GCP:
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        # Jika credentials service account tidak punya scopes, set default scope
        # agar refresh() bisa memperoleh access token tanpa error "invalid_scope".
        try:
            if getattr(creds, "scopes", None) is None and hasattr(creds, "with_scopes"):
                creds = creds.with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
        except Exception:
            # bila gagal set scopes, tetap kembalikan creds asli
            pass
        return creds
    except Exception as e:
        print(f"⚠️ Warning: Tidak bisa load credentials - {e}")
        return None

def upload_file_to_gcs(file_bytes, filename):
    """Upload file ke GCS (optional, hanya jika credentials ada)"""
    if not USE_GCP:
        print(f"ℹ️ GCP tidak configured - skipping GCS upload untuk {filename}")
        return True
    
    try:
        client = storage.Client(credentials=get_credentials(), project=PROJECT_ID)
        bucket = client.bucket("retail-data-raw-493606")
        blob = bucket.blob(filename)
        blob.upload_from_string(file_bytes)
        print(f"✅ File {filename} uploaded to GCS")
        return True
    except Exception as e:
        print(f"⚠️ GCS upload failed: {e}")
        return False


def _save_local_append(df):
    import os
    import pandas as pd
    local_path = "processed_data_local.csv"
    if os.path.exists(local_path):
        try:
            old_df = pd.read_csv(local_path)
            combined_df = pd.concat([old_df, df], ignore_index=True)
            combined_df.to_csv(local_path, index=False)
        except Exception:
            df.to_csv(local_path, index=False)
    else:
        df.to_csv(local_path, index=False)
    print(f"✅ Data saved locally to {local_path} (appended)")

def upload_dataframe_to_bq(df, table_id: str = None):
    """Upload pandas DataFrame ke BigQuery (optional, hanya jika credentials ada)
    
    Jika GCP tidak configured, simpan locally ke CSV sebagai fallback.
    """
    if not USE_GCP:
        print(f"ℹ️ GCP tidak configured - saving data locally instead")
        _save_local_append(df)
        return True
    
    try:
        client = bigquery.Client(credentials=get_credentials(), project=PROJECT_ID)
        if table_id is None:
            table_id = f"{PROJECT_ID}.retail_warehouse.integrated_retail_data"

        job = client.load_table_from_dataframe(df, table_id)
        job.result()  # tunggu hingga selesai
        print(f"✅ Data uploaded to BigQuery")
        return True
    except Exception as e:
        print(f"⚠️ BigQuery upload failed: {e}")
        # Fallback: save locally
        _save_local_append(df)
        return True

def get_data_from_bq():
    """Get data dari BigQuery atau local file jika GCP tidak available"""
    if not USE_GCP:
        print(f"ℹ️ GCP tidak configured - trying to read from local file")
        local_path = "processed_data_local.csv"
        try:
            import pandas as pd
            df = pd.read_csv(local_path)
            return df.to_dict(orient='records')
        except FileNotFoundError:
            print(f"⚠️ Tidak ada local data file - returning empty list")
            return []
    
    try:
        client = bigquery.Client(credentials=get_credentials(), project=PROJECT_ID)
        query = f"SELECT * FROM `{PROJECT_ID}.retail_warehouse.integrated_retail_data` LIMIT 100"
        # Mengembalikan data dalam bentuk dictionary agar bisa dikirim sebagai JSON
        results = client.query(query).result()
        print(f"✅ Data fetched from BigQuery")
        return [dict(row) for row in results]
    except Exception as e:
        print(f"⚠️ BigQuery query failed: {e}")
        # Fallback: try local file
        local_path = "processed_data_local.csv"
        try:
            import pandas as pd
            df = pd.read_csv(local_path)
            return df.to_dict(orient='records')
        except FileNotFoundError:
            return []