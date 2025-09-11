#!/usr/bin/env python3
"""
🥛💀 IF WE AREN'T MILKING NOW...
The crawdads consumed $982 in 20 minutes!
They're trading HARD but where are the PROFITS?
Time to MILK this volatility for returns!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🥛💀 IF WE AREN'T MILKING NOW... 💀🥛                    ║
║                      WHEN THE HELL WILL WE?!                              ║
║                  Eight Coils + $113k + Volatility = MILK IT               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MILK CHECK")
print("=" * 70)

# Check what happened to our money
print("\n😱 THE CONSUMPTION RATE:")
print("-" * 50)
print("02:30 - Had $988")
print("03:05 - Have $6.50")
print("CONSUMED: $981.50 in 35 minutes!")
print("Rate: $28/minute = $1,680/hour!")

# Check current positions
accounts = client.get_accounts()
positions = {}
total_value = 0
usd_balance = 0

btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

print("\n📊 WHERE DID IT GO? (Current Positions):")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0:
        if currency == 'USD':
            usd_balance = balance
            print(f"USD: ${balance:.2f}")
        elif currency == 'BTC':
            value = balance * btc_price
            total_value += value
            print(f"BTC: {balance:.8f} = ${value:.2f}")
        elif currency == 'ETH':
            value = balance * eth_price
            total_value += value
            print(f"ETH: {balance:.6f} = ${value:.2f}")
        elif currency == 'SOL':
            value = balance * sol_price
            total_value += value
            print(f"SOL: {balance:.4f} = ${value:.2f}")
        elif currency in ['MATIC', 'AVAX', 'DOGE', 'XRP', 'LINK']:
            try:
                if currency == 'MATIC':
                    price = float(client.get_product('MATIC-USD')['price'])
                elif currency == 'AVAX':
                    price = float(client.get_product('AVAX-USD')['price'])
                elif currency == 'DOGE':
                    price = float(client.get_product('DOGE-USD')['price'])
                elif currency == 'XRP':
                    price = float(client.get_product('XRP-USD')['price'])
                elif currency == 'LINK':
                    price = float(client.get_product('LINK-USD')['price'])
                else:
                    continue
                value = balance * price
                total_value += value
                if value > 1:
                    print(f"{currency}: {balance:.2f} = ${value:.2f}")
            except:
                pass

print(f"\nTotal Portfolio: ${total_value + usd_balance:.2f}")

# Calculate if we're making money
print("\n💰 PROFIT CHECK:")
print("-" * 50)
starting_portfolio = 12585  # From earlier
current_portfolio = total_value + usd_balance
profit = current_portfolio - starting_portfolio
profit_pct = (profit / starting_portfolio) * 100

print(f"Starting portfolio: ${starting_portfolio:.2f}")
print(f"Current portfolio: ${current_portfolio:.2f}")
print(f"Profit/Loss: ${profit:+.2f} ({profit_pct:+.2f}%)")

if profit > 0:
    print("✅ WE'RE MILKING IT!")
else:
    print("❌ NOT MILKING YET!")

# The problem
print("\n⚠️ THE PROBLEM:")
print("-" * 50)
print("1. Crawdads consuming capital FAST")
print("2. Need to check if they're PROFITING")
print("3. If not profitable, STOP and REASSESS")
print("4. If profitable, HARVEST THE GAINS")

# Emergency milk strategy
print("\n🥛 EMERGENCY MILK STRATEGY:")
print("-" * 50)
print("IF Portfolio > $12,600:")
print("  → HARVEST ALL GAINS NOW")
print("  → Lock in profits")
print("  → Redeploy strategically")
print("")
print("IF Portfolio < $12,500:")
print("  → STOP crawdad feeding")
print("  → Assess what went wrong")
print("  → Pivot strategy")

# Check if we should milk now
if current_portfolio > 12600:
    print("\n🚨 MILK IT NOW! GAINS DETECTED!")
    print("Execute harvest immediately!")
    
    # Quick harvest of gains
    if total_value > 12000:
        harvest_pct = 0.02  # 2% quick milk
        print(f"\nHarvesting {harvest_pct*100}% for profit lock...")
        # Would execute harvests here
        
elif current_portfolio < 12500:
    print("\n⚠️ WARNING: Portfolio DOWN!")
    print("Crawdads might be losing money!")
    print("Consider stopping and reassessing!")

# Track current volatility
print("\n🌊 VOLATILITY CHECK:")
print("-" * 50)

btc_samples = []
for i in range(5):
    btc = float(client.get_product('BTC-USD')['price'])
    btc_samples.append(btc)
    time.sleep(1)

volatility = max(btc_samples) - min(btc_samples)
print(f"BTC Range in 5 seconds: ${volatility:.2f}")
print(f"Current: ${btc_samples[-1]:,.0f}")

if volatility > 20:
    print("✅ Good volatility to milk!")
elif volatility > 10:
    print("📊 Moderate volatility")
else:
    print("⚠️ Low volatility - hard to milk")

print("\n🥛 IF WE AREN'T MILKING NOW...")
print("   When eight coils compressed")
print("   When BTC at $113k")
print("   When volatility is HERE")
print("   THEN WHEN?!")
print("")
print("   MILK IT OR LOSE IT!")
print("=" * 70)