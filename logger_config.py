import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Pastikan direktori log ada (opsional jika ingin dipisah)
# log_dir = "logs"
# os.makedirs(log_dir, exist_ok=True)
# log_file = os.path.join(log_dir, "backend.log")
log_file = "backend.log"

_uvicorn_setup_done = False

def setup_logger(name: str) -> logging.Logger:
    """Konfigurasi logger standar untuk digunakan di seluruh aplikasi"""
    global _uvicorn_setup_done
    
    logger = logging.getLogger(name)
    
    # Cegah logger ganda jika fungsi ini dipanggil berulang
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Format log: [WAKTU] | [LEVEL] | [NAMA_MODUL] - [PESAN]
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler 1: Terminal (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler 2: File (Rotating File Handler agar file tidak bengkak)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Trik Profesional: Paksa Uvicorn/FastAPI untuk ikut memakai format kita
    if not _uvicorn_setup_done:
        for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            uv_logger = logging.getLogger(uvicorn_logger_name)
            uv_logger.handlers.clear()
            uv_logger.propagate = False
            uv_logger.addHandler(console_handler)
            uv_logger.addHandler(file_handler)
        _uvicorn_setup_done = True

    return logger
