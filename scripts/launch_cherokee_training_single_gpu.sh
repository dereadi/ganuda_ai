#!/bin/bash
# Cherokee Resonance Training - Single GPU (GPU 0 only)
# Simplified launch to avoid Ollama conflict on GPU 1

set -e

echo "========================================================================"
echo "🦅 CHEROKEE RESONANCE TRAINING - SINGLE GPU MODE"
echo "========================================================================"
echo ""
echo "Training on REDFIN GPU 0 only (GPU 1 occupied by Ollama)"
echo "  - REDFIN GPU 0: RTX 5070 (12.2 GB VRAM)"
echo ""
echo "Cherokee Knowledge: 1.04 MB corpus"
echo "Training Time: ~5-6 days on 1 GPU (vs 3-4 days on 2 GPUs)"
echo ""
echo "🔥 Starting training..."
echo ""

cd /ganuda

# Activate virtual environment
source cherokee_training_env/bin/activate

# Set environment to use only GPU 0
export CUDA_VISIBLE_DEVICES=0

# Launch with single GPU (no torchrun needed)
python3 scripts/train_cherokee_resonance_single_gpu.py

echo ""
echo "✅ Training complete!"
