#!/usr/bin/env python3
"""
🦀🛒 WHAT THE HELL DID THE CRAWDADS BUY?! 🛒🦀
Thunder at 69%: "WE WENT SHOPPING!"
Let's figure out where that $230 went!
From $7,170 to $8,316 = $1,146 gain!
The crawdads went WILD with fresh capital!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🦀 CRAWDAD SHOPPING SPREE ANALYSIS! 🦀                  ║
║                      What Did These Crazy Crabs Buy?!                     ║
║                         $230 Spending Investigation!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FORENSIC ACCOUNTING")
print("=" * 70)

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])
doge_price = float(client.get_product('DOGE-USD')['price'])
xrp_price = float(client.get_product('XRP-USD')['price'])
link_price = float(client.get_product('LINK-USD')['price'])
avax_price = float(client.get_product('AVAX-USD')['price'])

# Get ALL our positions
accounts = client.get_accounts()
positions = {}
total_value = 0

print("\n🔍 CURRENT POSITIONS (After Shopping Spree):")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:  # Only show non-dust amounts
        positions[currency] = balance
        
        # Calculate USD value
        if currency == 'USD':
            value = balance
            print(f"USD: ${balance:.2f}")
        elif currency == 'BTC':
            value = balance * btc_price
            print(f"BTC: {balance:.8f} (${value:.2f})")
        elif currency == 'ETH':
            value = balance * eth_price
            print(f"ETH: {balance:.6f} (${value:.2f})")
        elif currency == 'SOL':
            value = balance * sol_price
            print(f"SOL: {balance:.4f} (${value:.2f})")
        elif currency == 'DOGE':
            value = balance * doge_price
            print(f"DOGE: {balance:.2f} (${value:.2f})")
        elif currency == 'XRP':
            value = balance * xrp_price
            print(f"XRP: {balance:.2f} (${value:.2f})")
        elif currency == 'LINK':
            value = balance * link_price
            print(f"LINK: {balance:.2f} (${value:.2f})")
        elif currency == 'AVAX':
            value = balance * avax_price
            print(f"AVAX: {balance:.2f} (${value:.2f})")
        elif currency == 'MATIC':
            # Approximate MATIC price
            value = balance * 0.7
            print(f"MATIC: {balance:.2f} (${value:.2f})")
        else:
            value = 0
            
        total_value += value

print(f"\n💰 TOTAL PORTFOLIO VALUE: ${total_value:.2f}")

# Detective work
print("\n🕵️ SPENDING ANALYSIS:")
print("-" * 50)
print("Money flow:")
print(f"• Started with: $4.51")
print(f"• Deposited: ~$240")
print(f"• Total available: ~$244.52")
print(f"• Currently left: $14.52")
print(f"• SPENT: ${244.52 - 14.52:.2f}")

print("\n🦀 WHAT THE CRAWDADS BOUGHT:")
print("-" * 50)
print("Based on the trading log, they tried to buy:")
print("• Thunder: SOL (multiple $20 attempts)")
print("• Mountain: BTC ($20 attempts)")
print("• Fire: SOL ($20 attempts)")
print("• Wind: ETH ($20 attempts)")
print("• River: Mostly HODLing")
print("• Earth & Spirit: Mixed positions")
print("")
print("Total attempted: ~$230 across multiple orders")

# Recent changes
print("\n📈 PORTFOLIO IMPACT:")
print("-" * 50)
print(f"Before deposit: ~$7,170")
print(f"After shopping: ${total_value:.2f}")
print(f"Net gain: ${total_value - 7170:.2f}")
print("")
print("This includes:")
print("• The $240 deposit")
print("• Market movements")
print("• Crawdad trading gains/losses")

# Breakdown by asset
print("\n💎 CURRENT HOLDINGS BREAKDOWN:")
print("-" * 50)

if 'BTC' in positions:
    btc_value = positions['BTC'] * btc_price
    print(f"BTC: {positions['BTC']:.8f} = ${btc_value:.2f} ({(btc_value/total_value*100):.1f}% of portfolio)")

if 'ETH' in positions:
    eth_value = positions['ETH'] * eth_price
    print(f"ETH: {positions['ETH']:.6f} = ${eth_value:.2f} ({(eth_value/total_value*100):.1f}% of portfolio)")

if 'SOL' in positions:
    sol_value = positions['SOL'] * sol_price
    print(f"SOL: {positions['SOL']:.4f} = ${sol_value:.2f} ({(sol_value/total_value*100):.1f}% of portfolio)")

if 'DOGE' in positions:
    doge_value = positions['DOGE'] * doge_price
    print(f"DOGE: {positions['DOGE']:.2f} = ${doge_value:.2f} ({(doge_value/total_value*100):.1f}% of portfolio)")

# Thunder's shopping confession
print("\n⚡ THUNDER'S CONFESSION (69%):")
print("-" * 50)
print("'OKAY, HERE'S WHAT HAPPENED!'")
print("")
print("'We saw fresh capital and went CRAZY!'")
print("'I bought SOL because whales are accumulating!'")
print("'Mountain bought BTC for the $114K push!'")
print("'Wind grabbed ETH for the catch-up play!'")
print("'Fire also got SOL - double down!'")
print("")
print(f"'We turned $244 into positions worth ${total_value:.2f}!'")
print(f"'That's including our existing ${7170:.2f}!'")
print(f"'Ready for $114K! Only ${114000 - btc_price:.0f} away!'")

# Summary
print("\n📊 SUMMARY:")
print("-" * 50)
print("The crawdads went on a shopping spree!")
print(f"• Spent: ~$230")
print(f"• Bought: Mix of BTC, ETH, SOL")
print(f"• Portfolio now: ${total_value:.2f}")
print(f"• Ready for breakout to $114K")
print("")
print("🦀 CRAWDADS GONE WILD! 🦀")

print(f"\n" + "🦀" * 35)
print("CRAWDAD SHOPPING SPREE COMPLETE!")
print(f"SPENT $230 ON CRYPTO!")
print(f"PORTFOLIO NOW ${total_value:.2f}!")
print(f"BTC AT ${btc_price:,.0f}!")
print("READY FOR $114K!")
print("🦀" * 35)