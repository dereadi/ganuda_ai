#!/bin/bash
source /ganuda/config/secrets.env
# Trigger IT Triad ITSM Evaluation
# Run this on redfin to start the evaluation

echo "================================================"
echo "IT TRIAD ITSM EVALUATION - STARTING"
echo "================================================"
echo

# Check if running as dereadi
if [ "$(whoami)" != "dereadi" ]; then
    echo "ERROR: Must run as dereadi user"
    exit 1
fi

# Stop existing IT Triad daemon
echo "1. Stopping IT Triad daemon..."
IT_PID=$(pgrep -f "it_triad_cli.py --pm")
if [ -n "$IT_PID" ]; then
    echo "   Found IT Triad daemon (PID: $IT_PID)"
    kill $IT_PID
    sleep 3
    echo "   ✅ Daemon stopped"
else
    echo "   No daemon running"
fi

# Read task from thermal memory
echo ""
echo "2. Reading task assignment from thermal memory..."
TASK=$(PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -U claude -d triad_federation -t -A -c "
SELECT content
FROM triad_shared_memories
WHERE content ILIKE '%HIGH PRIORITY TASK ASSIGNMENT - IT MANAGEMENT TRIAD%'
ORDER BY created_at DESC
LIMIT 1;
")

if [ -z "$TASK" ]; then
    echo "   ERROR: Could not find task assignment in thermal memory"
    exit 1
fi

echo "   ✅ Task assignment found ($(echo "$TASK" | wc -c) characters)"
echo ""

# Read evaluation guidance
echo "3. Reading comprehensive evaluation guidance..."
GUIDANCE=$(cat /Users/Shared/ganuda/IT_TRIAD_ITSM_PROMPT.txt)
if [ -z "$GUIDANCE" ]; then
    echo "   ERROR: Could not find IT_TRIAD_ITSM_PROMPT.txt"
    exit 1
fi
echo "   ✅ Evaluation guidance loaded"
echo ""

# Combine into full prompt
FULL_PROMPT="$TASK

════════════════════════════════════════════════════════════════════════════════

$GUIDANCE"

# Save prompt to temp file
PROMPT_FILE="/tmp/it_triad_itsm_evaluation_$(date +%Y%m%d_%H%M%S).txt"
echo "$FULL_PROMPT" > "$PROMPT_FILE"
echo "4. Full prompt saved to: $PROMPT_FILE"
echo ""

# Start IT Triad interactively
echo "5. Starting IT Triad in interactive mode..."
echo ""
echo "================================================"
echo "IT TRIAD IS NOW LOADING..."
echo "================================================"
echo ""

cd /home/dereadi
source cherokee_venv/bin/activate

# Run IT Triad and feed the prompt
echo "$FULL_PROMPT" | python3 it_triad/it_triad_cli.py

echo ""
echo "================================================"
echo "IT TRIAD EVALUATION COMPLETE"
echo "================================================"
echo ""
echo "Check thermal memory for results:"
echo "  tags: ['itsm', 'investigation', 'phase1']"
echo "  tags: ['itsm', 'requirements', 'phase2']"
echo "  tags: ['itsm', 'options_analysis', 'recommendation']"
echo ""

