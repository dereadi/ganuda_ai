#!/bin/bash
# Build vLLM from source for Blackwell sm_120
# Kanban #1740 — Run as dereadi with sudo access
# Expected duration: 1-2 hours
set -e

LOG="/ganuda/logs/vllm-source-build-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

echo "=========================================="
echo "vLLM Source Build for sm_120 (Blackwell)"
echo "Started: $(date)"
echo "Log: $LOG"
echo "=========================================="

# Step 1: Install build deps
echo ""
echo "[Step 1/7] Installing build dependencies..."
sudo apt-get update -qq
sudo apt-get install -y cmake ninja-build
cmake --version
ninja --version
echo "[Step 1/7] DONE"

# Step 1b: Install Python build deps
echo ""
echo "[Step 1b] Installing Python build dependencies..."
/home/dereadi/cherokee_venv/bin/pip install setuptools_scm 2>&1 | tail -3
echo "[Step 1b] DONE"

# Step 1c: Set CUDA_HOME (symlinks to container overlay CUDA 12.8 toolkit)
export CUDA_HOME="/ganuda/cuda-12.8"
export CUDA_PATH="/ganuda/cuda-12.8"
export CUDA_TOOLKIT_ROOT_DIR="/ganuda/cuda-12.8"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}"
echo "[Step 1c] CUDA_HOME=$CUDA_HOME"
echo "nvcc: $($CUDA_HOME/bin/nvcc --version 2>&1 | tail -1)"

# Step 2: Backup
echo ""
echo "[Step 2/7] Backing up current vLLM..."
mkdir -p /ganuda/backups
/home/dereadi/cherokee_venv/bin/pip freeze > /ganuda/backups/cherokee_venv_freeze_$(date +%Y%m%d).txt
VLLM_DIR=$(/home/dereadi/cherokee_venv/bin/python -c "import vllm, os; print(os.path.dirname(vllm.__file__))")
cp -a "$VLLM_DIR" /ganuda/backups/vllm-0.15.1-pip-backup-$(date +%Y%m%d)
echo "Backed up: $VLLM_DIR"
echo "[Step 2/7] DONE"

# Step 3: Clone source
echo ""
echo "[Step 3/7] Cloning vLLM v0.15.1 source..."
mkdir -p /ganuda/src
if [ -d /ganuda/src/vllm-source ]; then
    echo "Source dir exists, removing old clone..."
    rm -rf /ganuda/src/vllm-source
fi
git clone --branch v0.15.1 https://github.com/vllm-project/vllm.git /ganuda/src/vllm-source
cd /ganuda/src/vllm-source
echo "Cloned: $(git log -1 --oneline)"
echo "[Step 3/7] DONE"

# Step 4: Build from source
echo ""
echo "[Step 4/7] Building vLLM from source (this takes 1-2 hours)..."
source /home/dereadi/cherokee_venv/bin/activate

export CUDA_HOME="/ganuda/cuda-12.8"
export CUDA_PATH="/ganuda/cuda-12.8"
export CUDA_TOOLKIT_ROOT_DIR="/ganuda/cuda-12.8"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}"
export CMAKE_CUDA_COMPILER="$CUDA_HOME/bin/nvcc"
export TORCH_CUDA_ARCH_LIST="12.0"
export VLLM_FLASH_ATTN_VERSION=2
export MAX_JOBS=16

pip install -e /ganuda/src/vllm-source --no-build-isolation

VLLM_VER=$(python -c "import vllm; print(vllm.__version__)")
echo "Installed vLLM version: $VLLM_VER"
echo "[Step 4/7] DONE"

# Step 5: Smoke test
echo ""
echo "[Step 5/7] Smoke testing with awq_marlin (native sm_120)..."
sudo systemctl stop vllm.service || true
sleep 5

# Start test server in background
python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/qwen2.5-72b-instruct-awq \
  --port 8000 \
  --quantization awq_marlin \
  --dtype float16 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 32768 \
  --max-num-seqs 256 \
  --trust-remote-code &
VLLM_PID=$!

echo "Waiting for vLLM to start (PID: $VLLM_PID)..."
for i in $(seq 1 60); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "Health check passed after ${i}0 seconds"
        break
    fi
    if ! kill -0 $VLLM_PID 2>/dev/null; then
        echo "ERROR: vLLM process died during startup!"
        echo "[Step 5/7] FAILED — falling back to workaround config"
        # Restore workaround service
        sudo cp /ganuda/config/vllm.service.workaround /etc/systemd/system/vllm.service
        sudo systemctl daemon-reload
        sudo systemctl start vllm.service
        echo "Workaround service restored and started."
        echo "Build log: $LOG"
        exit 1
    fi
    sleep 10
done

# Test inference
echo "Testing inference..."
RESPONSE=$(curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/ganuda/models/qwen2.5-72b-instruct-awq", "messages": [{"role": "user", "content": "What is 2+2? Answer in one word."}], "max_tokens": 10}')

echo "Response: $RESPONSE"

if echo "$RESPONSE" | grep -q '"finish_reason":"stop"'; then
    echo "Inference test PASSED!"
else
    echo "ERROR: Inference test FAILED"
    kill $VLLM_PID 2>/dev/null || true
    wait $VLLM_PID 2>/dev/null || true
    # Restore workaround
    sudo cp /ganuda/config/vllm.service.workaround /etc/systemd/system/vllm.service
    sudo systemctl daemon-reload
    sudo systemctl start vllm.service
    echo "Workaround service restored."
    echo "Build log: $LOG"
    exit 1
fi

# Kill test server
kill $VLLM_PID 2>/dev/null || true
wait $VLLM_PID 2>/dev/null || true
sleep 5
echo "[Step 5/7] DONE"

# Step 6: Deploy native service config
echo ""
echo "[Step 6/7] Deploying native sm_120 service config..."
cat > /ganuda/config/vllm.service.native << 'SVCEOF'
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
SVCEOF

sudo cp /ganuda/config/vllm.service.native /etc/systemd/system/vllm.service
sudo systemctl daemon-reload
sudo systemctl start vllm.service

sleep 30

if systemctl is-active --quiet vllm.service; then
    echo "Service is running with native sm_120 kernels!"
else
    echo "WARNING: Service failed to start with native config"
    echo "Reverting to workaround..."
    sudo cp /ganuda/config/vllm.service.workaround /etc/systemd/system/vllm.service
    sudo systemctl daemon-reload
    sudo systemctl start vllm.service
    echo "Workaround service restored."
    exit 1
fi
echo "[Step 6/7] DONE"

# Step 7: Benchmark
echo ""
echo "[Step 7/7] Benchmarking..."
sleep 10

START_TIME=$(date +%s%N)
BENCH=$(curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/ganuda/models/qwen2.5-72b-instruct-awq", "messages": [{"role": "user", "content": "Write a detailed paragraph about the history of the Cherokee Nation, covering their origins, the Trail of Tears, and modern sovereignty efforts."}], "max_tokens": 200}')
END_TIME=$(date +%s%N)

ELAPSED_MS=$(( (END_TIME - START_TIME) / 1000000 ))
TOKENS=$(echo "$BENCH" | python -c "import sys,json; d=json.load(sys.stdin); print(d['usage']['completion_tokens'])" 2>/dev/null || echo "unknown")
echo "Generated $TOKENS tokens in ${ELAPSED_MS}ms"
if [ "$TOKENS" != "unknown" ] && [ "$ELAPSED_MS" -gt 0 ]; then
    TPS=$(python -c "print(f'{$TOKENS / ($ELAPSED_MS / 1000):.1f}')" 2>/dev/null || echo "unknown")
    echo "Throughput: ~${TPS} tokens/second"
fi

echo ""
echo "=========================================="
echo "BUILD COMPLETE"
echo "Finished: $(date)"
echo "vLLM: native sm_120 with awq_marlin"
echo "Log: $LOG"
echo "=========================================="
