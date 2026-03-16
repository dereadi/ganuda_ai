# Jr Instruction: Deploy BitNet.cpp Ternary Inference on Greenfin

**Task ID**: To be assigned
**Priority**: P2
**Story Points**: 3
**Node**: greenfin (192.168.132.224 / 10.100.0.3)
**Blocked by**: Nothing
**Blocks**: Consultation Ring LocalAdapter integration (gated on benchmark — Coyote condition)
**Epic**: Sovereign Inference / DC-9 Waste Heat
**Council Vote**: `#a1a673b834ba2e0f` (0.891 confidence, 8/0/0 APPROVED WITH CONDITIONS)

## What This Delivers

A CPU-only ternary LLM inference endpoint on greenfin, running Microsoft's BitNet.cpp framework. 100B-class models on pure CPU at 5-7 tok/s with 72-82% less energy than GPU inference. Greenfin has 107 GB free RAM, 16 Zen 5 cores, and is currently underutilized.

This is DC-9 in action: sovereign inference without Nvidia dependency, on hardware we already own, at a fraction of the energy cost.

## Why Greenfin

| Resource | Available | BitNet Needs |
|----------|-----------|-------------|
| RAM | 107 GB free | ~20 GB for 100B model |
| CPU | 16 cores / 32 threads (Zen 5) | Integer math — Zen 5 excels |
| Disk | 1.6 TB free | ~15 GB for model weights |
| GPU | None needed | CPU-only inference |
| Network | WireGuard 10.100.0.3 | Consultation Ring calls over mesh |

Greenfin is on the WireGuard mesh and can be reached from redfin (Consultation Ring) at 10.100.0.3.

## Implementation

### Step 1: Install Build Dependencies

```bash
sudo apt install -y clang-18 cmake git python3-pip python3-venv
```

Both clang-18 and cmake are available in the Ubuntu 24.04 noble repos. libclang-18 is already installed.

### Step 2: Clone and Build BitNet.cpp

```bash
cd /ganuda
git clone https://github.com/microsoft/BitNet.git bitnet
cd bitnet
# Pin to known-good commit (Owl condition) — update hash after verifying latest stable
git checkout <PINNED_COMMIT_HASH>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup_env.py --hf-repo microsoft/BitNet-b1.58-2B-4T -q i2_s
```

This downloads the official 2.4B parameter model (trained on 4T tokens) and builds the inference engine with clang-18.

**Owl condition**: Before cloning, check the latest stable release/tag on the BitNet repo. Pin the exact commit hash in this instruction and record it in greenfin's recovery runbook.

### Step 3: Verify Inference

```bash
cd /ganuda/bitnet
source venv/bin/activate
python run_inference.py -m models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf \
  -p "Explain what ternary computing means for AI inference" \
  -t 8 -n 128
```

Expected: 5-7 tokens/second on greenfin's Zen 5 cores.

### Step 4: Benchmark

```bash
python utils/e2e_benchmark.py -m models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf \
  -n 200 -p 256 -t 16
```

Record: tokens/second, memory usage, CPU utilization. Compare against vLLM on redfin for same prompt.

### Step 5: Create Inference API Wrapper

**File**: `/ganuda/services/bitnet_inference/server.py`

Simple FastAPI wrapper on port 9500:

```
POST /generate
  - prompt (str, max 4096 chars — Eagle Eye condition)
  - max_tokens (int, default 256, max 1024)
  - temperature (float, default 0.7)
  → returns {"text": "...", "tokens_per_second": float, "model": "BitNet-b1.58-2B-4T", "cpu_temp_c": float}
  → rejects prompts > 4096 chars with 400 (Eagle Eye condition)

GET /health
  → returns necklace-format JSON for Fire Guard, includes cpu_temp_c (Peace Chief condition)
```

Subprocess calls to `run_inference.py` or use the Python bindings if available.

**Crawdad condition**: Do NOT log full prompt text to disk. Log only metadata: timestamp, prompt_length, max_tokens, tokens_per_second, latency_ms. If full prompt logging is needed for debugging, route through the thermal memory pipeline with PII scrub.

### Step 6: Systemd Service

**File**: `/etc/systemd/system/bitnet-inference.service`

```ini
[Unit]
Description=BitNet Ternary Inference Service
After=network.target

[Service]
Type=simple
User=dereadi
ExecStart=/ganuda/bitnet/venv/bin/python /ganuda/services/bitnet_inference/server.py
WorkingDirectory=/ganuda/services/bitnet_inference
Environment=PYTHONPATH=/ganuda
Restart=on-failure
RestartSec=10
# Turtle condition: limit to 8 of 16 cores so embedding/Promtail/OpenObserve are never starved
AllowedCPUs=0-7

[Install]
WantedBy=multi-user.target
```

**Turtle condition**: Do NOT enable on boot (`systemctl enable`) until 48 hours of manual observation pass. Start with `systemctl start` only. Enable after validation.

### Step 7: Fire Guard Integration

Add port 9500 health check to `/ganuda/scripts/fire_guard.py` necklace on greenfin.

## Testing

1. **Build**: BitNet.cpp compiles without errors on greenfin
2. **Inference**: Model generates coherent text at >3 tok/s
3. **Benchmark**: Record tok/s, memory, CPU — compare to redfin vLLM
4. **API**: `curl localhost:9500/generate -d '{"prompt":"hello","max_tokens":32}'` returns valid JSON
5. **Health**: `curl localhost:9500/health` returns necklace-format
6. **Mesh access**: From redfin: `curl 10.100.0.3:9500/health` returns OK
7. **Energy**: Monitor power draw during inference vs idle baseline

## Future Integration

**Coyote condition (GATE)**: Do NOT route production Consultation Ring queries to BitNet until benchmark comparison against vLLM on the same prompts shows acceptable quality. Record honest results — no "it works!" theater. The 2.4B model will not match Qwen2.5-72B on reasoning tasks. That's fine — it fills a different niche (fast, cheap, zero-GPU). But the quality boundary must be documented before production routing.

Once Consultation Ring service is live (port 9400 on redfin) AND benchmarks are validated, the LocalAdapter can be pointed at `10.100.0.3:9500` instead of (or alongside) vLLM. This gives the UCB bandit a zero-GPU-cost consultation option with different model DNA (ternary vs FP16).

## Definition of Done

- [ ] BitNet.cpp built on greenfin from pinned commit hash (Owl)
- [ ] BitNet-b1.58-2B-4T model downloaded and running
- [ ] >3 tok/s on greenfin CPU
- [ ] FastAPI wrapper on port 9500 with input length validation (Eagle Eye)
- [ ] No full prompt logging — metadata only (Crawdad)
- [ ] Systemd service started (NOT enabled — Turtle 48hr gate)
- [ ] AllowedCPUs=0-7 in service file (Turtle)
- [ ] CPU thermal monitoring in health endpoint and benchmarks (Peace Chief)
- [ ] Fire Guard health check added
- [ ] Reachable from redfin over WireGuard mesh (10.100.0.3 only)
- [ ] Honest benchmark vs vLLM recorded (Coyote — gate for Consultation Ring routing)
- [ ] Commit hash and build steps added to greenfin recovery runbook (Owl)
