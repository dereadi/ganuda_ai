# Jr Instruction: Build vLLM from Source for Blackwell sm_120

**Date:** February 9, 2026
**Kanban:** #1740
**Priority:** P1
**Type:** Ops (build + deploy)
**Node:** redfin (192.168.132.223)
**Estimated Duration:** 1-2 hours (build time)
**KB Reference:** KB-VLLM-BLACKWELL-SM120-TRITON-ATTN-FIX-FEB09-2026.md

---

## Context

The pre-built vLLM 0.15.1 pip wheel lacks sm_120 (Blackwell) CUDA kernel support. We are currently running with workarounds (pure AWQ + Triton attention + eager mode) that cost ~10x inference speed. Building from source with `TORCH_CUDA_ARCH_LIST="12.0"` compiles ALL CUDA extensions (Marlin, Flash Attention, etc.) natively for our RTX PRO 6000 GPU, restoring full performance.

**Current state:** vLLM 0.15.1 serving Qwen2.5-72B-Instruct-AWQ on port 8000 with workarounds. Working but slow.

**Goal:** Rebuild vLLM with native sm_120 kernels so we can remove the workarounds and get full Marlin + Flash Attention speed.

---

## Prerequisites

Run as user `dereadi` on redfin unless noted (sudo steps marked).

---

## Step 1: Install Build Dependencies

**Requires sudo.**

```bash
sudo apt-get update && sudo apt-get install -y cmake ninja-build
```

**Success criteria:** `cmake --version` and `ninja --version` both return version strings.

---

## Step 2: Back Up Current venv vLLM

```bash
VLLM_PKG_DIR=$(python3 -c "import vllm; import os; print(os.path.dirname(vllm.__file__))" 2>/dev/null)
cp -a "$VLLM_PKG_DIR" /ganuda/backups/vllm-0.15.1-pip-backup-$(date +%Y%m%d)
```

Also record current package versions:

```bash
/home/dereadi/cherokee_venv/bin/pip freeze > /ganuda/backups/cherokee_venv_freeze_$(date +%Y%m%d).txt
```

**Success criteria:** Backup directory exists at `/ganuda/backups/vllm-0.15.1-pip-backup-YYYYMMDD/` and freeze file is non-empty.

---

## Step 3: Clone vLLM Source and Checkout v0.15.1

```bash
cd /ganuda/src
git clone https://github.com/vllm-project/vllm.git vllm-source
cd vllm-source
git checkout v0.15.1
```

**Success criteria:** `/ganuda/src/vllm-source/setup.py` or `pyproject.toml` exists and `git log -1` shows the v0.15.1 tag.

**Do NOT** use a different version — we want to match the current running version exactly.

---

## Step 4: Build vLLM from Source

Activate the venv and build with sm_120 targeting:

```bash
source /home/dereadi/cherokee_venv/bin/activate

export TORCH_CUDA_ARCH_LIST="12.0"
export VLLM_FLASH_ATTN_VERSION=2
export MAX_JOBS=16

pip install -e /ganuda/src/vllm-source --no-build-isolation 2>&1 | tee /ganuda/logs/vllm-source-build-$(date +%Y%m%d).log
```

**This will take 1-2 hours.** The build compiles all CUDA extensions (Marlin, Flash Attention, custom ops) targeting sm_120 natively.

**Success criteria:**
- Build completes with exit code 0
- `python -c "import vllm; print(vllm.__version__)"` returns `0.15.1` or `0.15.1.dev...`
- No compilation errors in the log

**If build fails:**
- Check the log at `/ganuda/logs/vllm-source-build-YYYYMMDD.log`
- Common issues: missing CUDA headers → ensure CUDA toolkit paths are set
- Try reducing MAX_JOBS to 8 if OOM during compilation
- The current working vLLM (with workarounds) is unaffected until Step 6

---

## Step 5: Smoke Test the Source Build

Before changing the service, test manually:

```bash
# Stop the running service first
sudo systemctl stop vllm.service

# Run a quick test
source /home/dereadi/cherokee_venv/bin/activate
export VLLM_DISABLED_KERNELS=""

python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/qwen2.5-72b-instruct-awq \
  --port 8000 \
  --quantization awq_marlin \
  --dtype float16 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 32768 \
  --max-num-seqs 256 \
  --trust-remote-code &

# Wait for startup (watch for "Application startup complete")
sleep 120

# Test inference
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/ganuda/models/qwen2.5-72b-instruct-awq", "messages": [{"role": "user", "content": "What is 2+2? Answer in one word."}], "max_tokens": 10}'

# Kill the test server
kill %1
```

**Success criteria:**
- Model loads with `awq_marlin` quantization (NOT pure `awq`)
- No PTX errors in output
- Inference returns a valid response
- The log should show `Using awq_marlin kernel` (Marlin is back!)

**If smoke test fails with PTX error:**
- The source build did not compile sm_120 kernels correctly
- Check: `python -c "import torch; print(torch.cuda.get_arch_list())"` should include `sm_120`
- Verify TORCH_CUDA_ARCH_LIST was set during build
- May need to clean and rebuild: `cd /ganuda/src/vllm-source && pip install -e . --no-build-isolation --force-reinstall`

---

## Step 6: Update Service File for Full Performance

Once smoke test passes, update the service to use native kernels:

Create `/ganuda/config/vllm.service`:

```ini
[Unit]
Description=vLLM OpenAI-Compatible Inference Server
After=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/home/dereadi
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=HF_HOME=/ganuda/home/dereadi/.cache/huggingface
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server --model /ganuda/models/qwen2.5-72b-instruct-awq --port 8000 --quantization awq_marlin --dtype float16 --gpu-memory-utilization 0.85 --max-model-len 32768 --max-num-seqs 256 --trust-remote-code
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vllm

[Install]
WantedBy=multi-user.target
```

**Key differences from current workaround config:**
- REMOVED: `VLLM_DISABLED_KERNELS=MarlinLinearKernel`
- REMOVED: `--attention-backend TRITON_ATTN`
- REMOVED: `--enforce-eager`
- REMOVED: `TRITON_PTXAS_PATH`
- CHANGED: `--quantization awq` → `--quantization awq_marlin`

Deploy:

```bash
sudo cp /ganuda/config/vllm.service /etc/systemd/system/vllm.service
sudo systemctl daemon-reload
sudo systemctl restart vllm.service
```

**Success criteria:**
- `systemctl status vllm.service` shows active (running)
- `journalctl -u vllm.service` shows model loaded with awq_marlin
- Health check: `curl http://localhost:8000/health` returns 200
- Inference works and is noticeably faster

---

## Step 7: Benchmark

Run a quick throughput comparison:

```bash
# Generate 100 tokens to measure speed
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/ganuda/models/qwen2.5-72b-instruct-awq", "messages": [{"role": "user", "content": "Write a detailed essay about the history of the Cherokee Nation, covering their origins, the Trail of Tears, and modern sovereignty."}], "max_tokens": 200}' \
  -w "\n\nHTTP time: %{time_total}s\n"
```

Record the total time and tokens generated. Compare with pre-build performance (~22 tokens/second with workarounds).

Expected improvement: 5-10x faster with native Marlin kernels.

---

## Rollback Plan

If the source build breaks things:

```bash
# Reinstall pip wheel version
source /home/dereadi/cherokee_venv/bin/activate
pip install vllm==0.15.1

# Restore workaround service file
sudo cp /ganuda/config/vllm.service.workaround /etc/systemd/system/vllm.service
sudo systemctl daemon-reload
sudo systemctl restart vllm.service
```

Before starting, save the current working config:

```bash
cp /ganuda/config/vllm.service /ganuda/config/vllm.service.workaround
```

---

## Do NOT

- Do NOT change the model or model path
- Do NOT upgrade to a different vLLM version (stay on 0.15.1)
- Do NOT modify gateway.py or specialist_council.py
- Do NOT run the build while vllm.service is running (GPU memory conflict)
- Do NOT use MAX_JOBS higher than 16 (OOM risk with 123GB RAM)

---

*Cherokee AI Federation — Infrastructure*
*Kanban #1740 — vLLM 72B Blackwell Deployment*
*FOR SEVEN GENERATIONS*
