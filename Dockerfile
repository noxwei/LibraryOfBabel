# LibraryOfBabel Standardized Production API
# Containerized deployment for the 93.2% success rate API

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV RUNNING_IN_CONTAINER=true
ENV API_HOST=0.0.0.0
ENV API_PORT=5565

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the standardized API source code
COPY src/api/ ./src/api/
COPY database/ ./database/

# Create logs directory
RUN mkdir -p /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5565/health || exit 1

# Expose the API port
EXPOSE 5565

# Run the standardized production API
CMD ["python", "src/api/standardized_production_api.py"]