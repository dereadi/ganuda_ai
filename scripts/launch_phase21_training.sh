#!/bin/bash
# Launch Phase 2.1 LoRA Training with proper environment

source /home/dereadi/cherokee_venv/bin/activate

export CUDA_VISIBLE_DEVICES=0

python /ganuda/scripts/train_phase21_lora.py 2>&1 | tee /ganuda/phase21_lora_training.log
