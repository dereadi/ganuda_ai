# Jr Instruction: Deploy Exo Distributed Inference Across Mac Cluster

**Task ID:** EXO-CLUSTER-001
**Priority:** P2
**Date:** February 7, 2026
**Nodes:** sasass (.241), sasass2 (.242), tpm-macbook (.21)
**Assigned:** Infrastructure Jr.
**Council Vote:** Recommended (architecture addition)

## Overview

Deploy Exo to pool the unified memory across the three Apple Silicon Mac nodes for distributed large model inference. This enables running 70B+ parameter models that won't fit on any single node.

## Hardware Inventory

| Node | Chip | Unified Memory | Thunderbolt | IP |
|------|------|---------------|-------------|-----|
| tpm-macbook | M4 Max | 128 GB | TB5 (120 Gb/s, RDMA capable) | 192.168.132.21 |
| sasass | M1 Max | 64 GB | TB4 (40 Gb/s) | 192.168.132.241 |
| sasass2 | M1 Max | 64 GB | TB4 (40 Gb/s) | 192.168.132.242 |
| **Total** | | **256 GB** | | |

**Model capacity at 256GB:**
- Llama 3.1 70B FP16 (~140GB) — fits with room for KV cache
- Llama 3.1 405B Q4 (~200GB) — fits
- Qwen2.5 72B FP16 (~144GB) — fits
- DeepSeek-V3 671B Q2 (~250GB) — tight but possible

## Phase 1: Install Exo on All Mac Nodes

### Step 1.1: Install on each Mac

Run on **each** of the three Mac nodes (sasass, sasass2, tpm-macbook):

```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone Exo
cd /Users/Shared/ganuda
git clone https://github.com/exo-explore/exo.git
cd exo

# Build the dashboard
# (requires Node.js - install via brew if needed)
brew install node  # if not installed
cd exo/api/chatgpt-shim
npm install && npm run build
cd /Users/Shared/ganuda/exo

# Test that it starts
uv run exo --help
```

### Step 1.2: Verify network connectivity between nodes

```bash
# From each Mac, verify the others are reachable
ping -c 2 192.168.132.241  # sasass
ping -c 2 192.168.132.242  # sasass2
ping -c 2 192.168.132.21   # tpm-macbook (when connected)
```

## Phase 2: Configure Exo Cluster

### Step 2.1: Start Exo on each node

Exo uses automatic peer discovery via mDNS/UDP broadcast. Just start it on each Mac:

```bash
# On sasass (.241):
cd /Users/Shared/ganuda/exo
uv run exo --node-id sasass --listen-port 52415

# On sasass2 (.242):
cd /Users/Shared/ganuda/exo
uv run exo --node-id sasass2 --listen-port 52415

# On tpm-macbook (.21):
cd /Users/Shared/ganuda/exo
uv run exo --node-id tpm-macbook --listen-port 52415
```

Exo should auto-discover the other nodes and show them in the dashboard at `http://localhost:52415/`.

### Step 2.2: Verify cluster formation

```bash
# Check the dashboard on any node
curl -s http://localhost:52415/v1/models | python3 -m json.tool
```

Should show available models and all three nodes.

### Step 2.3: Test with a large model

```bash
# Download and run Llama 3.1 70B
curl -s -X POST http://localhost:52415/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.1-70b",
    "messages": [{"role": "user", "content": "Hello, what model are you?"}],
    "max_tokens": 100
  }' | python3 -m json.tool
```

## Phase 3: Create Persistent Services

### Step 3.1: Create launchd plist for sasass and sasass2

**File:** `/Users/Shared/ganuda/services/com.cherokee.exo.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.exo</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/Shared/ganuda/exo/.venv/bin/exo</string>
        <string>--listen-port</string>
        <string>52415</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/Shared/ganuda/exo</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/Shared/ganuda/logs/exo.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Shared/ganuda/logs/exo.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
```

### Step 3.2: Install and start on Mac Studios

```bash
# On sasass and sasass2:
mkdir -p /Users/Shared/ganuda/logs
cp /Users/Shared/ganuda/services/com.cherokee.exo.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.cherokee.exo.plist
```

The tpm-macbook can start/stop Exo manually since it's not always connected.

## Phase 4: Integrate with LLM Gateway

### Step 4.1: Add Exo as a backend in the gateway

On **redfin**, update `/ganuda/services/llm_gateway/gateway.py` to add the Exo cluster as an additional backend for large model requests:

```python
EXO_BACKEND = "http://192.168.132.241:52415"  # Exo cluster (sasass primary)
```

Add a new endpoint or route large model requests to the Exo backend when the requested model exceeds what redfin/bluefin can serve.

### Step 4.2: Gateway health check

Add Exo cluster health to the `/health` endpoint:
```python
# Check Exo cluster
exo_status = "unhealthy"
try:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{EXO_BACKEND}/v1/models", timeout=3.0)
        if resp.status_code == 200:
            exo_status = "healthy"
except Exception:
    exo_status = "unreachable"
```

## Architecture After Deployment

```
LLM Gateway (redfin:8080)
  ├── /v1/chat/completions (≤32B) → redfin vLLM (Qwen2.5-Coder-32B, RTX 6000 48GB)
  ├── /v1/vlm/*                   → bluefin adapter:8092 → vLLM:8090 (Qwen2-VL-7B, RTX 5070 12GB)
  └── /v1/chat/completions (70B+) → Exo cluster (sasass+sasass2+laptop, 256GB unified)
```

## Networking Notes

- Exo uses mDNS/UDP broadcast for peer discovery — all nodes must be on same subnet
- sasass (.241) and sasass2 (.242) are on 192.168.132.0/24 — same as federation
- tpm-macbook (.21) is also on 192.168.132.0/24 when on LAN
- If discovery fails over Ethernet, Exo supports manual peer specification:
  ```bash
  uv run exo --node-id sasass --peers "sasass2@192.168.132.242:52415,tpm-macbook@192.168.132.21:52415"
  ```

## Performance Expectations

- Over Gigabit Ethernet: ~5-10 tok/s for 70B models (memory-bandwidth bound, not network)
- Over Thunderbolt (if directly connected): 20-30 tok/s
- The M4 Max MacBook will do more work (128GB = ~50% of layers) with the Mac Studios splitting the rest

## Security Notes

- Exo exposes an HTTP API on port 52415 — bind to 192.168.132.x only, not 0.0.0.0
- No authentication built into Exo — rely on network segmentation (VLAN 1 only)
- Crawdad review recommended before production deployment
- Model downloads go to `~/.cache/huggingface/` — ensure disk space

---
**FOR SEVEN GENERATIONS** - Many minds, one understanding.
