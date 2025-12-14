#!/bin/bash
################################################################################
# Memory Jr. LoRA Training Launch Script
# Fractal Brain Architecture - Phase 1 POC
# Cherokee Council JRs
################################################################################

source /home/dereadi/cherokee_venv/bin/activate
export CUDA_VISIBLE_DEVICES=0

# Fix CUDA memory fragmentation (suggested by PyTorch error)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

python3 /ganuda/scripts/train_memory_jr_lora.py
