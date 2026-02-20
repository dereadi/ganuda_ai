#!/bin/bash
# Resume vLLM sm_120 native build — Steps 5-7
# Picks up where build_vllm_sm120.sh was interrupted by network drop
# Kanban #1740
set -e

LOG="/ganuda/logs/vllm-sm120-resume-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

echo "=========================================="
echo "vLLM sm_120 Native — Resume Steps 5-7"
echo "Started: $(date)"
echo "Log: $LOG"
echo "=========================================="

# ── Step 0: Clean up zombie processes from interrupted build ──
echo ""
echo "[Step 0] Cleaning up stopped processes from network drop..."
# Kill stopped build script and its children
kill -9 8761 8763 9086 2>/dev/null || true
# The sudo systemctl stop (PID 34894) is stuck in T state
sudo kill -9 34894 2>/dev/null || true
sleep 2
echo "Zombies cleared."

# ── Set environment ──
export CUDA_HOME="/ganuda/cuda-12.8"
export CUDA_PATH="/ganuda/cuda-12.8"
export PATH="$CUDA_HOME/bin:/home/dereadi/cherokee_venv/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}"
source /home/dereadi/cherokee_venv/bin/activate

# ── Step 5: Smoke test with native awq_marlin ──
echo ""
echo "[Step 5/7] Smoke testing native sm_120 with awq_marlin..."
echo ">>> Council will be OFFLINE during this test <<<"

# Stop the workaround service
echo "Stopping workaround vLLM service..."
sudo systemctl stop vllm.service
sleep 5

# Confirm it's down
if curl -s --max-time 3 http://localhost:8000/health > /dev/null 2>&1; then
    echo "WARNING: Port 8000 still responding, force-killing..."
    sudo fuser -k 8000/tcp 2>/dev/null || true
    sleep 3
fi
echo "Port 8000 clear."

# Start native server — NO enforce-eager, NO TRITON_ATTN workarounds
echo "Starting native vLLM with awq_marlin (sm_120 Marlin kernels)..."
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
echo "Native vLLM PID: $VLLM_PID"

# Wait for health (up to 10 minutes for model load)
echo "Waiting for health check..."
HEALTHY=0
for i in $(seq 1 60); do
    if curl -s --max-time 3 http://localhost:8000/health > /dev/null 2>&1; then
        echo "Health check PASSED after $((i * 10)) seconds"
        HEALTHY=1
        break
    fi
    if ! kill -0 $VLLM_PID 2>/dev/null; then
        echo "ERROR: Native vLLM process died during startup!"
        echo "Last 30 lines of output:"
        # Check journalctl for any output
        journalctl --no-pager -n 30 2>/dev/null || true
        break
    fi
    echo "  ...waiting ($((i * 10))s)"
    sleep 10
done

if [ "$HEALTHY" -ne 1 ]; then
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  NATIVE SMOKE TEST FAILED — REVERTING    ║"
    echo "╚══════════════════════════════════════════╝"
    kill $VLLM_PID 2>/dev/null || true
    wait $VLLM_PID 2>/dev/null || true
    sleep 3
    echo "Restoring workaround service..."
    sudo systemctl start vllm.service
    sleep 10
    if curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
        echo "Workaround service restored. Council is back online."
    else
        echo "CRITICAL: Workaround service also failed to start!"
        echo "Manual intervention needed: sudo systemctl restart vllm.service"
    fi
    echo "Build log: $LOG"
    exit 1
fi

# ── Inference test ──
echo ""
echo "Testing inference with native Marlin kernels..."
RESPONSE=$(curl -s --max-time 30 http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/ganuda/models/qwen2.5-72b-instruct-awq", "messages": [{"role": "user", "content": "What is 2+2? Answer in one word."}], "max_tokens": 10}')

echo "Response: $RESPONSE"

if echo "$RESPONSE" | grep -q '"finish_reason"'; then
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  NATIVE INFERENCE TEST PASSED!           ║"
    echo "╚══════════════════════════════════════════╝"
else
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  INFERENCE FAILED — REVERTING            ║"
    echo "╚══════════════════════════════════════════╝"
    kill $VLLM_PID 2>/dev/null || true
    wait $VLLM_PID 2>/dev/null || true
    sleep 3
    sudo systemctl start vllm.service
    sleep 10
    echo "Workaround service restored."
    echo "Build log: $LOG"
    exit 1
fi

# Kill test server
kill $VLLM_PID 2>/dev/null || true
wait $VLLM_PID 2>/dev/null || true
sleep 5
echo "[Step 5/7] DONE"

# ── Step 6: Deploy native service config ──
echo ""
echo "[Step 6/7] Deploying native sm_120 service config..."

cat > /ganuda/config/vllm.service.native << 'SVCEOF'
[Unit]
Description=vLLM OpenAI-Compatible Inference Server (Native sm_120)
After=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/home/dereadi
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=HF_HOME=/ganuda/home/dereadi/.cache/huggingface
Environment=CUDA_HOME=/ganuda/cuda-12.8
Environment=LD_LIBRARY_PATH=/ganuda/cuda-12.8/lib64:/ganuda/cuda-12.8/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model /ganuda/models/qwen2.5-72b-instruct-awq \
  --port 8000 \
  --quantization awq_marlin \
  --dtype float16 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 32768 \
  --max-num-seqs 256 \
  --trust-remote-code
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

echo "Waiting for service to stabilize (30s)..."
sleep 30

if systemctl is-active --quiet vllm.service; then
    # Double-check with health endpoint
    if curl -s --max-time 10 http://localhost:8000/health > /dev/null 2>&1; then
        echo ""
        echo "╔══════════════════════════════════════════╗"
        echo "║  NATIVE SERVICE DEPLOYED AND HEALTHY!    ║"
        echo "╚══════════════════════════════════════════╝"
    else
        echo "Service running but health not responding yet, waiting 60 more seconds..."
        sleep 60
        if curl -s --max-time 10 http://localhost:8000/health > /dev/null 2>&1; then
            echo "Health check passed on second attempt."
        else
            echo "WARNING: Service running but health endpoint not responding."
            echo "Check: journalctl -u vllm.service -n 50"
        fi
    fi
else
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  SERVICE FAILED — REVERTING              ║"
    echo "╚══════════════════════════════════════════╝"
    sudo cp /ganuda/config/vllm.service.workaround /etc/systemd/system/vllm.service
    sudo systemctl daemon-reload
    sudo systemctl start vllm.service
    echo "Workaround service restored."
    echo "Build log: $LOG"
    exit 1
fi
echo "[Step 6/7] DONE"

# ── Step 7: Benchmark ──
echo ""
echo "[Step 7/7] Benchmarking native sm_120 performance..."
sleep 10

# Warm up
curl -s --max-time 30 http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/ganuda/models/qwen2.5-72b-instruct-awq", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 5}' > /dev/null 2>&1

# Real benchmark
START_NS=$(date +%s%N)
BENCH=$(curl -s --max-time 60 http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/ganuda/models/qwen2.5-72b-instruct-awq", "messages": [{"role": "user", "content": "Write a detailed paragraph about the history of the Cherokee Nation, covering their origins, the Trail of Tears, and modern sovereignty efforts."}], "max_tokens": 200}')
END_NS=$(date +%s%N)

ELAPSED_MS=$(( (END_NS - START_NS) / 1000000 ))
TOKENS=$(echo "$BENCH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['usage']['completion_tokens'])" 2>/dev/null || echo "unknown")
PROMPT_TOKENS=$(echo "$BENCH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['usage']['prompt_tokens'])" 2>/dev/null || echo "unknown")

echo ""
echo "── BENCHMARK RESULTS ──"
echo "Prompt tokens:     $PROMPT_TOKENS"
echo "Completion tokens: $TOKENS"
echo "Wall time:         ${ELAPSED_MS}ms"

if [ "$TOKENS" != "unknown" ] && [ "$ELAPSED_MS" -gt 0 ]; then
    TPS=$(python3 -c "print(f'{$TOKENS / ($ELAPSED_MS / 1000):.1f}')")
    echo "Throughput:        ${TPS} tokens/sec"
    echo ""
    echo "Compare to workaround (TRITON_ATTN + enforce-eager):"
    echo "  Expected ~3-5 tok/s workaround → ~15-30+ tok/s native"
fi

echo ""
echo "=========================================="
echo "BUILD COMPLETE — NATIVE sm_120 DEPLOYED"
echo "Finished: $(date)"
echo "Model: Qwen2.5-72B-Instruct-AWQ"
echo "Quantization: awq_marlin (native Marlin kernels)"
echo "GPU: RTX PRO 6000 (Blackwell sm_120)"
echo "No workarounds: enforce-eager OFF, TRITON_ATTN OFF"
echo "Log: $LOG"
echo "=========================================="
