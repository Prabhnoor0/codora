FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first to avoid resolver issues
RUN pip install --no-cache-dir --upgrade pip

# Python dependencies
# PyTorch CPU wheel is fetched from the official index; all other packages from PyPI
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --default-timeout=1000 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Copy source
COPY . .

# Expose API port
EXPOSE 8000

# Default command (overridden by docker-compose for worker)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
