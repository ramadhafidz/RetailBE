FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN git clone https://github.com/ramadhafidz/RetailML.git /app/RetailML

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
