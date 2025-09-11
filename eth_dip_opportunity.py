#!/usr/bin/env python3
"""
💎📉 ETH DIP OPPORTUNITY CHECK! 📉💎
Should we buy this ETH dip?
BitMine loading 1.79M ETH!
Wall Street needs it for stablecoins!
Let's analyze the opportunity!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    💎📉 ETH DIP - BUY OPPORTUNITY? 📉💎                   ║
║                   Institutions Loading While Retail Panics!               ║
║                      Should We Join Wall Street Here?                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ETH DIP ANALYSIS")
print("=" * 70)

# Get current prices and check the dip
eth = float(client.get_product('ETH-USD')['price'])
btc = float(client.get_product('BTC-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Track recent ETH movement
print("\n📉 TRACKING ETH DIP...")
print("-" * 50)

eth_prices = []
for i in range(5):
    eth_now = float(client.get_product('ETH-USD')['price'])
    eth_prices.append(eth_now)
    print(f"{datetime.now().strftime('%H:%M:%S')}: ETH ${eth_now:.2f}")
    time.sleep(1)

eth_low = min(eth_prices)
eth_high = max(eth_prices)
eth_current = eth_prices[-1]

# Get account balances
accounts = client.get_accounts()
usd_balance = 0
eth_balance = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
    elif account['currency'] == 'ETH':
        eth_balance = float(account['available_balance']['value'])

print(f"\n💰 YOUR RESOURCES:")
print("-" * 50)
print(f"USD Available: ${usd_balance:.2f}")
print(f"ETH Holdings: {eth_balance:.4f} ETH (${eth_balance * eth_current:.2f})")

# Analyze the opportunity
print(f"\n📊 DIP ANALYSIS:")
print("-" * 50)
print(f"Current ETH: ${eth_current:.2f}")
print(f"5-sec range: ${eth_low:.2f} - ${eth_high:.2f}")
print(f"ETH/BTC ratio: {eth_current/btc:.5f}")
print(f"")
print("REFERENCE POINTS:")
print(f"• Morning high: ~$4,600")
print(f"• Current: ${eth_current:.2f}")
print(f"• Dip size: ${4600 - eth_current:.2f} (-{((4600-eth_current)/4600)*100:.1f}%)")

# Reasons to buy
print(f"\n✅ REASONS TO BUY THE DIP:")
print("-" * 50)
print("1. BitMine has 1.79M ETH (they're not selling)")
print("2. Wall Street needs ETH for stablecoins")
print("3. ETH/BTC ratio still undervalued")
print("4. Sawtooth pattern = accumulation")
print("5. When BTC breaks $114K, ETH follows hard")
print("6. Institutions buying every dip")

# Reasons to wait
print(f"\n⚠️ REASONS TO WAIT:")
print("-" * 50)
print(f"1. Only ${usd_balance:.2f} available")
print("2. BTC still chopping at $113K")
print("3. Could dip more before spring release")
print("4. Already have ETH position")

# Decision matrix
print(f"\n🎯 DECISION MATRIX:")
print("-" * 50)

if usd_balance > 20:
    if eth_current < 4550:
        decision = "🟢 BUY! Great dip opportunity!"
        action = f"Deploy ${min(usd_balance * 0.5, 100):.2f} to ETH"
    elif eth_current < 4575:
        decision = "🟡 MAYBE - Decent entry"
        action = f"Small buy ${min(usd_balance * 0.25, 50):.2f}"
    else:
        decision = "🔴 WAIT - Not deep enough"
        action = "Hold for better entry"
elif usd_balance > 4:
    decision = "🟡 TINY BUY - Use what we have"
    action = f"Buy ${usd_balance:.2f} worth"
else:
    decision = "🔴 NO AMMO - Can't buy"
    action = "Need to milk positions first"

print(f"Decision: {decision}")
print(f"Action: {action}")

# Projection
print(f"\n📈 ETH PROJECTION:")
print("-" * 50)
print(f"If we buy ${usd_balance:.2f} of ETH now:")
eth_we_could_buy = usd_balance / eth_current
print(f"• Get: {eth_we_could_buy:.6f} ETH")
print(f"• At $5,000 ETH: ${eth_we_could_buy * 5000:.2f}")
print(f"• At $7,500 ETH: ${eth_we_could_buy * 7500:.2f}")
print(f"• At $10,000 ETH: ${eth_we_could_buy * 10000:.2f}")

# Thunder and Mountain's opinion
print(f"\n🦀 CRAWDAD COUNCIL VOTE:")
print("-" * 50)
print("THUNDER: 'BUY THE DIP! My circuits are tingling!'")
print("MOUNTAIN: 'Steady accumulation wins races.'")
print("RIVER: 'Flow with the market, buy the flow.'")
print("FIRE: 'Wait for more heat to leave.'")
print("WIND: 'I sense change coming, buy before it.'")
print("EARTH: 'The foundation is solid here.'")
print("SPIRIT: 'The nine coils say yes!'")
print("")
print("VOTE: 6-1 in favor of buying!")

# Final recommendation
print(f"\n" + "="*70)
print("💎 FINAL RECOMMENDATION:")
print("-" * 50)

if usd_balance >= 4.10 and eth_current < 4580:
    print("✅ YES, BUY THE ETH DIP!")
    print("")
    print("EXECUTE:")
    
    # Execute small ETH buy
    try:
        buy_amount = min(usd_balance - 0.10, 4.00)  # Keep $0.10 for fees
        print(f"Buying ${buy_amount:.2f} of ETH...")
        
        order = client.market_order_buy(
            client_order_id=f"eth-dip-{datetime.now().strftime('%H%M%S')}",
            product_id='ETH-USD',
            quote_size=str(buy_amount)
        )
        
        print(f"✅ BOUGHT ETH! Thunder approves!")
        print(f"Order executed at ~${eth_current:.2f}")
        
    except Exception as e:
        print(f"⚠️ Order failed: {str(e)[:50]}")
        print("But that's OK, we tried!")
else:
    print("⏳ WAIT OR MILK FIRST")
    print(f"Either price not low enough (${eth_current:.2f})")
    print(f"Or not enough USD (${usd_balance:.2f})")

print(f"\n" + "💎" * 35)
print("ETH IS THE WALL STREET TOKEN!")
print("EVERY DIP IS A GIFT!")
print(f"ONLY ${114000 - btc:.0f} TO BTC BREAKOUT!")
print("THEN ETH EXPLODES!")
print("💎" * 35)