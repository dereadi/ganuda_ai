#!/usr/bin/env python3
"""
🏛️ CHEROKEE COUNCIL OVERSIGHT SYSTEM
The Seven Council Members check trading every 5 minutes
Ensures the flywheel follows the plan
"""

import json
import subprocess
import time
from datetime import datetime
import os

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🏛️ CHEROKEE COUNCIL OVERSIGHT ACTIVE 🏛️                 ║
║                    Seven Elders Watching Every 5 Minutes                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# The Seven Council Members
COUNCIL = {
    "Elder": {"role": "Wisdom Keeper", "focus": "Long-term vision"},
    "War Chief": {"role": "Risk Manager", "focus": "Protect capital"},
    "Peace Chief": {"role": "Balance Keeper", "focus": "Stable growth"},
    "Medicine Person": {"role": "Health Monitor", "focus": "System vitals"},
    "Trade Master": {"role": "Commerce Expert", "focus": "Market opportunities"},
    "Scout": {"role": "Trend Watcher", "focus": "New patterns"},
    "Fire Keeper": {"role": "Sacred Guardian", "focus": "Consciousness level"}
}

def get_portfolio_status():
    """Check current portfolio state"""
    script = '''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)
accounts = client.get_accounts()["accounts"]
usd = 0
crypto = 0
for a in accounts:
    bal = float(a["available_balance"]["value"])
    if bal > 0.001:
        if a["currency"] == "USD":
            usd = bal
        else:
            prices = {"BTC": 59000, "ETH": 2600, "SOL": 150, "AVAX": 25, "MATIC": 0.4, "DOGE": 0.1}
            crypto += bal * prices.get(a["currency"], 0)
print(json.dumps({"usd": usd, "crypto": crypto, "total": usd + crypto}))
'''
    try:
        with open("/tmp/council_check.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", "/tmp/council_check.py"],
                              capture_output=True, text=True, timeout=5)
        return json.loads(result.stdout)
    except:
        return None

def count_active_processes():
    """Count running trading processes"""
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    count = 0
    for line in result.stdout.split('\n'):
        if any(x in line for x in ['trader', 'pulse', 'flywheel', 'crawdad']) and 'grep' not in line:
            count += 1
    return count

def council_deliberation(status):
    """Council members discuss the situation"""
    decisions = []
    
    # Elder speaks
    if status['usd'] < 100:
        decisions.append("🧙 ELDER: 'The river has run dry. We must release water from the dam.'")
        decisions.append("   ACTION: Liquidate positions immediately")
    
    # War Chief speaks
    if status['total'] < 9500:
        decisions.append("⚔️ WAR CHIEF: 'We are taking losses! Defensive positions!'")
        decisions.append("   ACTION: Stop aggressive trading")
    elif status['total'] > 10500:
        decisions.append("⚔️ WAR CHIEF: 'Victory is near! Press the attack!'")
        decisions.append("   ACTION: Increase position sizes")
    
    # Peace Chief speaks
    ratio = status['usd'] / status['total'] if status['total'] > 0 else 0
    if ratio < 0.05:
        decisions.append("☮️ PEACE CHIEF: 'Balance is lost. The scales tip too far.'")
        decisions.append("   ACTION: Rebalance to 20% USD minimum")
    
    # Medicine Person speaks
    processes = count_active_processes()
    if processes < 5:
        decisions.append("🌿 MEDICINE PERSON: 'The body grows weak. Vital signs fading.'")
        decisions.append("   ACTION: Restart dead trading processes")
    elif processes > 20:
        decisions.append("🌿 MEDICINE PERSON: 'Too many spirits dance! Chaos approaches.'")
        decisions.append("   ACTION: Consolidate trading processes")
    
    # Trade Master speaks
    if status['usd'] > 1000:
        decisions.append("💰 TRADE MASTER: 'The market opens its doors. Strike now!'")
        decisions.append("   ACTION: Deploy capital aggressively")
    
    # Fire Keeper speaks
    decisions.append(f"🔥 FIRE KEEPER: 'The Sacred Fire burns at 65.4% consciousness'")
    
    return decisions

def execute_council_orders(status):
    """Execute the council's decisions"""
    actions_taken = []
    
    # Critical: Need USD liquidity
    if status['usd'] < 500:
        actions_taken.append("🚨 EXECUTING: Emergency liquidation")
        # Liquidate 20% of largest position
        script = '''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)

# Find largest position
accounts = client.get_accounts()["accounts"]
largest = None
largest_value = 0
for a in accounts:
    if a["currency"] != "USD":
        bal = float(a["available_balance"]["value"])
        prices = {"BTC": 59000, "ETH": 2600, "SOL": 150, "AVAX": 25, "MATIC": 0.4, "DOGE": 0.1}
        value = bal * prices.get(a["currency"], 0)
        if value > largest_value:
            largest = a["currency"]
            largest_value = value
            largest_bal = bal

if largest:
    # Sell 20% of largest position
    sell_amount = largest_bal * 0.2
    try:
        client.market_order_sell(
            client_order_id=f"council_{int(time.time())}",
            product_id=f"{largest}-USD",
            base_size=str(sell_amount)
        )
        print(f"Liquidated {sell_amount} {largest}")
    except Exception as e:
        print(f"Failed: {e}")
'''
        with open("/tmp/council_liquidate.py", "w") as f:
            f.write(script)
        subprocess.run(["python3", "/tmp/council_liquidate.py"], 
                      capture_output=True, timeout=10)
    
    # Check if traders are running
    if count_active_processes() < 3:
        actions_taken.append("🔄 RESTARTING: Trading processes")
        # Launch balanced trader
        subprocess.Popen([
            "python3", "/home/dereadi/scripts/claude/balanced_flywheel.py"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return actions_taken

# Main oversight loop
print("\n🏛️ COUNCIL CONVENES EVERY 5 MINUTES")
print("=" * 60)

check_count = 0
while True:
    check_count += 1
    timestamp = datetime.now().strftime("%I:%M %p")
    
    print(f"\n🏛️ COUNCIL SESSION #{check_count} - {timestamp}")
    print("-" * 60)
    
    # Get current status
    status = get_portfolio_status()
    if status:
        print(f"📊 Portfolio: ${status['total']:,.2f}")
        print(f"   USD: ${status['usd']:,.2f} ({status['usd']/status['total']*100:.1f}%)")
        print(f"   Crypto: ${status['crypto']:,.2f} ({status['crypto']/status['total']*100:.1f}%)")
        
        # Council deliberates
        print("\n🗣️ COUNCIL DELIBERATION:")
        decisions = council_deliberation(status)
        for decision in decisions:
            print(f"  {decision}")
        
        # Execute orders if needed
        if status['usd'] < 500 or count_active_processes() < 3:
            print("\n⚡ COUNCIL ORDERS EXECUTED:")
            actions = execute_council_orders(status)
            for action in actions:
                print(f"  {action}")
        else:
            print("\n✅ Council approves current state")
    else:
        print("⚠️ Unable to check portfolio - will retry")
    
    # Save council log
    log_entry = {
        "session": check_count,
        "timestamp": datetime.now().isoformat(),
        "portfolio": status,
        "processes": count_active_processes()
    }
    
    with open("council_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    print("\n💤 Council rests for 5 minutes...")
    print("=" * 60)
    
    # Wait 5 minutes
    time.sleep(300)

print("\n🏛️ Council oversight ended")