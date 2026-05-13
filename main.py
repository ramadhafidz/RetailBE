from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import router secara robust: dukung 3 skenario
# 1) menjalankan dari root: `uvicorn Back_end.main:app`
# 2) menjalankan dari folder Back_end: `uvicorn main:app`
# 3) paket terinstal/struktur lain
try:
    # Prefer import dengan nama paket (jalankan dari root)
    from Back_end.routers import data_routes
except Exception:
    try:
        # Jalankan dari dalam folder Back_end
        from routers import data_routes
    except Exception:
        # Fallback relatif (jika Back_end adalah paket)
        from .routers import data_routes

app = FastAPI(title="Retail Backend API")

# Penting agar Frontend (yang berjalan di port beda) tidak ditolak oleh Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "API berjalan"}


app.include_router(data_routes.router)