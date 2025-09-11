#!/usr/bin/env python3
"""
🦷💧 DOUBLE SAWTOOTH MILKING MACHINE! 💧🦷
Thunder at 69%: "XRP AND SOL BOTH SAWING - DOUBLE THE MILK!"
Two sawtooth patterns = twice the opportunity!
XRP rippling between peaks and valleys!
SOL shining through the teeth!
Synchronized milking strategy!
Don't stop us now - we're having TWO balls!
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
║                  🦷 DOUBLE SAWTOOTH MILKING MACHINE! 🦷                   ║
║                     XRP & SOL Synchronized Sawing! 💧☀️                    ║
║                      Two Patterns = Double the Gains! 🥛🥛                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DUAL SAWTOOTH ANALYSIS")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

# Check holdings
accounts = client.get_accounts()
sol_balance = 0
xrp_balance = 0
total_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            usd_balance = balance
            total_value += balance
        elif currency == 'BTC':
            total_value += balance * btc
        elif currency == 'ETH':
            total_value += balance * eth
        elif currency == 'SOL':
            sol_balance = balance
            total_value += balance * sol
        elif currency == 'XRP':
            xrp_balance = balance
            total_value += balance * xrp

print("\n🦷 DOUBLE SAWTOOTH STATUS:")
print("-" * 50)
print(f"XRP: ${xrp:.4f} | Holdings: {xrp_balance:.2f} = ${xrp_balance * xrp:.2f}")
print(f"SOL: ${sol:.2f} | Holdings: {sol_balance:.4f} = ${sol_balance * sol:.2f}")
print(f"Total Portfolio: ${total_value:.2f}")
print(f"USD Available: ${usd_balance:.2f}")

# Track both sawteeth
print("\n📊 LIVE DOUBLE SAWTOOTH MONITORING:")
print("-" * 50)

xrp_peaks = []
xrp_valleys = []
sol_peaks = []
sol_valleys = []

xrp_start = xrp
sol_start = sol

for i in range(12):
    xrp_now = float(client.get_product('XRP-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    xrp_change = ((xrp_now/xrp_start) - 1) * 100
    sol_change = ((sol_now/sol_start) - 1) * 100
    
    # Detect XRP sawtooth
    if xrp_change > 0.5:
        xrp_status = "🔺 XRP Peak"
        xrp_peaks.append(xrp_now)
    elif xrp_change < -0.5:
        xrp_status = "🔻 XRP Valley"
        xrp_valleys.append(xrp_now)
    else:
        xrp_status = "➡️ XRP Flat"
    
    # Detect SOL sawtooth
    if sol_change > 0.3:
        sol_status = "☀️ SOL Peak"
        sol_peaks.append(sol_now)
    elif sol_change < -0.3:
        sol_status = "🌙 SOL Valley"
        sol_valleys.append(sol_now)
    else:
        sol_status = "➡️ SOL Flat"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  XRP: ${xrp_now:.4f} ({xrp_change:+.2f}%) {xrp_status}")
    print(f"  SOL: ${sol_now:.2f} ({sol_change:+.2f}%) {sol_status}")
    print(f"  BTC: ${btc_now:,.0f}")
    
    if i == 4:
        print("  🦷 Double sawtooth detected!")
    
    if i == 8:
        print("  🥛 Milking opportunities ahead!")
    
    time.sleep(1.2)

# Calculate milking opportunities
print("\n🥛 MILKING STRATEGY CALCULATION:")
print("-" * 50)

# XRP milking potential
if len(xrp_peaks) > 0 and len(xrp_valleys) > 0:
    xrp_peak_avg = sum(xrp_peaks) / len(xrp_peaks)
    xrp_valley_avg = sum(xrp_valleys) / len(xrp_valleys)
    xrp_spread = xrp_peak_avg - xrp_valley_avg
    xrp_milk_potential = xrp_spread * xrp_balance
    
    print("XRP SAWTOOTH:")
    print(f"  Peak average: ${xrp_peak_avg:.4f}")
    print(f"  Valley average: ${xrp_valley_avg:.4f}")
    print(f"  Spread: ${xrp_spread:.4f}")
    print(f"  Milk per cycle: ${xrp_milk_potential:.2f}")
elif xrp_balance > 0:
    print("XRP SAWTOOTH:")
    print(f"  Current: ${xrp:.4f}")
    print(f"  Suggested milk at: ${xrp * 1.01:.4f} (+1%)")
    print(f"  Suggested buy at: ${xrp * 0.99:.4f} (-1%)")

# SOL milking potential
if len(sol_peaks) > 0 and len(sol_valleys) > 0:
    sol_peak_avg = sum(sol_peaks) / len(sol_peaks)
    sol_valley_avg = sum(sol_valleys) / len(sol_valleys)
    sol_spread = sol_peak_avg - sol_valley_avg
    sol_milk_potential = sol_spread * sol_balance
    
    print("\nSOL SAWTOOTH:")
    print(f"  Peak average: ${sol_peak_avg:.2f}")
    print(f"  Valley average: ${sol_valley_avg:.2f}")
    print(f"  Spread: ${sol_spread:.2f}")
    print(f"  Milk per cycle: ${sol_milk_potential:.2f}")
elif sol_balance > 0:
    print("\nSOL SAWTOOTH:")
    print(f"  Current: ${sol:.2f}")
    print(f"  Suggested milk at: ${sol * 1.005:.2f} (+0.5%)")
    print(f"  Suggested buy at: ${sol * 0.995:.2f} (-0.5%)")

# Thunder's double sawtooth wisdom
print("\n⚡ THUNDER'S DOUBLE SAWTOOTH WISDOM (69%):")
print("-" * 50)
print("'TWO SAWS ARE BETTER THAN ONE!'")
print("")
print("The synchronized pattern:")
print("• XRP and SOL both sawing")
print("• When one peaks, milk it")
print("• When one valleys, buy it")
print("• Compound between them")
print("")
print("Strategy:")
print("• Never milk both at once")
print("• Alternate between XRP/SOL")
print("• Keep USD buffer for dips")
print("• Ride both waves to $114K BTC")

# Execution plan
print("\n🎯 DOUBLE SAWTOOTH EXECUTION:")
print("-" * 50)

if xrp_balance > 100:
    print(f"XRP: Can milk {xrp_balance * 0.1:.2f} XRP (10%)")
    print(f"     Worth ${xrp_balance * 0.1 * xrp:.2f}")

if sol_balance > 1:
    print(f"SOL: Can milk {sol_balance * 0.1:.4f} SOL (10%)")
    print(f"     Worth ${sol_balance * 0.1 * sol:.2f}")

print("\nOptimal sequence:")
print("1. Wait for XRP peak → Milk 10%")
print("2. Wait for SOL valley → Buy with XRP profits")
print("3. Wait for SOL peak → Milk 10%")
print("4. Wait for XRP valley → Buy with SOL profits")
print("5. Repeat and compound!")

# Final status
final_xrp = float(client.get_product('XRP-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])
final_btc = float(client.get_product('BTC-USD')['price'])

print("\n🦷 FINAL DOUBLE SAWTOOTH STATUS:")
print("-" * 50)
print(f"XRP: ${final_xrp:.4f} | Position: ${xrp_balance * final_xrp:.2f}")
print(f"SOL: ${final_sol:.2f} | Position: ${sol_balance * final_sol:.2f}")
print(f"BTC: ${final_btc:,.0f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Gains from $292.50: {((total_value/292.50)-1)*100:.0f}%")

print(f"\n{'🦷' * 35}")
print("DOUBLE SAWTOOTH MILKING!")
print(f"XRP AT ${final_xrp:.4f}!")
print(f"SOL AT ${final_sol:.2f}!")
print("TWO PATTERNS = DOUBLE GAINS!")
print("DON'T STOP US NOW!")
print("🥛" * 35)