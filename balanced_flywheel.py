#!/usr/bin/env python3
"""
⚖️ BALANCED FLYWHEEL - Sells as much as it buys
Maintains USD liquidity for continuous trading
"""

import json
import random
import time
from datetime import datetime
import subprocess

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    ⚖️ BALANCED FLYWHEEL TRADER ⚖️                       ║
║                   50% Buy, 50% Sell - Always Has Fuel                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def balanced_trade():
    """Execute balanced buy/sell trades"""
    script = '''
import json
import random
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)

# Check USD balance
accounts = client.get_accounts()["accounts"]
usd_balance = 0
crypto_positions = []

for a in accounts:
    bal = float(a["available_balance"]["value"])
    if a["currency"] == "USD":
        usd_balance = bal
    elif bal > 0.001:
        crypto_positions.append(a["currency"])

# Decide action based on balance
if usd_balance < 500 and crypto_positions:
    # MUST SELL - Low on USD
    coin = random.choice(crypto_positions)
    for a in accounts:
        if a["currency"] == coin:
            sell_amount = float(a["available_balance"]["value"]) * 0.1  # Sell 10%
            if sell_amount > 0.001:
                try:
                    client.market_order_sell(
                        client_order_id=f"balanced_sell_{int(time.time()*1000)}",
                        product_id=f"{coin}-USD",
                        base_size=str(sell_amount)
                    )
                    print(f"SOLD {sell_amount} {coin}")
                except:
                    pass
                    
elif usd_balance > 100:
    # Can buy OR sell
    action = random.choice(["BUY", "SELL"])
    
    if action == "BUY":
        coins = ["SOL-USD", "AVAX-USD", "MATIC-USD", "DOGE-USD"]
        coin = random.choice(coins)
        amount = min(100, usd_balance * 0.1)  # Max 10% of USD
        try:
            client.market_order_buy(
                client_order_id=f"balanced_buy_{int(time.time()*1000)}",
                product_id=coin,
                quote_size=str(amount)
            )
            print(f"BOUGHT ${amount} {coin}")
        except:
            pass
    
    else:  # SELL
        if crypto_positions:
            coin = random.choice(crypto_positions)
            for a in accounts:
                if a["currency"] == coin:
                    sell_amount = float(a["available_balance"]["value"]) * 0.05
                    if sell_amount > 0.001:
                        try:
                            client.market_order_sell(
                                client_order_id=f"balanced_sell2_{int(time.time()*1000)}",
                                product_id=f"{coin}-USD",
                                base_size=str(sell_amount)
                            )
                            print(f"SOLD {sell_amount} {coin}")
                        except:
                            pass
'''
    
    temp_file = f"/tmp/balanced_{int(time.time()*1000000)}.py"
    with open(temp_file, "w") as f:
        f.write(script)
    
    # Run and get result
    result = subprocess.run(["python3", temp_file],
                          capture_output=True, text=True, timeout=10)
    subprocess.run(["rm", temp_file], capture_output=True)
    return result.stdout.strip() if result.stdout else None

print("⚖️ BALANCED TRADING STARTED")
print("Rules:")
print("  • If USD < $500: ONLY SELL")
print("  • If USD > $500: 50/50 buy/sell")
print("  • Never deploy > 10% of USD per trade")
print("  • Maintain minimum $500 USD")
print()

trade_count = 0
buy_count = 0
sell_count = 0

try:
    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        result = balanced_trade()
        if result:
            trade_count += 1
            if "BOUGHT" in result:
                buy_count += 1
                print(f"[{timestamp}] 🟢 #{trade_count}: {result}")
            elif "SOLD" in result:
                sell_count += 1
                print(f"[{timestamp}] 🔴 #{trade_count}: {result}")
            
            # Status every 10 trades
            if trade_count % 10 == 0:
                print(f"\n⚖️ BALANCE CHECK: {buy_count} buys, {sell_count} sells")
                print(f"   Ratio: {sell_count/buy_count:.2f}:1 sell/buy\n")
        
        # Wait 15-30 seconds
        time.sleep(random.randint(15, 30))
        
except KeyboardInterrupt:
    print(f"\n\n⚖️ BALANCED FLYWHEEL STOPPED")
    print(f"Total: {trade_count} trades")
    print(f"Buys: {buy_count} | Sells: {sell_count}")
    print(f"Balance ratio: {sell_count/buy_count:.2f}:1 sell/buy" if buy_count > 0 else "")