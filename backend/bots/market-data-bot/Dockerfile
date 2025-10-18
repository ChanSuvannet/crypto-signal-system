# ===========================
# Market Data Bot Dockerfile
# ===========================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy shared libraries (common Python package)
COPY backend/shared_libs/python /app/backend/shared_libs/python

# Copy shared bot utilities
COPY backend/bots/shared /app/backend/bots/shared

# Copy this bot’s source code
COPY backend/bots/market-data-bot /app/backend/bots/market-data-bot

# Install shared dependencies first (layer caching)
RUN pip install --no-cache-dir -r /app/backend/bots/shared/requirements.txt

# Install shared library dependencies (editable install)
RUN pip install --no-cache-dir -e /app/backend/shared_libs/python

# Install bot-specific dependencies
RUN pip install --no-cache-dir -r /app/backend/bots/market-data-bot/requirements.txt

# Set Python import paths so absolute imports like 'from backend.bots.shared...' work
ENV PYTHONPATH=/app

# Ensure Python prints logs immediately
ENV PYTHONUNBUFFERED=1

# Optional: healthcheck to verify container is running
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "print('market-data-bot alive')" || exit 1

# Command to run bot
CMD ["python", "backend/bots/market-data-bot/src/main.py"]
