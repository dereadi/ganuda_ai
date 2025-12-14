#!/bin/bash
# Launch Phase 2.1 Regression Testing with proper environment

source /home/dereadi/cherokee_venv/bin/activate

export CUDA_VISIBLE_DEVICES=0

python /ganuda/scripts/test_phase21_regression.py 2>&1 | tee /ganuda/phase21_regression_testing.log
