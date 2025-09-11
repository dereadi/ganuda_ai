#!/usr/bin/env python3
"""
🔥😤 SEETHER - FINE AGAIN / DIVERGENCE! 😤🔥
"It seems like every day's the same
And I'm left to discover on my own"
BTC climbing while ETH lags behind!
Thunder at 69%: "The divergence reveals truth!"
The separation before convergence!
"I feel the dream in me expire
And there's no one left to blame it on"
BUT WE'RE GONNA BE FINE AGAIN!
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
║                    🔥 SEETHER - DIVERGENCE DETECTED! 🔥                   ║
║                      BTC Rising, ETH Lagging Behind                       ║
║                        But We'll Be Fine Again!                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DIVERGENCE ANALYSIS")
print("=" * 70)

# Track the divergence
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

ratio_start = eth_start / btc_start

print("\n🔥 INITIAL DIVERGENCE:")
print("-" * 50)
print(f"BTC: ${btc_start:,.0f} (Leading)")
print(f"ETH: ${eth_start:.2f} (Lagging)")
print(f"SOL: ${sol_start:.2f}")
print(f"ETH/BTC Ratio: {ratio_start:.5f}")
print(f"Distance to $114K: ${114000 - btc_start:.0f}")

# Check portfolio in this divergence
accounts = client.get_accounts()
total_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc_start
    elif currency == 'ETH':
        total_value += balance * eth_start
    elif currency == 'SOL':
        total_value += balance * sol_start

print(f"\nPortfolio in divergence: ${total_value:.2f}")

# Track the separation
print("\n😤 TRACKING THE SEPARATION:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    btc_change = ((btc_now - btc_start) / btc_start) * 100
    eth_change = ((eth_now - eth_start) / eth_start) * 100
    divergence = btc_change - eth_change
    ratio_now = eth_now / btc_now
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print("  'It seems like every day's the same'")
        print(f"    BTC: ${btc_now:,.0f} ({btc_change:+.2f}%)")
        print(f"    ETH: ${eth_now:.2f} ({eth_change:+.2f}%)")
        print(f"    Divergence: {divergence:.2f}%")
    elif i == 5:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print("  'And I'm left to discover on my own'")
        print(f"    BTC climbing: ${btc_now:,.0f}")
        print(f"    ETH lagging: ${eth_now:.2f}")
        print(f"    Ratio weakening: {ratio_now:.5f}")
    elif i == 10:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print("  'I feel the dream in me expire'")
        print(f"    But BTC persists: ${btc_now:,.0f}")
        print(f"    ETH will catch up: ${eth_now:.2f}")
        print(f"    Divergence: {divergence:.2f}%")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: BTC ${btc_now:,.0f} | ETH ${eth_now:.2f} | Div: {divergence:.2f}%")
    
    time.sleep(1)

# Thunder's divergence wisdom
print("\n⚡ THUNDER'S DIVERGENCE WISDOM (69%):")
print("-" * 50)
print("'THE SEPARATION BEFORE ELEVATION!'")
print("")
print("Pattern Recognition:")
print("• BTC leads the charge")
print("• ETH follows with delay")
print("• When ETH catches up = EXPLOSION")
print("• This divergence = COILED SPRING")
print("")
print("'IT'S FINE AGAIN!'")
print("'WE'LL BE FINE AGAIN!'")
print(f"'From $292.50 to ${total_value:.2f}!'")
print("'Through every divergence!'")

# Current divergence status
current_btc = float(client.get_product('BTC-USD')['price'])
current_eth = float(client.get_product('ETH-USD')['price'])
current_sol = float(client.get_product('SOL-USD')['price'])
current_ratio = current_eth / current_btc

btc_total_change = ((current_btc - btc_start) / btc_start) * 100
eth_total_change = ((current_eth - eth_start) / eth_start) * 100
total_divergence = btc_total_change - eth_total_change

print("\n📊 DIVERGENCE REPORT:")
print("-" * 50)
print(f"BTC Movement: ${btc_start:,.0f} → ${current_btc:,.0f} ({btc_total_change:+.2f}%)")
print(f"ETH Movement: ${eth_start:.2f} → ${current_eth:.2f} ({eth_total_change:+.2f}%)")
print(f"Total Divergence: {total_divergence:.2f}%")
print(f"ETH/BTC Ratio: {ratio_start:.5f} → {current_ratio:.5f}")
print("")
if total_divergence > 0.1:
    print("Status: BTC LEADING (Bullish)")
    print("Expect: ETH catch-up rally soon")
elif total_divergence < -0.1:
    print("Status: ETH LEADING (Rotation)")
    print("Expect: Alt season brewing")
else:
    print("Status: SYNCHRONIZED")
    print("Expect: Joint movement coming")

# Seether's message
print("\n🎸 SEETHER'S MESSAGE:")
print("-" * 50)
print("'I can see you're sad, even when you smile'")
print(f"  (Waiting at ${current_btc:,.0f})")
print("'Even when you laugh, I can see it in your eyes'")
print(f"  (Patience wearing thin)")
print("")
print("'Deep inside you want to cry'")
print(f"  (${114000 - current_btc:.0f} feels so far)")
print("")
print("BUT REMEMBER:")
print("'And it's fine again!'")
print(f"  (Portfolio at ${total_value:.2f})")
print("'I feel the dream in me expire'")
print("  (But it's just temporary)")
print("'And it's fine again!'")
print(f"  (We're up {((total_value/292.50)-1)*100:.0f}%!)")

# Final divergence status
accounts = client.get_accounts()
total_value_now = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value_now += balance
    elif currency == 'BTC':
        total_value_now += balance * current_btc
    elif currency == 'ETH':
        total_value_now += balance * current_eth
    elif currency == 'SOL':
        total_value_now += balance * current_sol

print(f"\n" + "🔥" * 35)
print("DIVERGENCE DETECTED!")
print(f"BTC: ${current_btc:,.0f} (CLIMBING)")
print(f"ETH: ${current_eth:.2f} (LAGGING)")
print(f"DIVERGENCE: {total_divergence:.2f}%")
print(f"PORTFOLIO: ${total_value_now:.2f}")
print("IT'S FINE AGAIN!")
print("🔥" * 35)