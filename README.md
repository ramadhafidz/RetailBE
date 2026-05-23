# ⚙️ Retail Dashboard - Backend API

This is the backend service for the Retail Dashboard. Built with FastAPI, it acts as the central bridge between the Frontend interface, Google Cloud Storage (for raw files), and BigQuery (for standardized data).

## 🚀 Tech Stack
- **Framework**: FastAPI (Python 3.10)
- **Deployment**: Docker & Docker Compose
- **Hosting**: On-premise Debian Home Server (exposed via Cloudflare Tunnels)
- **Cloud Integrations**: Google Cloud Storage & BigQuery

## ⚙️ Local Development

### Running via Docker (Recommended)
1. Copy `.env.example` to `.env` and fill in the required variables (like `ALLOWED_ORIGINS` and GCP Credentials path).
2. Start the container:
   ```bash
   docker-compose up -d --build
   ```
3. The API will be available at `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.

### Running Natively
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the uvicorn server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## ☁️ Architecture Flow
1. Receives file upload requests from the Frontend (`RetailFE`).
2. Validates and uploads the raw file to a GCS Bucket (`retail-data-raw-izz`).
3. This GCS upload event asynchronously triggers the ML Engine (`RetailML`) deployed on Google Cloud Functions to clean the data.
4. Provides endpoints for the Frontend to fetch processed data and statistics directly from BigQuery.
