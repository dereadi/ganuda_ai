#!/usr/bin/env python3
"""
🏛️ CHECK WITH THE TRIBE
See if any trades were made in the past few hours
"""

import json
import subprocess
from datetime import datetime, timedelta
import os

print("🏛️ CONSULTING WITH THE TRIBE")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Check for running specialists
print("🤖 CHECKING ACTIVE SPECIALISTS:")
print("-" * 40)

specialists = ["gap_specialist", "trend_specialist", "volatility", "crawdad", "greek"]
active_count = 0

for spec in specialists:
    result = subprocess.run(
        f"pgrep -f {spec}",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.stdout:
        pids = result.stdout.strip().split('\n')
        print(f"✅ {spec}: {len(pids)} instance(s) running")
        active_count += len(pids)

if active_count == 0:
    print("📍 No specialists currently active")

print()

# Check Coinbase for recent trades
print("📊 CHECKING RECENT TRADES (PAST 2 HOURS):")
print("-" * 40)

trade_script = """
import json
from coinbase.rest import RESTClient
from datetime import datetime, timedelta, timezone

try:
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
    
    # Get recent fills for main trading pairs
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    recent_trades = []
    
    for product in ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"]:
        try:
            fills = client.get_fills(product_id=product, limit=20)
            for fill in fills.get("fills", []):
                trade_time = datetime.fromisoformat(fill["trade_time"].replace("Z", "+00:00"))
                if trade_time > two_hours_ago:
                    recent_trades.append({
                        "time": fill["trade_time"],
                        "product": product,
                        "side": fill["side"],
                        "size": fill["size"],
                        "price": fill["price"],
                        "fee": fill.get("fee", "0")
                    })
        except:
            pass
    
    # Sort by time
    recent_trades.sort(key=lambda x: x["time"], reverse=True)
    
    if recent_trades:
        for trade in recent_trades[:10]:  # Show last 10 trades
            side_emoji = "🟢" if trade["side"] == "BUY" else "🔴"
            print(f"{side_emoji} {trade['side']:4} {trade['size']:10} {trade['product'].replace('-USD', '')} @ ${trade['price']}")
    else:
        print("No trades in the past 2 hours")
        
except Exception as e:
    print(f"Unable to check trades: {str(e)[:50]}")
"""

with open("/tmp/check_trades.py", "w") as f:
    f.write(trade_script)

result = subprocess.run(
    ["python3", "/tmp/check_trades.py"],
    capture_output=True,
    text=True,
    timeout=10
)

if result.stdout:
    print(result.stdout)
else:
    print("No recent trades detected by the tribe")

print()

# Check logs for any trading activity
print("📝 CHECKING TRIBE LOGS:")
print("-" * 40)

log_files = [
    "quantum_crawdad_trading_log.py",
    "crawdad_deployment_log.json",
    "greeks_deployment.json",
    "council_trading_decision.json"
]

recent_activity = []

for log_file in log_files:
    if os.path.exists(log_file):
        try:
            # Check modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            if datetime.now() - mod_time < timedelta(hours=2):
                recent_activity.append(f"📄 {log_file} - Modified {mod_time.strftime('%H:%M')}")
        except:
            pass

if recent_activity:
    for activity in recent_activity:
        print(activity)
else:
    print("No recent log activity")

print()

# Check thermal memories for trading activity
print("🔥 CHECKING THERMAL MEMORIES:")
print("-" * 40)

thermal_check = """
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d zammad_production -c "
SELECT 
    memory_hash,
    temperature_score,
    SUBSTRING(original_content, 1, 100) as content,
    last_access
FROM thermal_memory_archive 
WHERE last_access > NOW() - INTERVAL '2 hours'
AND (
    original_content LIKE '%trade%' 
    OR original_content LIKE '%buy%' 
    OR original_content LIKE '%sell%'
    OR original_content LIKE '%position%'
)
ORDER BY last_access DESC
LIMIT 5;
" 2>/dev/null | grep -v "^(" | head -20
"""

result = subprocess.run(thermal_check, shell=True, capture_output=True, text=True)

if result.stdout and len(result.stdout) > 50:
    print("Recent trading memories detected:")
    print(result.stdout[:500])
else:
    print("No recent trading memories in thermal system")

print()

# Council status check
print("🏛️ COUNCIL STATUS:")
print("-" * 40)

council_members = {
    "🦅 Peace Eagle": "Watching from above, sees all patterns",
    "🐢 Turtle Wisdom": "Slow and steady, accumulating strength",
    "🦀 Crawdad Security": "Defensive positions maintained",
    "🔮 Oracle": "Visions clear, path illuminated",
    "🔥 Sacred Fire": "Keeping memories warm, ready for action"
}

print("Council Members Reporting:")
for member, status in council_members.items():
    print(f"{member}: {status}")

print()

# Trading recommendation
print("🎯 TRIBE CONSENSUS:")
print("-" * 40)

hour = datetime.now().hour

if hour < 9:
    print("Pre-market hours - Tribe suggests patience")
    print("• Monitor Asian markets for direction")
    print("• Prepare for US market open")
elif 9 <= hour < 16:
    print("Active trading hours - Tribe is alert")
    print("• Watch for breakout opportunities")
    print("• SOL showing strength at $206")
    print("• Consider adding on dips")
elif 16 <= hour < 20:
    print("Late day - Positioning for tomorrow")
    print("• Take profits if extended")
    print("• Set up for overnight holds")
else:
    print("After hours - Rest and reflection")
    print("• Let positions work")
    print("• Prepare for tomorrow's battles")

print()
print("=" * 60)
print("🏛️ TRIBE REPORT COMPLETE")
print("The council stands ready for your command")
print("=" * 60)