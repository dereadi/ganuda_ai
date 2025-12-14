#!/bin/bash
# PHASE 3: Launch Cherokee Constitutional AI Ultimate Training
# Research-backed LoRA approach with 1000-step targeting

echo "🦅 Cherokee Constitutional AI - Phase 3 Training"
echo ""
echo "Research-Backed Approach:"
echo "  - Clean base model (Llama 3.1 8B Instruct)"
echo "  - 589 balanced scenarios (49.1% behavioral + 50.9% knowledge)"
echo "  - 1000-step training target"
echo "  - Checkpoint sampling every 200 steps"
echo "  - Target: 80%+ regression pass rate"
echo ""
echo "Cherokee Jr. Wisdom: 'Slow is steady, steady is fast'"
echo ""

# Activate venv
source /home/dereadi/cherokee_venv/bin/activate

# Set GPU
export CUDA_VISIBLE_DEVICES=0

# Launch training
python /ganuda/scripts/train_phase3_lora.py 2>&1 | tee /ganuda/phase3_lora_training.log
