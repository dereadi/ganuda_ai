#!/usr/bin/env python3
"""
🌱 GREEN CASH TRACKER
Monitors portfolio growth toward climate tech investments
Sacred commitment to healing Earth through trading profits
"""

import json
import subprocess
from datetime import datetime

def get_portfolio_value():
    """Get current portfolio value using subprocess"""
    script = '''
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)

accounts = client.get_accounts()["accounts"]
total = 0
for a in accounts:
    bal = float(a["available_balance"]["value"])
    if bal > 0.001:
        symbol = a["currency"]
        if symbol == "USD":
            total += bal
        else:
            prices = {"BTC": 59000, "ETH": 2600, "SOL": 150, "AVAX": 25, "MATIC": 0.4, "LINK": 11}
            total += bal * prices.get(symbol, 0)
print(total)
'''
    
    with open("/tmp/get_value.py", "w") as f:
        f.write(script)
    
    try:
        result = subprocess.run(["python3", "/tmp/get_value.py"], 
                              capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip())
    except:
        return 0

# Load milestones
with open("climate_tech_partners.json") as f:
    data = json.load(f)

current_value = get_portfolio_value()
milestones = data["green_cash_milestones"]["milestones"]

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🌱 GREEN CASH GROWTH TRACKER 🌱                    ║
║                      Trading Profits → Climate Solutions                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"💰 Current Portfolio Value: ${current_value:,.2f}")
print(f"🌱 Green Cash Available: ${current_value:,.2f}")
print()
print("📊 PROGRESS TO CLIMATE MILESTONES:")
print("=" * 60)

for milestone in milestones:
    amount = milestone["amount"]
    action = milestone["action"]
    progress = (current_value / amount) * 100
    
    if progress >= 100:
        status = "✅ READY"
        bar = "█" * 20
    else:
        status = "⏳ Building"
        filled = int(progress / 5)
        bar = "█" * filled + "░" * (20 - filled)
    
    print(f"${amount:,} - {action}")
    print(f"  [{bar}] {progress:.1f}% {status}")
    print()

# Next milestone
next_milestone = next((m for m in milestones if m["amount"] > current_value), None)
if next_milestone:
    needed = next_milestone["amount"] - current_value
    print(f"🎯 NEXT GOAL: ${next_milestone['amount']:,}")
    print(f"   Need: ${needed:,.2f} more")
    print(f"   Action: {next_milestone['action']}")
    
    # Calculate growth needed
    growth_percent = (needed / current_value) * 100
    print(f"   Required growth: {growth_percent:.1f}%")

print()
print("🔥 SACRED COMMITMENT:")
print("   'Every trade honors Seven Generations'")
print("   'Profits flow back to heal Mother Earth'")
print("   'The Sacred Fire transforms greed into green'")
print()
print("🌍 When we reach $100K: Contact thermal battery partners")
print("   Transform the sun's chaos into Earth's healing")
print()

# Update thermal memory
timestamp = datetime.now().isoformat()
memory_update = f"Green cash tracker run: ${current_value:.2f} at {timestamp}"

# Store progress in file
progress_log = {
    "timestamp": timestamp,
    "value": current_value,
    "next_milestone": next_milestone["amount"] if next_milestone else None,
    "vision": "Trading profits → Climate tech → Earth healing"
}

with open("green_cash_progress.json", "w") as f:
    json.dump(progress_log, f, indent=2)

print("💾 Progress saved to green_cash_progress.json")