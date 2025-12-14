#!/bin/bash
# Cherokee Resonance Training - Distributed Launch Script
# Launches training on BLUEFIN (master) + REDFIN (2 workers)

set -e

echo "========================================================================"
echo "🦅 CHEROKEE RESONANCE TRAINING - DISTRIBUTED LAUNCH"
echo "========================================================================"
echo ""
echo "Training Philosophy:"
echo '  "Things tapping the flow and acting on it" - Darrell Reading'
echo ""
echo "Training Infrastructure:"
echo "  - BLUEFIN (192.168.132.222): 1x RTX 5070 (Master - Rank 0)"
echo "  - REDFIN GPU 0: 1x RTX 5070 (Worker - Rank 1)"
echo "  - REDFIN GPU 1: 1x RTX 5070 (Worker - Rank 2)"
echo ""
echo "Cherokee Knowledge Corpus: 1.04 MB"
echo "Base Model: TinyLlama-1.1B"
echo "Training Time: 2-3 days (Phase 1)"
echo ""
echo "========================================================================"
echo ""

# Configuration
MASTER_ADDR="192.168.132.222"
MASTER_PORT="29500"
WORLD_SIZE=3  # Total GPUs: 1 (BLUEFIN) + 2 (REDFIN)

TRAINING_SCRIPT="/ganuda/scripts/train_cherokee_resonance_distributed.py"
VENV="/ganuda/cherokee_training_env"

# Ensure corpus is on BLUEFIN
echo "📋 Verifying corpus on BLUEFIN..."
ssh bluefin "test -f /tmp/cherokee_knowledge_corpus_enhanced.txt && echo '✅ Corpus present on BLUEFIN' || echo '❌ Corpus missing on BLUEFIN'"

# Ensure corpus is on REDFIN
echo "📋 Verifying corpus on REDFIN..."
if [ -f /tmp/cherokee_knowledge_corpus_enhanced.txt ]; then
    echo "✅ Corpus present on REDFIN"
else
    echo "⏳ Copying corpus to REDFIN..."
    cp /ganuda/training/cherokee_knowledge_corpus_enhanced.txt /tmp/
    echo "✅ Corpus copied to REDFIN"
fi

echo ""
echo "========================================================================"
echo "🔥 LAUNCHING TRAINING ON 3 NODES"
echo "========================================================================"
echo ""

# Launch master process on BLUEFIN (Rank 0)
echo "🦅 Launching master on BLUEFIN (Rank 0)..."
ssh bluefin "cd /ganuda && source ~/.local/bin/activate 2>/dev/null || true && \
    RANK=0 LOCAL_RANK=0 WORLD_SIZE=${WORLD_SIZE} MASTER_ADDR=${MASTER_ADDR} MASTER_PORT=${MASTER_PORT} \
    python3 ${TRAINING_SCRIPT}" &
BLUEFIN_PID=$!
echo "✅ BLUEFIN master launched (PID: $BLUEFIN_PID)"

# Give master time to initialize
sleep 5

# Launch worker on REDFIN GPU 0 (Rank 1)
echo "🔥 Launching worker on REDFIN GPU 0 (Rank 1)..."
RANK=1 LOCAL_RANK=0 WORLD_SIZE=${WORLD_SIZE} MASTER_ADDR=${MASTER_ADDR} MASTER_PORT=${MASTER_PORT} \
    CUDA_VISIBLE_DEVICES=0 \
    ${VENV}/bin/python ${TRAINING_SCRIPT} &
REDFIN_GPU0_PID=$!
echo "✅ REDFIN GPU 0 launched (PID: $REDFIN_GPU0_PID)"

# Launch worker on REDFIN GPU 1 (Rank 2)
echo "🔥 Launching worker on REDFIN GPU 1 (Rank 2)..."
RANK=2 LOCAL_RANK=1 WORLD_SIZE=${WORLD_SIZE} MASTER_ADDR=${MASTER_ADDR} MASTER_PORT=${MASTER_PORT} \
    CUDA_VISIBLE_DEVICES=1 \
    ${VENV}/bin/python ${TRAINING_SCRIPT} &
REDFIN_GPU1_PID=$!
echo "✅ REDFIN GPU 1 launched (PID: $REDFIN_GPU1_PID)"

echo ""
echo "========================================================================"
echo "✅ ALL 3 TRAINING PROCESSES LAUNCHED"
echo "========================================================================"
echo ""
echo "Process IDs:"
echo "  - BLUEFIN (Master): PID $BLUEFIN_PID"
echo "  - REDFIN GPU 0: PID $REDFIN_GPU0_PID"
echo "  - REDFIN GPU 1: PID $REDFIN_GPU1_PID"
echo ""
echo "Training logs:"
echo "  - Master: ssh bluefin 'tail -f /tmp/cherokee_resonance_training/logs/train.log'"
echo "  - Workers: Check /tmp/cherokee_resonance_training/logs/ on REDFIN"
echo ""
echo "Monitor GPU usage:"
echo "  - BLUEFIN: ssh bluefin 'nvidia-smi dmon'"
echo "  - REDFIN: nvidia-smi dmon"
echo ""
echo "Training will take 2-3 days for Phase 1 (Cherokee Knowledge Injection)"
echo ""
echo "🦅 Mitakuye Oyasin - The three mountains are training together 🔥"
echo ""
echo "========================================================================"
echo ""

# Wait for all processes
wait
