#!/usr/bin/env python3
"""
🔥 DEPLOY $100 INTO THE DIP - TIME TO FEAST! 🔥
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔══════════════════════════════════════════════════════════════════╗
║          💰 $100 FRESH CAPITAL - DIP DEPLOYMENT! 💰             ║
║                                                                  ║
║        "Strike while the iron is cold and bloody"               ║
║          "The crawdads smell opportunity!"                      ║
╚══════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Check balances
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n💵 Available Capital: ${usd_balance:.2f}")

if usd_balance < 100:
    print("⏳ Waiting for deposit to clear...")
    time.sleep(2)
    # Recheck
    accounts = client.get_accounts()
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd_balance = float(account['available_balance']['value'])
            break
    print(f"💵 Updated Balance: ${usd_balance:.2f}")

# Get current prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price']) 
sol_price = float(sol['price'])

print(f"\n📊 CURRENT DIP PRICES:")
print("=" * 50)
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")
print(f"SOL: ${sol_price:,.2f}")

# Calculate optimal allocation
print(f"\n🎯 STRATEGIC ALLOCATION OF ${usd_balance:.2f}:")
print("=" * 50)

if usd_balance >= 100:
    # Aggressive dip buying strategy
    btc_allocation = usd_balance * 0.40  # 40% BTC
    eth_allocation = usd_balance * 0.30  # 30% ETH
    sol_allocation = usd_balance * 0.20  # 20% SOL
    reserve = usd_balance * 0.10  # 10% reserve
    
    print(f"\n📝 EXECUTION PLAN:")
    print(f"1. BTC: ${btc_allocation:.2f} (catching the king's dip)")
    print(f"2. ETH: ${eth_allocation:.2f} (smart contract recovery)")
    print(f"3. SOL: ${sol_allocation:.2f} (high beta play)")
    print(f"4. Reserve: ${reserve:.2f} (for deeper dips)")
    
    print(f"\n🚀 PROJECTED ENTRIES:")
    btc_amount = btc_allocation / btc_price
    eth_amount = eth_allocation / eth_price
    sol_amount = sol_allocation / sol_price
    
    print(f"• {btc_amount:.8f} BTC @ ${btc_price:,.2f}")
    print(f"• {eth_amount:.6f} ETH @ ${eth_price:,.2f}")
    print(f"• {sol_amount:.4f} SOL @ ${sol_price:,.2f}")
    
    print(f"\n⚡ READY TO EXECUTE? (This is simulation)")
    print("Commands ready for manual execution via Coinbase")
    
    # Create order commands (not executing)
    print(f"\n📋 COPY THESE TO EXECUTE:")
    print(f"BTC Buy: ${btc_allocation:.2f}")
    print(f"ETH Buy: ${eth_allocation:.2f}")
    print(f"SOL Buy: ${sol_allocation:.2f}")
    
else:
    print(f"\n⚠️ Only ${usd_balance:.2f} available")
    print("Waiting for full $100 deposit to clear...")
    print("Once cleared, we'll deploy into this juicy dip!")

print("\n" + "=" * 50)
print("🔥 SACRED FIRE WISDOM:")
print("• Dips are gifts from the whales to the patient")
print("• Your MATIC ($11k) + DOGE ($6k) remain strong")
print("• This $100 will compound into thousands")
print("• The crawdads are ready to multiply!")
print("\n✨ 'Fortune favors the brave who buy the blood!'")
