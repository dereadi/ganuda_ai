# Jr Build Instructions: Docker Compose Full Stack
## Priority: CRITICAL - One-Command Startup

---

## Objective

Create a Docker Compose setup that starts the ENTIRE Ganuda stack with a single command:

```bash
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda
cp .env.example .env  # Edit with your settings
docker-compose up -d
```

**Target**: Installation < 5 minutes, first API call < 10 minutes.

---

## What Gets Deployed

| Service | Port | Purpose |
|---------|------|---------|
| **gateway** | 8080 | LLM Gateway API (OpenAI-compatible) |
| **sag** | 4000 | Control Room UI (authenticated) |
| **postgres** | 5432 | Database (audit, memory, users) |
| **redis** | 6379 | Cache (sessions, messages) |
| **public-site** | 80/443 | Public website (optional) |
| **vllm** | 8000 | Local GPU inference (optional) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     docker-compose.yml                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  gateway    │  │    sag      │  │      postgres           │  │
│  │  :8080      │  │   :4000     │  │       :5432             │  │
│  │             │  │             │  │                         │  │
│  │ LLM API     │  │ Control UI  │  │ Audit, Memory, Users    │  │
│  │ + Council   │  │ + Auth      │  │                         │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
│                          │                                       │
│  ┌─────────────┐  ┌──────┴──────┐  ┌─────────────────────────┐  │
│  │   redis     │  │   vllm      │  │     public-site         │  │
│  │   :6379     │  │  :8000      │  │       :80/443           │  │
│  │             │  │  [optional] │  │      [optional]         │  │
│  │ Sessions    │  │ GPU Infer   │  │  ganuda.us              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Tasks

### Task 1: Create Dockerfile for Gateway

Location: `/ganuda/docker/Dockerfile.gateway`

```dockerfile
# Ganuda Gateway
# Lightweight OpenAI-compatible API gateway

FROM python:3.11-slim

LABEL maintainer="Cherokee AI Federation"
LABEL version="1.0"
LABEL description="Ganuda Gateway - Private AI Inference"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash ganuda

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ganuda/ ./ganuda/
COPY config/ ./config/

# Set ownership
RUN chown -R ganuda:ganuda /app

# Switch to non-root user
USER ganuda

# Environment
ENV GANUDA_CONFIG=/etc/ganuda/ganuda.yaml
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run gateway
CMD ["python", "-m", "ganuda.services.llm_gateway.gateway"]
```

### Task 2: Create Dockerfile for vLLM (Optional)

Location: `/ganuda/docker/Dockerfile.vllm`

```dockerfile
# Ganuda vLLM Inference Server
# GPU-accelerated local inference

FROM vllm/vllm-openai:latest

LABEL maintainer="Cherokee AI Federation"
LABEL description="Ganuda Inference - vLLM Backend"

# Environment
ENV MODEL_NAME=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Default command (can be overridden)
CMD ["--model", "${MODEL_NAME}", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 3: Create Docker Compose File

Location: `/ganuda/docker-compose.yml`

```yaml
# ============================================================
# GANUDA AI FEDERATION - Docker Compose
# One-command startup: docker-compose up -d
# ============================================================
version: '3.8'

services:
  # ============================================================
  # CORE SERVICES (Required)
  # ============================================================

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: ganuda-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-ganuda}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?Database password required}
      POSTGRES_DB: ${DB_NAME:-ganuda}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-ganuda}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ganuda-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: ganuda-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ganuda-network

  # LLM Gateway API
  gateway:
    build:
      context: .
      dockerfile: docker/gateway/Dockerfile
    container_name: ganuda-gateway
    restart: unless-stopped
    environment:
      - GANUDA_CONFIG=/app/config/ganuda.yaml
      - DB_PASSWORD=${DB_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ganuda-network

  # SAG Unified Interface (Control Room)
  sag:
    build:
      context: .
      dockerfile: docker/sag/Dockerfile
    container_name: ganuda-sag
    restart: unless-stopped
    environment:
      - GANUDA_CONFIG=/app/config/ganuda.yaml
      - DB_PASSWORD=${DB_PASSWORD}
      - SAG_SECRET_KEY=${SAG_SECRET_KEY:?SAG secret key required}
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    ports:
      - "4000:4000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      gateway:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ganuda-network

  # ============================================================
  # OPTIONAL SERVICES (Uncomment to enable)
  # ============================================================

  # vLLM Local Inference (requires NVIDIA GPU)
  # vllm:
  #   image: vllm/vllm-openai:latest
  #   container_name: ganuda-vllm
  #   restart: unless-stopped
  #   runtime: nvidia
  #   environment:
  #     - NVIDIA_VISIBLE_DEVICES=all
  #   command: >
  #     --model ${VLLM_MODEL:-microsoft/Phi-3-mini-4k-instruct}
  #     --host 0.0.0.0
  #     --port 8000
  #     --max-model-len 4096
  #   ports:
  #     - "8000:8000"
  #   volumes:
  #     - model_cache:/root/.cache/huggingface
  #   deploy:
  #     resources:
  #       reservations:
  #         devices:
  #           - driver: nvidia
  #             count: 1
  #             capabilities: [gpu]
  #   networks:
  #     - ganuda-network

  # Public Site (ganuda.us) - Marketing/Status page
  # public-site:
  #   build:
  #     context: .
  #     dockerfile: docker/public-site/Dockerfile
  #   container_name: ganuda-public
  #   restart: unless-stopped
  #   environment:
  #     - GATEWAY_URL=http://gateway:8080
  #   ports:
  #     - "80:80"
  #     - "443:443"
  #   volumes:
  #     - ./ssl:/etc/ssl/ganuda:ro
  #   depends_on:
  #     - gateway
  #   networks:
  #     - ganuda-network

  # Grafana Monitoring Dashboard
  # grafana:
  #   image: grafana/grafana:latest
  #   container_name: ganuda-grafana
  #   restart: unless-stopped
  #   environment:
  #     - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
  #   volumes:
  #     - grafana_data:/var/lib/grafana
  #     - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards
  #   ports:
  #     - "3000:3000"
  #   networks:
  #     - ganuda-network

# ============================================================
# NETWORKS & VOLUMES
# ============================================================

networks:
  ganuda-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  model_cache:
  grafana_data:
```

### Task 4: Create SAG Dockerfile

Location: `/ganuda/docker/sag/Dockerfile`

```dockerfile
# Ganuda SAG (Control Room) Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY sag/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY sag/ ./sag/
COPY lib/ ./lib/

# Create logs directory
RUN mkdir -p /app/logs

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/lib

# Expose port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:4000/health || exit 1

# Run SAG
CMD ["python", "sag/app.py"]
```

### Task 5: Create Database Init Script

Location: `/ganuda/docker/postgres/init.sql`

```sql
-- ============================================================
-- GANUDA DATABASE INITIALIZATION
-- Creates all tables for Gateway + SAG
-- ============================================================

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(64) UNIQUE NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    user_id VARCHAR(100),
    name VARCHAR(200),
    quota_total INTEGER DEFAULT 1000000,
    quota_used INTEGER DEFAULT 0,
    rate_limit INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_api_keys_key_id ON api_keys(key_id);

-- Audit Log
CREATE TABLE IF NOT EXISTS api_audit_log (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64) UNIQUE,
    key_id VARCHAR(64),
    endpoint VARCHAR(200),
    method VARCHAR(10),
    status_code INTEGER,
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER,
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_body JSONB,
    response_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_created ON api_audit_log(created_at);
CREATE INDEX idx_audit_key ON api_audit_log(key_id);

-- Thermal Memory
CREATE TABLE IF NOT EXISTS thermal_memory_archive (
    id SERIAL PRIMARY KEY,
    memory_hash VARCHAR(64) UNIQUE NOT NULL,
    original_content TEXT NOT NULL,
    compressed_content TEXT,
    current_stage VARCHAR(20) DEFAULT 'FRESH',
    temperature_score FLOAT DEFAULT 100.0,
    access_count INTEGER DEFAULT 0,
    last_access TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    size_bytes INTEGER,
    compression_ratio FLOAT DEFAULT 1.0,
    sacred_pattern BOOLEAN DEFAULT false,
    metadata JSONB
);

CREATE INDEX idx_thermal_hash ON thermal_memory_archive(memory_hash);
CREATE INDEX idx_thermal_stage ON thermal_memory_archive(current_stage);

-- Council Votes
CREATE TABLE IF NOT EXISTS council_votes (
    id SERIAL PRIMARY KEY,
    vote_id VARCHAR(64) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    context TEXT,
    specialist_votes JSONB,
    synthesis TEXT,
    confidence FLOAT,
    concerns JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_council_vote_id ON council_votes(vote_id);

-- Breadcrumb Trails
CREATE TABLE IF NOT EXISTS breadcrumb_trails (
    id SERIAL PRIMARY KEY,
    trail_id VARCHAR(64) NOT NULL,
    step_number INTEGER NOT NULL,
    action VARCHAR(100),
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    UNIQUE(trail_id, step_number)
);

CREATE INDEX idx_breadcrumb_trail ON breadcrumb_trails(trail_id);

-- SAG Users
CREATE TABLE IF NOT EXISTS sag_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'operator',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sag_users_username ON sag_users(username);

-- SAG Sessions
CREATE TABLE IF NOT EXISTS sag_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES sag_users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX idx_sag_sessions_id ON sag_sessions(session_id);
CREATE INDEX idx_sag_sessions_expires ON sag_sessions(expires_at);

-- ============================================================
-- DEFAULT DATA
-- ============================================================

-- Default admin API key (CHANGE IN PRODUCTION)
INSERT INTO api_keys (key_id, key_hash, user_id, name, quota_total)
VALUES (
    'gnd-admin',
    encode(sha256('gnd-admin-CHANGE-THIS-KEY'::bytea), 'hex'),
    'admin',
    'Default Admin Key',
    10000000
) ON CONFLICT (key_id) DO NOTHING;

-- Default SAG admin (password: changeme - CHANGE IMMEDIATELY)
-- Hash generated with: werkzeug.security.generate_password_hash('changeme')
INSERT INTO sag_users (username, password_hash, display_name, role)
VALUES (
    'admin',
    'pbkdf2:sha256:600000$salt$hash',
    'Administrator',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ganuda;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ganuda;
```

### Task 5: Create Example Config

Location: `/ganuda/ganuda.yaml.example`

```yaml
# Ganuda Gateway Configuration
# Copy this file to ganuda.yaml and customize

gateway:
  host: 0.0.0.0
  port: 8080
  api_key_required: true

inference:
  # Option 1: Local vLLM (uncomment vllm service in docker-compose.yml)
  # backend: vllm
  # base_url: http://vllm:8000

  # Option 2: External OpenAI-compatible API
  backend: openai
  base_url: https://api.openai.com/v1
  api_key: ${OPENAI_API_KEY}  # Set via environment
  model: gpt-4o-mini

database:
  host: postgres  # Docker service name
  port: 5432
  database: ganuda
  user: ganuda
  password: ${GANUDA_DB_PASSWORD:-changeme}

logging:
  level: INFO
  audit_enabled: true

# Intelligence modules (all disabled by default)
modules:
  council_enabled: false
  memory_enabled: false
  fse_enabled: false
```

### Task 6: Create .env.example

Location: `/ganuda/.env.example`

```bash
# ============================================================
# GANUDA ENVIRONMENT CONFIGURATION
# Copy to .env and fill in your values
# ============================================================

# ------------------------------------------------------------
# REQUIRED SETTINGS
# ------------------------------------------------------------

# Database password (REQUIRED)
DB_PASSWORD=your_secure_database_password_here

# SAG secret key for session encryption (REQUIRED)
# Generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
SAG_SECRET_KEY=your_secret_key_here

# ------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------

DB_USER=ganuda
DB_NAME=ganuda

# ------------------------------------------------------------
# INFERENCE BACKEND (Choose ONE)
# ------------------------------------------------------------

# Option 1: OpenAI API (easiest)
OPENAI_API_KEY=sk-your-openai-key-here

# Option 2: Anthropic API
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# Option 3: Local vLLM (requires GPU)
# Uncomment vllm service in docker-compose.yml
# VLLM_MODEL=microsoft/Phi-3-mini-4k-instruct

# ------------------------------------------------------------
# OPTIONAL INTEGRATIONS
# ------------------------------------------------------------

# Telegram bot
# TELEGRAM_BOT_TOKEN=your-bot-token

# iCloud Calendar
# ICLOUD_APPLE_ID=your@icloud.com
# ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Slack
# SLACK_BOT_TOKEN=xoxb-your-token
# SLACK_SIGNING_SECRET=your-signing-secret

# ------------------------------------------------------------
# MONITORING
# ------------------------------------------------------------

GRAFANA_PASSWORD=admin
LOG_LEVEL=INFO
```

### Task 7: Create Quickstart Script

Location: `/ganuda/scripts/quickstart.sh`

```bash
#!/bin/bash
# Ganuda Quickstart Script
# Usage: ./scripts/quickstart.sh

set -e

echo "🏔️  Ganuda Gateway Quickstart"
echo "=============================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Create config if not exists
if [ ! -f "ganuda.yaml" ]; then
    echo "📄 Creating ganuda.yaml from example..."
    cp ganuda.yaml.example ganuda.yaml
    echo "   Edit ganuda.yaml to configure your settings."
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "📄 Creating .env from example..."
    cp .env.example .env

    # Generate random password
    RANDOM_PASS=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
    sed -i "s/your-secure-password-here/$RANDOM_PASS/" .env
    echo "   Generated random database password in .env"
fi

echo ""
echo "🚀 Starting Ganuda Gateway..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
if curl -s http://localhost:8080/health | grep -q '"status":"ok"'; then
    echo ""
    echo "✅ Ganuda Gateway is running!"
    echo ""
    echo "   API Endpoint: http://localhost:8080"
    echo "   Health Check: http://localhost:8080/health"
    echo ""
    echo "   Example API call:"
    echo '   curl http://localhost:8080/v1/chat/completions \'
    echo '     -H "Content-Type: application/json" \'
    echo '     -H "Authorization: Bearer gnd-admin-CHANGE-THIS-KEY" \'
    echo '     -d '"'"'{"model": "default", "messages": [{"role": "user", "content": "Hello!"}]}'"'"
    echo ""
else
    echo "⚠️  Gateway may still be starting. Check with:"
    echo "   docker-compose logs -f gateway"
fi
```

### Task 8: Create Makefile

Location: `/ganuda/Makefile`

```makefile
# Ganuda Makefile - Convenient commands

.PHONY: help install start stop restart logs status clean test

help:
	@echo "Ganuda AI Federation"
	@echo ""
	@echo "  make install  - First-time setup"
	@echo "  make start    - Start all services"
	@echo "  make stop     - Stop all services"
	@echo "  make restart  - Restart services"
	@echo "  make logs     - View logs"
	@echo "  make status   - Check health"
	@echo "  make clean    - Remove containers/volumes"
	@echo ""

install:
	@./scripts/install.sh

start:
	docker-compose up -d
	@echo "Gateway: http://localhost:8080"
	@echo "SAG UI:  http://localhost:4000"

stop:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

status:
	@./scripts/verify.sh

clean:
	docker-compose down -v
```

### Task 9: Create Install Script

Location: `/ganuda/scripts/install.sh`

```bash
#!/bin/bash
set -e

echo "=================================="
echo "  Ganuda AI Federation Installer  "
echo "=================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not installed"
    exit 1
fi
echo "✓ Docker installed"

# Create .env
if [ ! -f .env ]; then
    cp .env.example .env

    # Generate secrets
    SAG_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    DB_PASS=$(python3 -c "import secrets; print(secrets.token_hex(16))" 2>/dev/null || openssl rand -hex 16)

    sed -i.bak "s/SAG_SECRET_KEY=.*/SAG_SECRET_KEY=$SAG_SECRET/" .env
    sed -i.bak "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASS/" .env
    rm -f .env.bak

    echo "✓ Generated .env with secure defaults"
fi

# Create directories
mkdir -p logs config

# Build
echo "Building images..."
docker-compose build

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env to add OPENAI_API_KEY"
echo "  2. Run: make start"
echo "  3. Visit: http://localhost:4000"
```

### Task 10: Create Verify Script

Location: `/ganuda/scripts/verify.sh`

```bash
#!/bin/bash
echo "Verifying Ganuda installation..."

# Check containers
for c in ganuda-postgres ganuda-redis ganuda-gateway ganuda-sag; do
    if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
        echo "✓ $c running"
    else
        echo "✗ $c NOT running"
    fi
done

# Check endpoints
curl -sf http://localhost:8080/health > /dev/null && echo "✓ Gateway healthy" || echo "✗ Gateway unhealthy"
curl -sf http://localhost:4000/health > /dev/null && echo "✓ SAG healthy" || echo "✗ SAG unhealthy"

echo ""
echo "Access points:"
echo "  Gateway API: http://localhost:8080"
echo "  SAG UI:      http://localhost:4000 (admin/changeme)"
```

---

## File Structure

```
/ganuda/
├── docker-compose.yml
├── .env.example
├── .env                          # Created by install.sh
├── Makefile
├── config/
│   └── ganuda.yaml
├── docker/
│   ├── gateway/
│   │   └── Dockerfile
│   ├── sag/
│   │   └── Dockerfile
│   ├── postgres/
│   │   └── init.sql
│   └── public-site/
│       └── Dockerfile
├── scripts/
│   ├── install.sh
│   └── verify.sh
├── services/
│   └── llm_gateway/
│       └── gateway.py
├── sag/
│   └── app.py
├── lib/
│   └── config_schema.py
└── logs/
```

---

## Quick Start (User Experience)

```bash
# Clone
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda

# Install
make install

# Edit .env with your OpenAI key
nano .env

# Start
make start

# Verify
make status

# First API call
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer gnd-admin-CHANGE-THIS-KEY" \
  -d '{"model": "default", "messages": [{"role": "user", "content": "Hello!"}]}'

# Access SAG Control Room
open http://localhost:4000
# Login: admin / changeme
```

---

## Testing Checklist

- [ ] `docker-compose up -d` starts all 4 core services
- [ ] PostgreSQL healthy within 30 seconds
- [ ] Redis healthy within 10 seconds
- [ ] Gateway healthy within 60 seconds
- [ ] SAG healthy within 60 seconds
- [ ] `/v1/chat/completions` returns response
- [ ] SAG login works (admin/changeme)
- [ ] Logs persist in `./logs/`
- [ ] Database persists across restarts
- [ ] Works on Linux, macOS, Windows (WSL)

---

## Success Criteria

1. ✅ Installation completes in < 5 minutes
2. ✅ First API call within 10 minutes
3. ✅ Single `docker-compose up -d` starts everything
4. ✅ `.env` contains all configurable settings
5. ✅ `config/ganuda.yaml` controls application behavior
6. ✅ Makefile provides convenient commands
7. ✅ Verification script confirms health
8. ✅ Works without GPU (OpenAI backend)

---

*For Seven Generations*
