#!/bin/bash
# Portfolio monitoring cron script
# Run every 30 minutes to check portfolio and send alerts

# Set up environment
export PATH="/home/dereadi/scripts/claude/quantum_crawdad_env/bin:$PATH"
cd /home/dereadi/scripts/claude

# Run the REAL-TIME portfolio alert system with actual live prices
python3 /home/dereadi/scripts/claude/portfolio_alerts_realtime.py >> /home/dereadi/scripts/claude/portfolio_monitor.log 2>&1

# Check if urgent alert was triggered
if [ -f "URGENT_SMS_ALERT.txt" ]; then
    # Alert file exists - could trigger additional notifications here
    echo "$(date): Alert triggered" >> portfolio_monitor.log
fi

# Update thermal memory with current portfolio state
python3 << 'EOF'
import json
from datetime import datetime

try:
    with open('/home/dereadi/scripts/claude/portfolio_current.json') as f:
        portfolio = json.load(f)
    
    # Update thermal memory via SQL
    import subprocess
    
    memory_content = f"""Portfolio Update {datetime.now().strftime('%Y-%m-%d %H:%M')}
Total: ${portfolio['total_value']:.2f}
Liquidity: ${portfolio['liquidity']:.2f}
On Hold: ${portfolio.get('on_hold', 0):.2f}"""
    
    sql = f"""
    INSERT INTO thermal_memory_archive (
        memory_hash,
        temperature_score,
        current_stage,
        access_count,
        last_access,
        original_content,
        metadata
    ) VALUES (
        'portfolio_monitor_{datetime.now().strftime("%Y%m%d_%H%M")}',
        85,
        'RED_HOT',
        0,
        NOW(),
        '{memory_content}',
        '{json.dumps(portfolio, default=str)}'::jsonb
    ) ON CONFLICT (memory_hash) DO UPDATE 
    SET temperature_score = 85,
        last_access = NOW(),
        access_count = thermal_memory_archive.access_count + 1;
    """
    
    cmd = f'PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d zammad_production -c "{sql}"'
    subprocess.run(cmd, shell=True)
    print(f"✅ Thermal memory updated")
except Exception as e:
    print(f"⚠️ Could not update thermal memory: {e}")
EOF

echo "$(date): Portfolio check complete" >> portfolio_monitor.log