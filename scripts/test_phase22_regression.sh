#!/bin/bash
# Test Phase 2.2 with reformatted corpus

source /home/dereadi/cherokee_venv/bin/activate

export CUDA_VISIBLE_DEVICES=0

# Update the test script to use Phase 2.2 model
sed 's/phase21_lora/phase22_lora/g' /ganuda/scripts/test_phase21_regression.py > /ganuda/scripts/test_phase22_regression.py
sed -i 's/PHASE 2.1/PHASE 2.2/g' /ganuda/scripts/test_phase22_regression.py
sed -i 's/Phase 2.1/Phase 2.2/g' /ganuda/scripts/test_phase22_regression.py
sed -i 's/phase21_regression/phase22_regression/g' /ganuda/scripts/test_phase22_regression.py

python /ganuda/scripts/test_phase22_regression.py 2>&1 | tee /ganuda/phase22_regression_testing.log
