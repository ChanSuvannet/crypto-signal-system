# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libmariadb-dev-compat \
    libmariadb-dev \
    libblas-dev \
    liblapack-dev \
    wget \
    curl \
    git \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && make install && \
    cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements
COPY backend/bots/market-data-bot/requirements.txt ./requirements.txt
COPY backend/bots/shared/requirements.txt ./shared/requirements.txt
# Install TA-Lib wheel from unofficial source

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir numpy
RUN pip install --no-cache-dir ta-lib==0.4.24
RUN pip install --no-cache-dir -r shared/requirements.txt

# Copy app code
COPY backend /app/backend

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Expose port if needed
EXPOSE 8000

# Command to run your app (replace as needed)
CMD ["python", "backend/main.py"]
