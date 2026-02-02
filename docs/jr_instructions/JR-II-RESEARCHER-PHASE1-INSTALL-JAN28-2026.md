# JR Instruction: ii-researcher Phase 1 - Core Installation

**JR ID:** JR-II-RESEARCHER-PHASE1-INSTALL-JAN28-2026
**Priority:** P1
**Assigned To:** Infrastructure Jr.
**Council Vote:** 166956a7959c2232
**Ultrathink:** ULTRATHINK-II-RESEARCHER-INTEGRATION-JAN28-2026.md

---

## Objective

Install ii-researcher as a systemd service on redfin, configured to use our vLLM via LiteLLM proxy.

---

## Steps

### 1. Clone Repository

```bash
cd /ganuda/services
git clone https://github.com/Intelligent-Internet/ii-researcher.git
cd ii-researcher
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Create Environment File

Create `/ganuda/services/ii-researcher/.env`:

```bash
# LLM Configuration - use LiteLLM proxy
OPENAI_API_BASE=http://localhost:8081/v1
OPENAI_API_KEY=local-not-needed

# Search Configuration
TAVILY_API_KEY=tvly-dev-placeholder
SEARCH_PROVIDER=tavily

# Model Configuration
DEFAULT_MODEL=nemotron-9b
REASONING_MODEL=nemotron-9b

# Limits
MAX_SOURCES=10
MAX_SEARCH_RESULTS=20
```

### 4. Create Systemd Service

Create `/ganuda/scripts/systemd/ii-researcher.service`:

```ini
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
ExecStart=/ganuda/services/ii-researcher/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8090
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ii-researcher

MemoryMax=2G
CPUQuota=100%

[Install]
WantedBy=multi-user.target
```

### 5. Install LiteLLM Proxy

```bash
pip install litellm[proxy]
```

Create `/ganuda/config/litellm_config.yaml`:

```yaml
model_list:
  - model_name: nemotron-9b
    litellm_params:
      model: openai/nvidia/NVIDIA-Nemotron-Nano-9B-v2
      api_base: http://localhost:8000/v1
      api_key: not-needed

  - model_name: gpt-4o
    litellm_params:
      model: openai/nvidia/NVIDIA-Nemotron-Nano-9B-v2
      api_base: http://localhost:8000/v1
      api_key: not-needed
```

Create `/ganuda/scripts/systemd/litellm-proxy.service`:

```ini
[Unit]
Description=LiteLLM Proxy for ii-researcher
After=network.target vllm.service
Wants=vllm.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services
ExecStart=/home/dereadi/cherokee_venv/bin/litellm --config /ganuda/config/litellm_config.yaml --port 8081
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=litellm-proxy

[Install]
WantedBy=multi-user.target
```

### 6. Enable Services

```bash
sudo ln -sf /ganuda/scripts/systemd/litellm-proxy.service /etc/systemd/system/
sudo ln -sf /ganuda/scripts/systemd/ii-researcher.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable litellm-proxy ii-researcher
sudo systemctl start litellm-proxy
# Wait for LiteLLM to start
sleep 5
sudo systemctl start ii-researcher
```

---

## Verification

```bash
# Check services
systemctl status litellm-proxy ii-researcher

# Test LiteLLM proxy
curl http://localhost:8081/v1/models

# Test ii-researcher health
curl http://localhost:8090/health

# Test basic search (once Tavily key is set)
curl -X POST http://localhost:8090/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test search", "max_results": 3}'
```

---

## Notes

- Tavily API key needs to be obtained from https://tavily.com (free tier available)
- LiteLLM proxy translates OpenAI API calls to our vLLM format
- ii-researcher will work without Tavily for local document research

---

FOR SEVEN GENERATIONS
