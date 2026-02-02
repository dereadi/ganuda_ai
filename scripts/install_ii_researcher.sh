#!/bin/bash
# ii-researcher Installation Script
# Council Vote: 166956a7959c2232
# For Seven Generations - Cherokee AI Federation

set -e

echo "=============================================="
echo "ii-researcher Installation - Phase 1"
echo "=============================================="

# Step 1: Clone repository
echo "[1/5] Cloning ii-researcher..."
cd /ganuda/services
if [ -d "ii-researcher" ]; then
    echo "Directory exists, pulling latest..."
    cd ii-researcher && git pull
else
    git clone https://github.com/Intelligent-Internet/ii-researcher.git
    cd ii-researcher
fi

# Step 2: Create virtual environment and install from pyproject.toml
echo "[2/5] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip

echo "[3/5] Installing ii-researcher from pyproject.toml..."
pip install .

# Step 4: Create environment file
echo "[4/5] Creating .env file..."
cat > /ganuda/services/ii-researcher/.env << 'EOF'
# LLM Configuration - point to our vLLM
OPENAI_API_KEY=not-needed-for-local
OPENAI_BASE_URL=http://localhost:8000/v1

# Search Configuration - Tavily for web search
TAVILY_API_KEY=tvly-dev-placeholder
SEARCH_PROVIDER=tavily
SCRAPER_PROVIDER=default

# Model Configuration - use our local Nemotron
R_MODEL=nvidia/NVIDIA-Nemotron-Nano-9B-v2
R_REPORT_MODEL=nvidia/NVIDIA-Nemotron-Nano-9B-v2
FAST_LLM=nvidia/NVIDIA-Nemotron-Nano-9B-v2

# Timeouts
SEARCH_PROCESS_TIMEOUT=300
SEARCH_QUERY_TIMEOUT=20
SCRAPE_URL_TIMEOUT=30

# Compression settings
USE_LLM_COMPRESSOR=TRUE
COMPRESS_MAX_OUTPUT_WORDS=6500
COMPRESS_MAX_INPUT_WORDS=32000
EOF

# Step 5: Create systemd services
echo "[5/5] Creating systemd services..."

mkdir -p /ganuda/scripts/systemd

# ii-researcher service (connects directly to vLLM)
cat > /ganuda/scripts/systemd/ii-researcher.service << 'EOF'
[Unit]
Description=ii-researcher Deep Search Agent
After=network.target vllm.service
Wants=vllm.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/ii-researcher
Environment=PATH=/ganuda/services/ii-researcher/venv/bin:/usr/bin:/bin
EnvironmentFile=/ganuda/services/ii-researcher/.env
ExecStart=/ganuda/services/ii-researcher/venv/bin/python -m uvicorn api:app --host 0.0.0.0 --port 8090
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ii-researcher

MemoryMax=4G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "=============================================="
echo "Installation complete!"
echo "=============================================="
echo ""
echo "Now run with sudo:"
echo ""
echo "  sudo ln -sf /ganuda/scripts/systemd/ii-researcher.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable ii-researcher"
echo "  sudo systemctl start ii-researcher"
echo ""
echo "Then verify:"
echo "  curl 'http://localhost:8090/search?question=test'"
echo ""
echo "FOR SEVEN GENERATIONS"
