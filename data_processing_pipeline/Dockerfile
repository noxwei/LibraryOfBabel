# BabelProcessorDb Pipeline Test Container
# Lightweight Python environment for EPUB processing and embedding generation

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for EPUB processing
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY database/ ./database/

# Create directories for data and logs
RUN mkdir -p /app/data/epubs /app/data/logs /app/data/output

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DB_NAME=BabelProcessorDb
ENV DB_HOST=host.docker.internal
ENV DB_USER=weixiangzhang
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV PIPELINE_MODE=test
ENV MAX_WORKERS=4
ENV MAX_BOOKS=10
ENV MAX_CHUNKS_PER_BOOK=1000

# Expose port for health checks
EXPOSE 8080

# Default command
CMD ["python", "scripts/run_pipeline_test.py"]