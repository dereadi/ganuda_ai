#!/bin/bash
# Launch Phase 2.3 Weighted LoRA Training - Synthesis Jr's Bayesian Prior Fix

source /home/dereadi/cherokee_venv/bin/activate

export CUDA_VISIBLE_DEVICES=0

python /ganuda/scripts/train_phase23_weighted_lora.py 2>&1 | tee /ganuda/phase23_weighted_training.log
