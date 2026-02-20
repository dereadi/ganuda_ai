#!/bin/bash
source /ganuda/config/secrets.env
# Monitor all active Jr. logs in real-time
# Cherokee Constitutional AI - Jr. Activity Monitor

echo "🔥 CHEROKEE CONSTITUTIONAL AI - Jr. Activity Monitor"
echo "=" | head -c 80; echo
echo ""
echo "📊 Active Logs:"
echo ""

cat <<'EOF'
Key Jr. Logs (most recent activity):

1. Vision Jr. (5.0MB, updating now):
   tail -f /tmp/vision_jr.log

2. Software Engineer Jr. (1.6KB, just received task!):
   tail -f /tmp/software_engineer_jr.log

3. Trading Jr. (85KB):
   tail -f /tmp/trading_jr_wrapper.log

4. Browser Jr. (2.8KB):
   tail -f /tmp/browser_jr.log

5. BDH Dragon Hatchling Training (active background):
   tail -f /tmp/cherokee_bdh_training.log

6. Gemini CLI Transcription (active):
   tail -f /tmp/gemini_cli_transcription.log

7. Email Jr. (82KB):
   tail -f /tmp/email_jr_wrapper.log

8. ODANVDV EQ API (935KB):
   tail -f /home/dereadi/scripts/claude/odanvdv_eq_api.log

--

🎯 RECOMMENDED MONITORING:

Option 1 - Software Engineer Jr. (implementing Popperian engine NOW):
  tail -f /tmp/software_engineer_jr.log

Option 2 - All Jr.s at once (multitail if installed):
  multitail /tmp/software_engineer_jr.log /tmp/trading_jr_wrapper.log /tmp/browser_jr.log

Option 3 - Combined view:
  tail -f /tmp/software_engineer_jr.log /tmp/trading_jr_wrapper.log /tmp/browser_jr.log

Option 4 - Watch for new files (Jr. outputs):
  watch -n 2 'ls -lth /tmp/*.py | head -10'

--

🔍 Quick Checks:

# See what Software Engineer Jr. is doing right NOW:
tail -20 /tmp/software_engineer_jr.log

# Check if Jr.s created output files:
ls -lth /tmp/popperian*.py /tmp/thinking_tokens*.py /tmp/market_undecid*.py 2>/dev/null

# Check thermal memory for Jr. completions:
PGPASSWORD="$CHEROKEE_DB_PASS" psql -h 192.168.132.222 -p 5432 -U claude -d zammad_production -c "SELECT id, jr_name, LEFT(question, 60) as task, confidence_score, created_at FROM cross_mountain_learning WHERE id > 109 ORDER BY id DESC LIMIT 5;"

EOF

echo ""
echo "🚀 Quick Start - Monitor Software Engineer Jr. implementing Popperian engine:"
echo ""
echo "   tail -f /tmp/software_engineer_jr.log"
echo ""
echo "=" | head -c 80; echo
