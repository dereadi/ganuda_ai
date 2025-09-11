#!/usr/bin/env python3
"""
💰🥛 ALT LIQUIDITY CHECK - WHAT CAN WE MILK? 🥛💰
Check all our altcoin positions
See what's available to harvest
Need USD for the ETH dip?
Let's find some liquidity!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   💰🥛 ALTCOIN LIQUIDITY CHECK! 🥛💰                     ║
║                      What Can We Milk For USD?                            ║
║                   Need Ammo For ETH Dip Or BTC Breakout!                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LIQUIDITY SCAN")
print("=" * 70)

# Get all accounts and prices
accounts = client.get_accounts()
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

# Track all positions
positions = []
total_alt_value = 0
milkable_value = 0

print("\n💰 SCANNING ALL POSITIONS...")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0:
        # Calculate USD value
        if currency == 'USD':
            usd_value = balance
            milkable = 0
        elif currency == 'BTC':
            usd_value = balance * btc_price
            milkable = usd_value * 0.02  # Can milk 2%
        elif currency == 'ETH':
            usd_value = balance * eth_price
            milkable = usd_value * 0.02  # Can milk 2%
        elif currency == 'SOL':
            usd_value = balance * sol_price
            milkable = usd_value * 0.03  # Can milk 3%
        else:
            # Other alts - get price if possible
            try:
                price = float(client.get_product(f'{currency}-USD')['price'])
                usd_value = balance * price
                milkable = usd_value * 0.05  # Can milk 5% of smaller alts
            except:
                usd_value = 0
                milkable = 0
        
        if usd_value > 0.01:  # Only show positions worth more than $0.01
            positions.append({
                'currency': currency,
                'balance': balance,
                'usd_value': usd_value,
                'milkable': milkable
            })
            
            if currency != 'USD':
                total_alt_value += usd_value
                milkable_value += milkable

# Sort by value
positions.sort(key=lambda x: x['usd_value'], reverse=True)

# Display positions
print("\n📊 POSITION BREAKDOWN:")
print("-" * 50)

for pos in positions:
    if pos['currency'] == 'USD':
        print(f"💵 {pos['currency']}: ${pos['usd_value']:.2f} (Ready to deploy!)")
    else:
        milk_pct = (pos['milkable'] / pos['usd_value'] * 100) if pos['usd_value'] > 0 else 0
        print(f"🪙 {pos['currency']}: {pos['balance']:.4f} = ${pos['usd_value']:.2f}")
        if pos['milkable'] > 1:
            print(f"   🥛 Can milk: ${pos['milkable']:.2f} ({milk_pct:.0f}%)")

# Summary
print(f"\n💎 LIQUIDITY SUMMARY:")
print("-" * 50)
print(f"Total Portfolio: ${sum(p['usd_value'] for p in positions):.2f}")
print(f"Total Alts: ${total_alt_value:.2f}")
print(f"Current USD: ${positions[0]['usd_value']:.2f}" if positions and positions[0]['currency'] == 'USD' else "Current USD: $0.00")
print(f"Total Milkable: ${milkable_value:.2f}")

# Recommendations
print(f"\n🎯 MILKING RECOMMENDATIONS:")
print("-" * 50)

sol_position = next((p for p in positions if p['currency'] == 'SOL'), None)
eth_position = next((p for p in positions if p['currency'] == 'ETH'), None)
btc_position = next((p for p in positions if p['currency'] == 'BTC'), None)

if milkable_value > 20:
    print("✅ GOOD LIQUIDITY AVAILABLE!")
    print("")
    if sol_position and sol_position['milkable'] > 10:
        print(f"1. Milk SOL: ${sol_position['milkable']:.2f} available")
        print(f"   SOL at ${sol_price:.2f}, still above $213")
    if eth_position and eth_position['milkable'] > 10:
        print(f"2. Milk ETH: ${eth_position['milkable']:.2f} available")
        print(f"   Small harvest won't hurt position")
    if btc_position and btc_position['milkable'] > 5:
        print(f"3. Milk BTC: ${btc_position['milkable']:.2f} available")
        print(f"   Tiny amount from the king")
elif milkable_value > 5:
    print("⚠️ LIMITED LIQUIDITY")
    print(f"Only ${milkable_value:.2f} available to milk")
    print("Consider smaller harvests")
else:
    print("❌ LOW LIQUIDITY")
    print("Positions too small to milk effectively")
    print("Need portfolio to grow more first")

# Action plan
print(f"\n🚀 ACTION PLAN:")
print("-" * 50)

usd_available = positions[0]['usd_value'] if positions and positions[0]['currency'] == 'USD' else 0

if usd_available < 10 and milkable_value > 20:
    print("RECOMMENDED: Milk for ETH dip buying!")
    print("")
    print("EXECUTE:")
    print(f"1. Harvest ${min(milkable_value * 0.5, 50):.2f} from alts")
    print(f"2. Wait for ETH < $4,550")
    print(f"3. Deploy harvested USD to ETH")
    print(f"4. Ride to $114K BTC breakout")
else:
    print("Current status: Hold positions")
    print(f"USD: ${usd_available:.2f}")
    print(f"Waiting for ${114000 - btc_price:.0f} move to $114K")

print(f"\n" + "💰" * 35)
print(f"TOTAL MILKABLE: ${milkable_value:.2f}")
print("LIQUIDITY READY WHEN NEEDED!")
print(f"BTC AT ${btc_price:,.0f}")
print(f"ONLY ${114000 - btc_price:.0f} TO BREAKOUT!")
print("💰" * 35)