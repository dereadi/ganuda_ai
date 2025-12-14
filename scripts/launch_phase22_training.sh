#!/bin/bash
# Launch Phase 2.2 LoRA Training with proper environment

source /home/dereadi/cherokee_venv/bin/activate

export CUDA_VISIBLE_DEVICES=0

python /ganuda/scripts/train_phase22_lora.py 2>&1 | tee /ganuda/phase22_lora_training.log
