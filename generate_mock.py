import pandas as pd
from datetime import datetime

# Generate mock data for different users
data = [
    # User: budi_jakarta (Cabang Jakarta)
    {"product_id": "JKT-001", "product_name": "Kopi Susu Gula Aren", "price": 18000, "stock": 50, "category": "Minuman", "source_file": "stok_jkt_mei.csv", "uploaded_by": "budi_jakarta", "processed_at": datetime.utcnow().isoformat()},
    {"product_id": "JKT-002", "product_name": "Roti Bakar Coklat", "price": 15000, "stock": 30, "category": "Makanan", "source_file": "stok_jkt_mei.csv", "uploaded_by": "budi_jakarta", "processed_at": datetime.utcnow().isoformat()},
    {"product_id": "JKT-003", "product_name": "Air Mineral 600ml", "price": 5000, "stock": 120, "category": "Minuman", "source_file": "stok_jkt_mei.csv", "uploaded_by": "budi_jakarta", "processed_at": datetime.utcnow().isoformat()},
    
    # User: sari_bandung (Cabang Bandung)
    {"product_id": "BDG-101", "product_name": "Keripik Kentang Original", "price": 12000, "stock": 85, "category": "Snack", "source_file": "inventori_bdg_2026.csv", "uploaded_by": "sari_bandung", "processed_at": datetime.utcnow().isoformat()},
    {"product_id": "BDG-102", "product_name": "Mie Instan Goreng", "price": 3500, "stock": 250, "category": "Makanan", "source_file": "inventori_bdg_2026.csv", "uploaded_by": "sari_bandung", "processed_at": datetime.utcnow().isoformat()},
    
    # User: andi_surabaya (Cabang Surabaya)
    {"product_id": "SBY-501", "product_name": "Teh Pucuk Harum", "price": 6000, "stock": 90, "category": "Minuman", "source_file": "data_barang_sby.csv", "uploaded_by": "andi_surabaya", "processed_at": datetime.utcnow().isoformat()},
    {"product_id": "SBY-502", "product_name": "Sabun Mandi Cair", "price": 25000, "stock": 40, "category": "Kebutuhan Harian", "source_file": "data_barang_sby.csv", "uploaded_by": "andi_surabaya", "processed_at": datetime.utcnow().isoformat()},
    {"product_id": "SBY-503", "product_name": "Pasta Gigi", "price": 14000, "stock": 60, "category": "Kebutuhan Harian", "source_file": "data_barang_sby.csv", "uploaded_by": "andi_surabaya", "processed_at": datetime.utcnow().isoformat()}
]

df = pd.DataFrame(data)
df.to_csv("c:/Kuliah/Semester 6/Data Warehousing/Retail/Back_end/processed_data_local.csv", index=False)
print("Berhasil men-generate processed_data_local.csv dengan data dummy dari berbagai user!")
