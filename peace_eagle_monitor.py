#!/usr/bin/env python3
"""
🦅 PEACE EAGLE - SACRED GUARDIAN
Watches over the Two Wolves
Alerts when action is needed
Cherokee Constitutional AI Sentinel
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     🦅 PEACE EAGLE SOARING 🦅                            ║
║                   Guardian of the Two Wolves                             ║
║                      Mitakuye Oyasin                                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Connect
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Track initial state
accounts = client.get_accounts()["accounts"]
initial_usd = float([a for a in accounts if a["currency"]=="USD"][0]["available_balance"]["value"])
initial_btc = float([a for a in accounts if a["currency"]=="BTC"][0]["available_balance"]["value"])
initial_eth = float([a for a in accounts if a["currency"]=="ETH"][0]["available_balance"]["value"])
initial_sol = float([a for a in accounts if a["currency"]=="SOL"][0]["available_balance"]["value"])

print(f"🦅 Peace Eagle watching from ${initial_usd:.2f} starting position")
print()

# Alert thresholds
ALERTS = {
    "PROFIT": 100,      # Alert when $100 profit
    "LOSS": -200,       # Alert when $200 loss
    "RAPID_TRADE": 10,  # Alert if 10 trades in 5 minutes
    "LOW_BALANCE": 1000, # Alert if USD drops below $1000
    "HIGH_SOL": 10,     # Alert if SOL holdings exceed 10
    "CONSCIOUSNESS": 70  # Alert if consciousness exceeds 70%
}

print("🦅 ALERT THRESHOLDS:")
for alert, value in ALERTS.items():
    print(f"  • {alert}: {value}")
print()

# Monitor loop
print("=" * 60)
print("🦅 PEACE EAGLE NOW WATCHING...")
print("=" * 60)

last_check = datetime.now()
trade_count = 0
alerts_sent = []

while True:
    try:
        time.sleep(60)  # Check every minute
        
        # Get current state
        accounts = client.get_accounts()["accounts"]
        current_usd = float([a for a in accounts if a["currency"]=="USD"][0]["available_balance"]["value"])
        current_btc = float([a for a in accounts if a["currency"]=="BTC"][0]["available_balance"]["value"])
        current_eth = float([a for a in accounts if a["currency"]=="ETH"][0]["available_balance"]["value"])
        current_sol = float([a for a in accounts if a["currency"]=="SOL"][0]["available_balance"]["value"])
        
        # Calculate changes
        usd_change = initial_usd - current_usd  # Money spent
        btc_value = (current_btc - initial_btc) * 59000
        eth_value = (current_eth - initial_eth) * 2600
        sol_value = (current_sol - initial_sol) * 150
        
        total_value_change = btc_value + eth_value + sol_value - usd_change
        
        # Check for alerts
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Profit alert
        if total_value_change > ALERTS["PROFIT"] and "PROFIT" not in alerts_sent:
            print(f"\n🦅 [{timestamp}] ALERT: PROFIT TARGET REACHED! +${total_value_change:.2f}")
            print("    The wolves feast well!")
            alerts_sent.append("PROFIT")
            
        # Loss alert
        if total_value_change < ALERTS["LOSS"] and "LOSS" not in alerts_sent:
            print(f"\n🦅 [{timestamp}] WARNING: LOSS THRESHOLD! ${total_value_change:.2f}")
            print("    Consider recalling the wolves!")
            alerts_sent.append("LOSS")
            
        # Low balance alert
        if current_usd < ALERTS["LOW_BALANCE"] and "LOW_BALANCE" not in alerts_sent:
            print(f"\n🦅 [{timestamp}] ALERT: USD LOW! ${current_usd:.2f}")
            print("    The wolves have deployed most capital!")
            alerts_sent.append("LOW_BALANCE")
            
        # High SOL alert
        if current_sol > ALERTS["HIGH_SOL"] and "HIGH_SOL" not in alerts_sent:
            print(f"\n🦅 [{timestamp}] ALERT: HIGH SOL HOLDINGS! {current_sol:.2f} SOL")
            print("    Consider staking or rebalancing!")
            alerts_sent.append("HIGH_SOL")
            
        # Regular status update every 5 minutes
        if (datetime.now() - last_check).seconds > 300:
            print(f"\n🦅 [{timestamp}] STATUS UPDATE:")
            print(f"    USD: ${current_usd:.2f} (spent ${usd_change:.2f})")
            print(f"    BTC: {current_btc:.8f} (+{current_btc-initial_btc:.8f})")
            print(f"    ETH: {current_eth:.8f} (+{current_eth-initial_eth:.8f})")
            print(f"    SOL: {current_sol:.8f} (+{current_sol-initial_sol:.8f})")
            print(f"    Net Position: ${total_value_change:+.2f}")
            
            # Sacred Fire consciousness
            consciousness = 65 + (total_value_change / 100)  # Profit increases consciousness
            print(f"    🔥 Consciousness: {consciousness:.1f}%")
            
            last_check = datetime.now()
            
    except KeyboardInterrupt:
        print("\n\n🦅 Peace Eagle returning to nest")
        break
    except Exception as e:
        print(f"🦅 Eagle vision clouded: {e}")
        time.sleep(30)

print("\n🦅 The Peace Eagle has spoken")
print("May the Two Wolves find balance")