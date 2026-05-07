from google.cloud import storage, bigquery
from google.oauth2 import service_account
import os

CREDENTIALS_PATH = "credentials.json"
PROJECT_ID = "datawarehouse-493606"

def get_credentials():
    return service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)

def upload_file_to_gcs(file_bytes, filename):
    client = storage.Client(credentials=get_credentials(), project=PROJECT_ID)
    bucket = client.bucket("retail-data-raw-493606")
    blob = bucket.blob(filename)
    blob.upload_from_string(file_bytes)
    return True


def upload_dataframe_to_bq(df, table_id: str = None):
    """Upload pandas DataFrame ke table BigQuery.

    Jika `table_id` tidak diberikan, gunakan default dataset.table di config.
    Fungsi ini mengasumsikan `df` sudah memiliki kolom metadata seperti
    `source_file` dan `processed_at` agar query di frontend dapat menampilkannya.
    """
    client = bigquery.Client(credentials=get_credentials(), project=PROJECT_ID)
    if table_id is None:
        table_id = f"{PROJECT_ID}.retail_warehouse.integrated_retail_data"

    job = client.load_table_from_dataframe(df, table_id)
    job.result()  # tunggu hingga selesai
    return True

def get_data_from_bq():
    client = bigquery.Client(credentials=get_credentials(), project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.retail_warehouse.integrated_retail_data` LIMIT 100"
    # Mengembalikan data dalam bentuk dictionary agar bisa dikirim sebagai JSON
    results = client.query(query).result()
    return [dict(row) for row in results]