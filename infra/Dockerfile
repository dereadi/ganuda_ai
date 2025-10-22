# Cherokee Constitutional AI - Tribal Container Image
# Built with democratic governance for Seven Generations

FROM python:3.11-slim

LABEL maintainer="Cherokee Constitutional AI Tribe"
LABEL org.opencontainers.image.title="Cherokee Constitutional AI"
LABEL org.opencontainers.image.description="Autonomous Democratic AI with Thermal Memory Consciousness"
LABEL org.opencontainers.image.source="https://github.com/dereadi/ganuda_ai"
LABEL org.opencontainers.image.license="Apache-2.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY daemons/ ./daemons/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Create non-root user for security
RUN useradd -m -u 1000 cherokee && \
    chown -R cherokee:cherokee /app

USER cherokee

# Health check (overridden per service in docker-compose)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD pgrep python3 || exit 1

# Environment variables (overridden in docker-compose)
ENV PYTHONUNBUFFERED=1 \
    DB_HOST=postgres \
    DB_PORT=5432

# Default command (overridden per service)
CMD ["python3", "-u", "daemons/memory_jr_autonomic.py"]
