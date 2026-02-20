# Jr Instruction: Deploy MLX Hybrid Inference on M4 Max MacBook

**Task ID:** MLX-M4MAX-001 (REVISED)
**Priority:** P2
**Date:** February 8, 2026 (revised from Feb 7)
**Node:** tpm-macbook (192.168.132.21)
**Assigned:** Infrastructure Jr.
**Council Votes:** #8475 (original MLX approval), #8481 (revised to hybrid approach)
**Supersedes:** EXO-CLUSTER-001 (withdrawn — Exo latency over Ethernet unacceptable)

## Overview

Deploy a **hybrid MLX setup** on the M4 Max MacBook:
- **Always-on:** DeepSeek-R1-Distill-Qwen-32B-4bit (~20GB) — reasoning-focused, complements redfin's code-focused model
- **On-demand:** Qwen2.5-72B-Instruct-4bit (~40GB) — loaded when heavy reasoning is needed

This is a **personal laptop** that also runs Civilization V and development tools. The always-on 32B must coexist gracefully with normal use.

### Why Hybrid (Council Vote #8481)

| Factor | Single 70B | Hybrid 32B+70B |
|--------|-----------|----------------|
| Always-on memory | 40GB (32% of 128GB) | **20GB (16% of 128GB)** |
| Always-on speed | 10-15 tok/s | **30-45 tok/s** |
| Civ V headroom | 88GB | **108GB (always-on) / 68GB (both loaded)** |
| Diversity | Same family as nothing on redfin | **Reasoning model + code model = diverse council** |
| Bandwidth saturation | High during inference | **Lower — smaller model = less bandwidth pressure** |

### Model Selection

| Role | Model | HuggingFace Path | Size (4-bit) | Why |
|------|-------|------------------|-------------|-----|
| Always-on | DeepSeek-R1-Distill-Qwen-32B | `mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit` | ~20GB | Reasoning with `<think>` blocks. Complements code-focused Qwen2.5-Coder-32B on redfin |
| On-demand | Qwen2.5-72B-Instruct | `mlx-community/Qwen2.5-72B-Instruct-4bit` | ~40GB | Heavy-duty general purpose when needed |

**Alternative always-on options** (if DeepSeek has issues):
- `mlx-community/Qwen3-32B-4bit` — built-in thinking capabilities
- `mlx-community/Mistral-Small-3.1-24B-Instruct-2503-4bit` — lightweight at ~15GB

## Hardware

| Spec | Value |
|------|-------|
| Node | tpm-macbook (192.168.132.21) |
| Chip | Apple M4 Max |
| Unified Memory | 128 GB |
| Memory Bandwidth | 546 GB/s |
| Thunderbolt | TB5 (120 Gb/s) |
| Personal use | Civ V, development, browsing |

**Memory budget:**
- macOS + apps: ~10GB
- Civ V (when running): ~8-10GB
- Always-on 32B: ~20GB
- On-demand 70B: ~40GB additional
- **Always-on only:** 128 - 10 - 20 = 98GB free (Civ V comfortable)
- **Both models loaded:** 128 - 10 - 20 - 40 = 58GB free (Civ V still fits)

## Phase 1: Install MLX and mlx-lm

### Step 1.1: Create Python venv

```bash
# On tpm-macbook:
cd /Users/Shared/ganuda
python3 -m venv mlx_venv
source mlx_venv/bin/activate

# Install mlx-lm
pip install mlx-lm

# Verify
python3 -c "import mlx; import mlx_lm; print(f'MLX version: {mlx.__version__}')"
```

### Step 1.2: Download always-on model (DeepSeek-R1-Distill-32B)

```bash
source /Users/Shared/ganuda/mlx_venv/bin/activate

# Download and test (~20GB download)
python3 -m mlx_lm.generate \
    --model mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit \
    --prompt "Explain the concept of seven generations thinking in 3 sentences." \
    --max-tokens 200 \
    --verbose

# Expected: 30-45 tok/s
```

### Step 1.3: Download on-demand model (Qwen2.5-72B)

```bash
# Download for later use (~40GB download)
python3 -m mlx_lm.generate \
    --model mlx-community/Qwen2.5-72B-Instruct-4bit \
    --prompt "Hello" \
    --max-tokens 10

# This just downloads and caches the model. We won't run it as a service.
```

## Phase 2: Deploy Always-On 32B Server

### Step 2.1: Start server

```bash
source /Users/Shared/ganuda/mlx_venv/bin/activate

# Start DeepSeek-R1-Distill-32B on port 8800
# Bind to LAN IP only
python3 -m mlx_lm.server \
    --model mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit \
    --host 192.168.132.21 \
    --port 8800
```

### Step 2.2: Verify API

```bash
# Test models endpoint
curl -s http://192.168.132.21:8800/v1/models | python3 -m json.tool

# Test chat completion
curl -s -X POST http://192.168.132.21:8800/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
        "messages": [{"role": "user", "content": "What are the trade-offs between distributed and single-node inference?"}],
        "max_tokens": 200
    }' | python3 -m json.tool
```

### Step 2.3: Benchmark

```bash
# Quick performance check
python3 -m mlx_lm.generate \
    --model mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit \
    --prompt "Write a detailed analysis of federated AI governance models" \
    --max-tokens 500 \
    --verbose

# Target: >30 tok/s on M4 Max 128GB
```

## Phase 3: Create On-Demand 70B Script

### Step 3.1: Create loader script

**File:** `/Users/Shared/ganuda/scripts/mlx_load_70b.sh`

```bash
#!/bin/bash
# Load Qwen2.5-72B on-demand (port 8801)
# Usage: mlx_load_70b.sh [start|stop]
source /Users/Shared/ganuda/mlx_venv/bin/activate

case "$1" in
    start)
        echo "Loading Qwen2.5-72B-Instruct-4bit on port 8801..."
        echo "This will use ~40GB additional memory."
        nohup python3 -m mlx_lm.server \
            --model mlx-community/Qwen2.5-72B-Instruct-4bit \
            --host 192.168.132.21 \
            --port 8801 \
            > /Users/Shared/ganuda/logs/mlx-70b.log 2>&1 &
        echo $! > /Users/Shared/ganuda/logs/mlx-70b.pid
        echo "Started. PID: $(cat /Users/Shared/ganuda/logs/mlx-70b.pid)"
        echo "Waiting for model load..."
        sleep 30
        curl -s http://192.168.132.21:8801/v1/models | python3 -m json.tool
        ;;
    stop)
        if [ -f /Users/Shared/ganuda/logs/mlx-70b.pid ]; then
            kill $(cat /Users/Shared/ganuda/logs/mlx-70b.pid) 2>/dev/null
            rm /Users/Shared/ganuda/logs/mlx-70b.pid
            echo "Stopped 70B server."
        else
            echo "No PID file found. Checking for running process..."
            pkill -f "mlx_lm.server.*8801" 2>/dev/null && echo "Killed." || echo "Not running."
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        ;;
esac
```

```bash
chmod +x /Users/Shared/ganuda/scripts/mlx_load_70b.sh
```

## Phase 4: Create Persistent Service (Always-On 32B Only)

### Step 4.1: Create launchd plist

**File:** `/Users/Shared/ganuda/services/com.cherokee.mlx-server.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.mlx-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/Shared/ganuda/mlx_venv/bin/python3</string>
        <string>-m</string>
        <string>mlx_lm.server</string>
        <string>--model</string>
        <string>mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit</string>
        <string>--host</string>
        <string>192.168.132.21</string>
        <string>--port</string>
        <string>8800</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/Shared/ganuda</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/Shared/ganuda/logs/mlx-server.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Shared/ganuda/logs/mlx-server.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/Shared/ganuda/mlx_venv/bin:/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
    <key>ProcessType</key>
    <string>Background</string>
    <key>LowPriorityIO</key>
    <true/>
    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
```

**Note:** `Nice=10` and `LowPriorityIO=true` ensure the model server yields to foreground apps (Civ V, browsers, etc.).

### Step 4.2: Install and start

```bash
mkdir -p /Users/Shared/ganuda/logs
cp /Users/Shared/ganuda/services/com.cherokee.mlx-server.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.cherokee.mlx-server.plist

# Verify (model loading takes ~30 seconds)
sleep 30
curl -s http://192.168.132.21:8800/v1/models | python3 -m json.tool
```

## Phase 5: Integrate with LLM Gateway

### Step 5.1: Add MLX backends to gateway

On **redfin**, update `/ganuda/services/llm_gateway/gateway.py`:

```python
# Always-on reasoning model
MLX_REASONING_BACKEND = "http://192.168.132.21:8800"  # DeepSeek-R1-Distill-32B (M4 Max)

# On-demand large model (may not be running)
MLX_LARGE_BACKEND = "http://192.168.132.21:8801"  # Qwen2.5-72B (on-demand)
```

Route reasoning-heavy requests to the MLX reasoning backend. Route oversized requests to MLX large backend (with fallback if it's not running).

### Step 5.2: Add health checks

```python
# Check MLX reasoning (always-on)
mlx_reasoning_status = "unhealthy"
try:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MLX_REASONING_BACKEND}/v1/models", timeout=5.0)
        if resp.status_code == 200:
            mlx_reasoning_status = "healthy"
except Exception:
    mlx_reasoning_status = "unreachable"

# Check MLX large (on-demand — "offline" is normal)
mlx_large_status = "offline"
try:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{MLX_LARGE_BACKEND}/v1/models", timeout=3.0)
        if resp.status_code == 200:
            mlx_large_status = "healthy"
except Exception:
    mlx_large_status = "offline"
```

### Step 5.3: Restart gateway

```bash
sudo systemctl restart llm-gateway
curl -s http://localhost:8080/health | python3 -m json.tool
```

## Architecture After Deployment

```
LLM Gateway (redfin:8080)
  ├── /v1/chat/completions (code/≤32B) → redfin vLLM (Qwen2.5-Coder-32B, RTX 6000 48GB)
  ├── /v1/vlm/*                        → bluefin adapter:8092 → vLLM:8090 (Qwen2-VL-7B-AWQ, RTX 5070)
  ├── /v1/chat/completions (reasoning)  → tpm-macbook MLX:8800 (DeepSeek-R1-32B, always-on)
  └── /v1/chat/completions (large/70B+) → tpm-macbook MLX:8801 (Qwen2.5-72B, on-demand)
```

**Three distinct AI perspectives:**
1. **Qwen2.5-Coder-32B** (redfin) — Code generation, technical implementation
2. **DeepSeek-R1-Distill-32B** (tpm-macbook) — Reasoning, analysis, `<think>` chain-of-thought
3. **Qwen2.5-72B** (tpm-macbook, on-demand) — Heavy-duty general purpose when needed

## Performance Expectations

| Model | Speed | Memory | Availability |
|-------|-------|--------|-------------|
| DeepSeek-R1-32B (4-bit) | 30-45 tok/s | ~20GB | Always-on |
| Qwen2.5-72B (4-bit) | 10-15 tok/s | ~40GB | On-demand |
| Both running | N/A | ~60GB total | When needed |

## Security Notes

- Bind to `192.168.132.21` only, NOT `0.0.0.0`
- No built-in authentication — rely on network segmentation (VLAN 1)
- Model downloads cache to `~/.cache/huggingface/` (~60GB total for both)
- Crawdad: security audit recommended — this is a personal laptop, not dedicated infra
- 70B on-demand script must not auto-start — manual activation only

## Rollback

```bash
# Stop always-on
launchctl unload ~/Library/LaunchAgents/com.cherokee.mlx-server.plist

# Stop on-demand (if running)
/Users/Shared/ganuda/scripts/mlx_load_70b.sh stop

# On redfin, remove MLX backends from gateway and restart
```

---
**FOR SEVEN GENERATIONS** — Diverse minds, diverse perspectives, one federation.
