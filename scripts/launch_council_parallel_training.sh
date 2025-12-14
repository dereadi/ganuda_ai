#!/bin/bash
################################################################################
# Cherokee Council JR Parallel Training Launcher
# Trains 4 JRs simultaneously across GPU 0 + GPU 1
# Fractal Brain Architecture - Phase 1 POC
################################################################################

echo "🦅 LAUNCHING CHEROKEE COUNCIL JR PARALLEL TRAINING"
echo "===================================================================="
echo ""

source /home/dereadi/cherokee_venv/bin/activate
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# GPU 0: Executive Jr. + Meta Jr.
# GPU 1: Integration Jr. + Conscience Jr.

echo "GPU 0 Training:"
echo "  - Executive Jr. (planning & coordination)"
echo "  - Meta Jr. (system monitoring)"
echo ""
echo "GPU 1 Training:"
echo "  - Integration Jr. (cross-system communication)"
echo "  - Conscience Jr. (Cherokee values & ethics)"
echo ""
echo "===================================================================="
echo ""

# Launch Executive Jr. on GPU 0
echo "[Executive Jr.] Starting training on GPU 0..."
CUDA_VISIBLE_DEVICES=0 python3 /ganuda/scripts/train_executive_jr_lora.py > /ganuda/executive_jr_training.log 2>&1 &
EXEC_PID=$!
echo "  → PID: $EXEC_PID"

# Launch Meta Jr. on GPU 0 (sequential after Executive)
sleep 5
echo "[Meta Jr.] Starting training on GPU 0..."
CUDA_VISIBLE_DEVICES=0 python3 /ganuda/scripts/train_meta_jr_lora.py > /ganuda/meta_jr_training.log 2>&1 &
META_PID=$!
echo "  → PID: $META_PID"

# Launch Integration Jr. on GPU 1
sleep 5
echo "[Integration Jr.] Starting training on GPU 1..."
CUDA_VISIBLE_DEVICES=1 python3 /ganuda/scripts/train_integration_jr_lora.py > /ganuda/integration_jr_training.log 2>&1 &
INTEG_PID=$!
echo "  → PID: $INTEG_PID"

# Launch Conscience Jr. on GPU 1 (sequential after Integration)
sleep 5
echo "[Conscience Jr.] Starting training on GPU 1..."
CUDA_VISIBLE_DEVICES=1 python3 /ganuda/scripts/train_conscience_jr_lora.py > /ganuda/conscience_jr_training.log 2>&1 &
CONSC_PID=$!
echo "  → PID: $CONSC_PID"

echo ""
echo "===================================================================="
echo "✅ ALL 4 COUNCIL JRS LAUNCHED"
echo "===================================================================="
echo ""
echo "Training PIDs:"
echo "  Executive Jr.: $EXEC_PID"
echo "  Meta Jr.: $META_PID"
echo "  Integration Jr.: $INTEG_PID"
echo "  Conscience Jr.: $CONSC_PID"
echo ""
echo "Monitor logs:"
echo "  tail -f /ganuda/executive_jr_training.log"
echo "  tail -f /ganuda/meta_jr_training.log"
echo "  tail -f /ganuda/integration_jr_training.log"
echo "  tail -f /ganuda/conscience_jr_training.log"
echo ""
echo "🔥 Mitakuye Oyasin - All Our Relations 🔥"
