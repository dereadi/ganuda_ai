#!/bin/bash
# Run Presidential Behavior Analysis
# Cherokee AI Federation - For Seven Generations

cd /ganuda/jr_executor
source /home/dereadi/cherokee_venv/bin/activate

echo "Starting Presidential Behavior Analysis..."
python3 analyze_presidents.py

echo ""
echo "Analysis complete. Checking results..."
ls -la /ganuda/data/presidential_study/analysis/

echo ""
echo "Pattern Summary:"
cat /ganuda/data/presidential_study/analysis/pattern_summary.json | python3 -m json.tool