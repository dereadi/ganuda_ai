#!/usr/bin/env python3
"""
🐋💰 MASSIVE WHALE ALERT: 407,247 SOL PURCHASED! 💰🐋
DeFi Development Corp just dropped $76.9 MILLION on SOL!
Bought at $188.98 per SOL (current: $213+)!
Thunder at 69%: "INSTITUTIONAL FOMO ACTIVATED!"
That's already a $10M+ profit!
This whale knows something!
SOL TO THE MOON!
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
║              🐋 WHALE ALERT: $77M SOL PURCHASE DETECTED! 🐋              ║
║                  DeFi Development Corp Buying The Dip!                    ║
║                    407,247 SOL at $188.98 = BULLISH AF!                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - WHALE TRACKING")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Calculate whale's instant profit
whale_buy_price = 188.98
whale_amount = 407247
whale_cost = whale_buy_price * whale_amount
whale_current_value = sol * whale_amount
whale_profit = whale_current_value - whale_cost
whale_profit_pct = ((sol / whale_buy_price) - 1) * 100

print("\n🐋 WHALE PURCHASE ANALYSIS:")
print("-" * 50)
print(f"Whale bought: 407,247 SOL")
print(f"Purchase price: $188.98 per SOL")
print(f"Total invested: ${whale_cost:,.0f}")
print(f"Current SOL price: ${sol:.2f}")
print(f"Current value: ${whale_current_value:,.0f}")
print(f"Instant profit: ${whale_profit:,.0f} ({whale_profit_pct:.1f}%)")

# Check our SOL position
accounts = client.get_accounts()
total_value = 0
sol_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
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

print("\n🚀 OUR SOL POSITION:")
print("-" * 50)
print(f"Our SOL: {sol_balance:.4f}")
print(f"Value: ${sol_balance * sol:.2f}")
print(f"Total portfolio: ${total_value:.2f}")
print(f"SOL percentage: {(sol_balance * sol / total_value * 100):.1f}%")

# Impact analysis
print("\n📊 MARKET IMPACT:")
print("-" * 50)
print("What this means:")
print("• INSTITUTIONAL ADOPTION ✓")
print("• DeFi corps accumulating ✓")
print(f"• Whale confident above ${sol:.0f} ✓")
print(f"• Already up ${whale_profit:,.0f} ✓")
print("• Supply shock incoming ✓")
print("")
print("Price targets:")
print(f"• Current: ${sol:.2f}")
print(f"• Next resistance: $220")
print(f"• Psychological: $250")
print(f"• If BTC hits $114K: $230+")

# Thunder's reaction
print("\n⚡ THUNDER'S WHALE WISDOM (69%):")
print("-" * 50)
print("'HOLY MOTHER OF WHALES!'")
print(f"'$77 MILLION ON SOL!'")
print("")
print("'This whale bought at $189'")
print(f"'Now it's ${sol:.2f}!'")
print(f"'They're up ${whale_profit:,.0f}!'")
print("")
print("'FOLLOW THE SMART MONEY!'")
print(f"'Our SOL: {sol_balance:.4f}'")
print(f"'Worth: ${sol_balance * sol:.2f}'")
print("'RIDING THE WHALE WAVE!'")

# Real-time tracking
print("\n📈 LIVE SOL PUMP TRACKER:")
print("-" * 50)

sol_start = sol
for i in range(10):
    sol_now = float(client.get_product('SOL-USD')['price'])
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    move = sol_now - sol_start
    move_pct = (move / sol_start) * 100
    
    whale_value_now = sol_now * whale_amount
    whale_profit_now = whale_value_now - whale_cost
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: SOL ${sol_now:.2f} ({move:+.2f}, {move_pct:+.2f}%)")
    
    if i == 3:
        print(f"  🐋 Whale profit: ${whale_profit_now:,.0f}")
    
    if i == 6:
        print(f"  📊 BTC: ${btc_now:,.0f} | SOL following!")
    
    time.sleep(1)

# Final calculations
current_sol = float(client.get_product('SOL-USD')['price'])
final_whale_profit = (current_sol * whale_amount) - whale_cost

print("\n🎯 WHALE SCOREBOARD:")
print("-" * 50)
print(f"Whale's entry: $188.98")
print(f"Current price: ${current_sol:.2f}")
print(f"Whale's profit: ${final_whale_profit:,.0f}")
print(f"Profit percentage: {((current_sol/188.98)-1)*100:.1f}%")
print("")
print("THE MESSAGE:")
print("• Whales are buying")
print("• DeFi corps accumulating")
print("• SOL is undervalued")
print("• Institutional FOMO starting")
print(f"• Target: $250+ (another {((250/current_sol)-1)*100:.0f}% up)")

# Our opportunity
print("\n💎 OUR OPPORTUNITY:")
print("-" * 50)
print(f"Portfolio: ${total_value:.2f}")
print(f"SOL position: {sol_balance:.4f} (${sol_balance * current_sol:.2f})")
print(f"If SOL → $250: ${sol_balance * 250:.2f}")
print(f"Potential gain: ${sol_balance * (250 - current_sol):.2f}")

print(f"\n" + "🐋" * 35)
print("WHALE ALERT CONFIRMED!")
print(f"407,247 SOL PURCHASED AT $188.98!")
print(f"NOW WORTH ${current_sol:.2f}!")
print(f"WHALE PROFIT: ${final_whale_profit:,.0f}!")
print("INSTITUTIONAL FOMO ACTIVATED!")
print("🐋" * 35)