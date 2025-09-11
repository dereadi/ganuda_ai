#!/bin/bash
# Guardian Process Monitor - Updated by Council

# Check critical processes
PROCESSES=(
    "quantum_crawdad_live_trader.py"
    "council_auto_milker_spongy_throttle.py"
    "solar_storm_trading_strategy.py"
    "greeks_moon_mission_bot.py"
)

LOG_FILE="/home/dereadi/scripts/claude/logs/guardian.log"

echo "[$(date)] Guardian checking processes..." >> $LOG_FILE

for process in "${PROCESSES[@]}"; do
    if ! pgrep -f "$process" > /dev/null; then
        echo "[$(date)] WARNING: $process not running!" >> $LOG_FILE
        
        # Restart critical processes
        if [ "$process" == "council_auto_milker_spongy_throttle.py" ]; then
            echo "[$(date)] Restarting Council Milker..." >> $LOG_FILE
            cd /home/dereadi/scripts/claude
            nohup python3 $process > /dev/null 2>&1 &
            echo "[$(date)] Council Milker restarted with PID $!" >> $LOG_FILE
        fi
    else
        echo "[$(date)] ✓ $process is running" >> $LOG_FILE
    fi
done

# Check USD balance for milking opportunities
python3 - << 'EOF'
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

accounts = client.get_accounts()
usd_balance = 0
for a in accounts['accounts']:
    if a['currency'] == 'USD':
        usd_balance = float(a['available_balance']['value'])
        break

if usd_balance < 50:
    print(f"[Guardian] Low USD: ${usd_balance:.2f} - Milker should activate!")
else:
    print(f"[Guardian] USD healthy: ${usd_balance:.2f}")
EOF
