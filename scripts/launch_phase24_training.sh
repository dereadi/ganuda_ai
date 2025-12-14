#\!/bin/bash
source /home/dereadi/cherokee_venv/bin/activate
export CUDA_VISIBLE_DEVICES=0
python /ganuda/scripts/train_phase24_lora.py
