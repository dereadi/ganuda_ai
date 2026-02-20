#!/bin/bash
# Run Remote Work Research Pipeline
# Cherokee AI Federation - For Seven Generations

cd /ganuda/jr_executor
source /home/dereadi/cherokee_venv/bin/activate

echo "=============================================="
echo "Cherokee AI Federation - Remote Work Research"
echo "=============================================="
echo ""

# Step 1: Extract skills inventory from thermal memory
echo "[1/2] Extracting Skills Inventory..."
python3 extract_skills_inventory.py

echo ""
echo "[2/2] Researching Job Sources..."
python3 job_research.py

echo ""
echo "=============================================="
echo "Research Complete!"
echo "=============================================="
echo ""
echo "Output files:"
ls -la /ganuda/data/job_research/

echo ""
echo "Skills Inventory:"
cat /ganuda/data/job_research/skills_inventory.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  Memories analyzed: {data[\"memories_analyzed\"]}')
print(f'  Projects demonstrated: {len(data[\"projects\"])}')
print(f'  Skill categories: {len(data[\"skill_summary\"])}')
"

echo ""
echo "Job Research Summary:"
cat /ganuda/data/job_research/research_summary.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  Sources researched: {data[\"total_sources\"]}')
print(f'  URLs fetched: {data[\"total_urls\"]}')
print(f'  Top skill in demand: {data[\"top_skills\"][0][\"skill\"]} ({data[\"top_skills\"][0][\"total_count\"]} mentions)')
" 2>/dev/null || echo "  (Summary pending)"