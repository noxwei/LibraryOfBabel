# AI Agent Communication Gateway
# Dr. Marcus Thompson - DevOps Monitoring & Observability Specialist
# LibraryOfBabel Agentic AI-Ready Monitoring Architecture

FROM python:3.13-slim

LABEL maintainer="Dr. Marcus Thompson <devops@libraryofbabel.com>"
LABEL description="AI Agent Communication Gateway for LibraryOfBabel Monitoring"
LABEL version="1.0.0"
LABEL ai-ready="true"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 gateway && chown -R gateway:gateway /app
USER gateway

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the gateway
CMD ["python", "agent_gateway.py"]