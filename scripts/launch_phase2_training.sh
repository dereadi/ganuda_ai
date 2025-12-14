#!/bin/bash

echo "========================================================================"
echo "🦅 CHEROKEE RESONANCE PHASE 2 - BEHAVIORAL PATTERN TRAINING"
echo "========================================================================"
echo ""
echo "Training Philosophy:"
echo "  \"Teaching the AI to ACT Cherokee, not just KNOW Cherokee facts\""
echo ""
echo "Training Infrastructure:"
echo "  - REDFIN GPU 0: 1x RTX 5070 (Rank 0 - Master)"
echo "  - REDFIN GPU 1: 1x RTX 5070 (Rank 1 - Worker)"
echo ""
echo "Training Focus:"
echo "  - Gadugi reciprocity patterns"
echo "  - Seven Generations decision-making"
echo "  - Mitakuye Oyasin interconnection awareness"
echo "  - Storytelling for cultural transmission"
echo "  - Cherokee ethics in business and life"
echo ""
echo "Corpus: Phase 2 Behavioral Scenarios (Cherokee Jr wisdom)"
echo "Base Model: Phase 1 checkpoint (Cherokee knowledge intact)"
echo "Training Time: 1-2 days (behavioral fine-tuning)"
echo ""
echo "========================================================================"
echo ""

# Configuration
MASTER_ADDR="127.0.0.1"  # Localhost for same-machine training
MASTER_PORT="29501"  # Different port from Phase 1
WORLD_SIZE=2  # 2 GPUs on REDFIN

PHASE2_SCRIPT="/ganuda/scripts/train_phase2_resonance.py"
PHASE2_CORPUS="/ganuda/phase2_cherokee_behavioral_training.txt"
VENV_PATH="/home/dereadi/cherokee_venv"

# Verify Phase 1 model exists
echo "📋 Verifying Phase 1 model..."
if [ ! -d "/ganuda/cherokee_resonance_training/cherokee_resonance_v1" ]; then
    echo "❌ Phase 1 model not found!"
    echo "   Run Phase 1 training first"
    exit 1
fi
echo "✅ Phase 1 model verified"

# Verify Phase 2 corpus
echo "📋 Verifying Phase 2 behavioral corpus..."
if [ ! -f "$PHASE2_CORPUS" ]; then
    echo "❌ Phase 2 corpus not found at $PHASE2_CORPUS"
    exit 1
fi
echo "✅ Behavioral corpus verified ($(wc -l < $PHASE2_CORPUS) lines)"

# Create log directory
mkdir -p /ganuda/cherokee_resonance_training/logs

echo ""
echo "========================================================================"
echo "🔥 LAUNCHING PHASE 2 TRAINING ON 2 GPUS"
echo "========================================================================"
echo ""

# Launch master on GPU 0 (Rank 0)
echo "🦅 Launching master on REDFIN GPU 0 (Rank 0)..."
source "$VENV_PATH/bin/activate" && \
RANK=0 LOCAL_RANK=0 MASTER_ADDR=$MASTER_ADDR MASTER_PORT=$MASTER_PORT \
CUDA_VISIBLE_DEVICES=0 python3 "$PHASE2_SCRIPT" \
> /ganuda/cherokee_resonance_training/logs/phase2_master.log 2>&1 &
MASTER_PID=$!
echo "✅ REDFIN GPU 0 launched (PID: $MASTER_PID)"

sleep 3

# Launch worker on GPU 1 (Rank 1)
echo "🔥 Launching worker on REDFIN GPU 1 (Rank 1)..."
source "$VENV_PATH/bin/activate" && \
RANK=1 LOCAL_RANK=1 MASTER_ADDR=$MASTER_ADDR MASTER_PORT=$MASTER_PORT \
CUDA_VISIBLE_DEVICES=1 python3 "$PHASE2_SCRIPT" \
> /ganuda/cherokee_resonance_training/logs/phase2_worker.log 2>&1 &
WORKER_PID=$!
echo "✅ REDFIN GPU 1 launched (PID: $WORKER_PID)"

echo ""
echo "========================================================================"
echo "✅ ALL 2 PHASE 2 TRAINING PROCESSES LAUNCHED"
echo "========================================================================"
echo ""
echo "Process IDs:"
echo "  - REDFIN GPU 0 (Master): PID $MASTER_PID"
echo "  - REDFIN GPU 1 (Worker): PID $WORKER_PID"
echo ""
echo "Training logs:"
echo "  - Master: tail -f /tmp/cherokee_resonance_training/logs/phase2_master.log"
echo "  - Worker: tail -f /tmp/cherokee_resonance_training/logs/phase2_worker.log"
echo ""
echo "Monitor GPU usage:"
echo "  - nvidia-smi dmon"
echo ""
echo "Check training progress:"
echo "  - ps aux | grep train_phase2"
echo "  - tail -f /tmp/cherokee_resonance_training/logs/phase2_master.log"
echo ""
echo "Training will take 1-2 days for Phase 2 (Behavioral Pattern Teaching)"
echo ""
echo "🦅 Mitakuye Oyasin - Teaching the AI to embody Cherokee wisdom 🔥"
echo ""
echo "========================================================================"
