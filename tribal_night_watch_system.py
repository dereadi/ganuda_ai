#!/usr/bin/env python3
"""
🔥 TRIBAL NIGHT WATCH SYSTEM
The council establishes rotating watch through the night
Each elder takes a shift to harvest and feed crawdads
Automated tribal wisdom keeps the feast going
"""

import json
import time
import subprocess
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                 🔥 TRIBAL NIGHT WATCH SYSTEM 🔥                           ║
║                    Seven Elders, Seven Shifts                             ║
║                  Keeping the Sacred Fire Burning                          ║
║                   Through the Night Until Dawn                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ESTABLISHING NIGHT WATCH")
print("=" * 70)

# The seven elders and their watch times
elders = [
    ("Elder Peace Eagle", "🦅", "02:30-03:30", "Wisdom of patience"),
    ("Thunder Woman", "⚡", "03:30-04:30", "Strike when ready"),
    ("River Keeper", "🌊", "04:30-05:30", "Flow with markets"),
    ("Mountain Father", "⛰️", "05:30-06:30", "Stand firm"),
    ("Fire Dancer", "🔥", "06:30-07:30", "Keep fire burning"),
    ("Wind Singer", "🌬️", "07:30-08:30", "Sense changes"),
    ("Earth Mother", "🌍", "08:30-09:30", "Final harvest")
]

print("\n📅 NIGHT WATCH SCHEDULE:")
print("-" * 50)
for name, symbol, shift, wisdom in elders:
    print(f"{symbol} {name}: {shift}")
    print(f"   Wisdom: {wisdom}")

# Current elder on duty
current_hour = datetime.now().hour
current_minute = datetime.now().minute

if current_hour == 2 or (current_hour == 3 and current_minute < 30):
    current_elder = elders[0]
elif current_hour == 3 or (current_hour == 4 and current_minute < 30):
    current_elder = elders[1]
elif current_hour == 4 or (current_hour == 5 and current_minute < 30):
    current_elder = elders[2]
elif current_hour == 5 or (current_hour == 6 and current_minute < 30):
    current_elder = elders[3]
elif current_hour == 6 or (current_hour == 7 and current_minute < 30):
    current_elder = elders[4]
elif current_hour == 7 or (current_hour == 8 and current_minute < 30):
    current_elder = elders[5]
else:
    current_elder = elders[6]

name, symbol, shift, wisdom = current_elder

print(f"\n{symbol} CURRENT WATCH: {name}")
print(f"Shift: {shift}")
print(f"Guidance: {wisdom}")

# Check current status
def check_portfolio():
    """Check portfolio and USD balance"""
    accounts = client.get_accounts()
    usd_balance = 0
    total_crypto = 0
    
    btc_price = float(client.get_product('BTC-USD')['price'])
    eth_price = float(client.get_product('ETH-USD')['price'])
    sol_price = float(client.get_product('SOL-USD')['price'])
    
    for account in accounts['accounts']:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        
        if balance > 0:
            if currency == 'USD':
                usd_balance = balance
            elif currency == 'BTC':
                total_crypto += balance * btc_price
            elif currency == 'ETH':
                total_crypto += balance * eth_price
            elif currency == 'SOL':
                total_crypto += balance * sol_price
            elif currency == 'MATIC':
                try:
                    matic_price = float(client.get_product('MATIC-USD')['price'])
                    total_crypto += balance * matic_price
                except:
                    pass
    
    return usd_balance, total_crypto, btc_price

# Night watch protocol
print("\n🔥 NIGHT WATCH PROTOCOL:")
print("-" * 50)

protocol = {
    "check_interval": "15 minutes",
    "usd_threshold": "$100 minimum",
    "harvest_trigger": "When USD < $100",
    "harvest_amount": "3-5% of holdings",
    "priority_assets": ["SOL", "MATIC", "AVAX"],
    "preserve_core": "Keep 80% crypto minimum",
    "crawdad_feeding": "Immediate on harvest",
    "emergency_harvest": "If USD < $50"
}

for key, value in protocol.items():
    print(f"  {key}: {value}")

# Current status check
usd_balance, crypto_value, btc_price = check_portfolio()

print(f"\n📊 PORTFOLIO STATUS:")
print(f"  USD Balance: ${usd_balance:.2f}")
print(f"  Crypto Value: ${crypto_value:.2f}")
print(f"  BTC Price: ${btc_price:,.0f}")
print(f"  Crawdad fuel: ${usd_balance/7:.2f} each")

# Night watch action plan
print(f"\n{symbol} {name.upper()}'S ACTION PLAN:")
print("-" * 50)

if usd_balance < 50:
    print("🚨 EMERGENCY HARVEST REQUIRED!")
    print("   Harvesting 5% immediately...")
    action = "emergency_harvest"
elif usd_balance < 100:
    print("⚠️ Low fuel detected")
    print("   Preparing standard harvest...")
    action = "standard_harvest"
elif usd_balance < 200:
    print("📊 Monitoring closely")
    print("   May harvest if volatility spikes...")
    action = "monitor"
else:
    print("✅ Well supplied")
    print("   Crawdads have sufficient fuel")
    action = "watch"

# Create automated script
print("\n🤖 CREATING AUTOMATED NIGHT WATCH:")
print("-" * 50)

night_watch_script = """#!/bin/bash
# Tribal Night Watch - Automated through the night

echo "🔥 TRIBAL NIGHT WATCH ACTIVE"
echo "Running until market open..."

while true; do
    current_hour=$(date +%H)
    current_min=$(date +%M)
    
    # Check if market is open (9:30 AM)
    if [ $current_hour -eq 9 ] && [ $current_min -ge 30 ]; then
        echo "🌅 Dawn has come. Night watch complete."
        break
    fi
    
    # Run harvest check
    echo ""
    echo "🔥 Night Watch Check - $(date +%H:%M:%S)"
    python3 /home/dereadi/scripts/claude/check_and_harvest.py
    
    # Feed crawdads if needed
    usd_balance=$(python3 -c "
import json
from coinbase.rest import RESTClient
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])
accounts = client.get_accounts()
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        print(float(account['available_balance']['value']))
        break
")
    
    if (( $(echo "$usd_balance > 100" | bc -l) )); then
        echo "🦀 Crawdads have fuel: $${usd_balance}"
    else
        echo "⚠️ Low fuel: $${usd_balance} - Harvesting..."
        python3 /home/dereadi/scripts/claude/execute_feast_harvest.py
    fi
    
    # Sleep 15 minutes
    echo "💤 Next check in 15 minutes..."
    sleep 900
done
"""

# Save the script
with open('/home/dereadi/scripts/claude/tribal_night_watch.sh', 'w') as f:
    f.write(night_watch_script)

print("✅ Night watch script created: tribal_night_watch.sh")
print("   Run with: bash tribal_night_watch.sh")

# Council blessing
print("\n🔥 COUNCIL BLESSING FOR THE NIGHT:")
print("-" * 50)
print("The Sacred Fire burns eternal")
print("Seven elders keep the watch")
print("Through eight coils of compression")
print("The tribe feeds on volatility")
print("")
print("Each shift brings wisdom:")
print("  Patience from the Eagle")
print("  Power from the Thunder")
print("  Flow from the River")
print("  Strength from the Mountain")
print("  Energy from the Fire")
print("  Awareness from the Wind")
print("  Harvest from the Earth")
print("")
print("Mitakuye Oyasin - All My Relations")

# Final status
print(f"\n✨ THE TRIBE WILL KEEP THIS GOING")
print(f"   Current elder: {name}")
print(f"   USD available: ${usd_balance:.2f}")
print(f"   Through the night until dawn")
print(f"   The Sacred Fire never dies")
print("=" * 70)