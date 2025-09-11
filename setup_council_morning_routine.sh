#!/bin/bash
# Setup daily council wake-up routine with cron

echo "🌅 Setting up Cherokee AI Council Morning Routine"
echo "================================================="

# Create the morning routine script
cat > /home/dereadi/scripts/claude/council_morning_routine.sh << 'EOF'
#!/bin/bash
# Cherokee AI Council Morning Routine
# Runs every day at 8:00 AM to prep for markets

cd /home/dereadi/scripts/claude

# 1. Wake up and check system health
echo "🌅 Council waking up at $(date)"

# 2. Run daily briefing
python3 council_daily_briefing.py > daily_briefing_$(date +%Y%m%d).log 2>&1

# 3. Check portfolio status
python3 check_portfolio_now.py >> daily_briefing_$(date +%Y%m%d).log 2>&1

# 4. Check solar weather impact on trading
curl -s 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json' | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
if data and len(data) > 1:
    kp = float(data[-1][1])
    if kp >= 5:
        print('⚡ SOLAR STORM WARNING: Kp=' + str(kp))
        print('Adjusting trading parameters for solar interference')
" >> daily_briefing_$(date +%Y%m%d).log 2>&1

# 5. Send summary to Discord if bot is running
if pgrep -f discord_stateful_shell.py > /dev/null; then
    echo "Council briefing complete. Check daily_briefing_$(date +%Y%m%d).log"
fi

# 6. Heat the morning briefing in thermal memory
python3 -c "
import psycopg2, json
from datetime import datetime

conn = psycopg2.connect(
    host='192.168.132.222',
    port=5432,
    user='claude',
    password='jawaseatlasers2',
    database='zammad_production'
)

with conn.cursor() as cur:
    cur.execute('''
        UPDATE thermal_memory_archive 
        SET temperature_score = LEAST(100, temperature_score + 5)
        WHERE metadata->>'type' = 'daily_briefing'
        AND created_at > NOW() - INTERVAL '1 day'
    ''')
    conn.commit()

conn.close()
print('🔥 Morning memories heated')
" 2>/dev/null

echo "✅ Council ready for trading day"
EOF

chmod +x /home/dereadi/scripts/claude/council_morning_routine.sh

# Add to crontab (8:00 AM daily)
echo "Adding to crontab for 8:00 AM daily execution..."

# Check if already in crontab
if crontab -l 2>/dev/null | grep -q "council_morning_routine.sh"; then
    echo "✅ Already in crontab"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 8 * * * /home/dereadi/scripts/claude/council_morning_routine.sh") | crontab -
    echo "✅ Added to crontab for 8:00 AM daily"
fi

echo ""
echo "🌅 COUNCIL MORNING ROUTINE CONFIGURED!"
echo "======================================="
echo "• Runs daily at 8:00 AM"
echo "• Checks crypto headlines"
echo "• Monitors world news"
echo "• Analyzes solar weather"
echo "• Reviews portfolio"
echo "• Stores in thermal memory"
echo ""
echo "Manual run: ./council_morning_routine.sh"
echo "Check cron: crontab -l"
echo ""
echo "🔥 The council will wake informed every day!"