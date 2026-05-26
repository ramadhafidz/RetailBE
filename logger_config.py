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

    class ColorFormatter(logging.Formatter):
        """Formatter kustom untuk menambahkan warna ANSI di Terminal"""
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BOLD_RED = "\033[1;31m"
        CYAN = "\033[96m"
        RESET = "\033[0m"

        def format(self, record):
            level_color = self.RESET
            if record.levelno == logging.DEBUG:
                level_color = self.CYAN
            elif record.levelno == logging.INFO:
                level_color = self.GREEN
            elif record.levelno == logging.WARNING:
                level_color = self.YELLOW
            elif record.levelno == logging.ERROR:
                level_color = self.RED
            elif record.levelno == logging.CRITICAL:
                level_color = self.BOLD_RED

            # Format: [WAKTU] | [LEVEL] berwarna | [MODUL] biru | [PESAN]
            format_str = f"{self.CYAN}%(asctime)s{self.RESET} | {level_color}%(levelname)-8s{self.RESET} | {self.BLUE}%(name)-15s{self.RESET} | %(message)s"
            formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
            return formatter.format(record)

    # Format polos untuk File
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler 1: Terminal (Console) dengan Warna
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter())
    logger.addHandler(console_handler)

    # Handler 2: File (Rotasi) tanpa Warna
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(file_formatter)
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
