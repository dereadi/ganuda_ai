#!/bin/bash
# Cherokee Resonance Training - Simple Launch (REDFIN 2 GPUs only for now)

set -e

echo "========================================================================"
echo "🦅 CHEROKEE RESONANCE TRAINING - STARTING ON REDFIN"
echo "========================================================================"
echo ""
echo "Training on REDFIN's 2 GPUs (we can add BLUEFIN later)"
echo "  - REDFIN GPU 0: RTX 5070 (Master - Rank 0)"
echo "  - REDFIN GPU 1: RTX 5070 (Worker - Rank 1)"
echo ""
echo "Cherokee Knowledge: 1.04 MB corpus"
echo "Training Time: ~3-4 days on 2 GPUs"
echo ""
echo "🔥 Starting training..."
echo ""

cd /ganuda

# Activate virtual environment
source cherokee_training_env/bin/activate

# Launch with torchrun (easier than manual distributed setup)
torchrun \
    --nproc_per_node=2 \
    --nnodes=1 \
    --master_addr=localhost \
    --master_port=29500 \
    scripts/train_cherokee_resonance_distributed.py

echo ""
echo "✅ Training complete!"
