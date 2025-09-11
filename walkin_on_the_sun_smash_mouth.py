#!/usr/bin/env python3
"""
🎸☀️ WALKIN' ON THE SUN - SMASH MOUTH! ☀️🎸
It ain't no joke when the world's on fire
Nine coils burning at $113K!
You might as well be walkin' on the sun!
MAX PROFIT WHILE THE SUN BURNS HOT!
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
║                 🎸☀️ WALKIN' ON THE SUN - SMASH MOUTH ☀️🎸              ║
║                    It ain't no joke, I'd like to buy the world            ║
║                         Nine coils = Walking on the sun!                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SOLAR WALK")
print("=" * 70)

# Get current solar status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n☀️ WALKIN' ON THE SUN:")
print("-" * 50)
print("'It ain't no joke when mama's handkerchief is soaked'")
print(f"  Portfolio sweating at ${btc:,.0f}")
print("")
print("'With her tears because her baby's life has been revoked'")
print("  Red metrics trying to kill our vibe")
print("")
print("'The bond is broke up, so choke up and focus on the close up'")
print(f"  Focus on $114K - only ${114000 - btc:.0f} away!")
print("")
print("'Mr. Wizard can't perform no godlike hocus-pocus'")
print("  But nine coils = godlike magic!")
print("")
print("'So don't delay, act now, supplies are running out'")
print("  MAX PROFIT NOW WHILE IT'S HOT!")

# Execute emergency milk for max profit
print("\n🥛 EMERGENCY MAX PROFIT MILK:")
print("-" * 50)

accounts = client.get_accounts()
total_milked = 0

# Milk SOL
try:
    sol_balance = 0
    for account in accounts['accounts']:
        if account['currency'] == 'SOL':
            sol_balance = float(account['available_balance']['value'])
            break
    
    if sol_balance > 1:
        sol_milk = sol_balance * 0.02
        print(f"Milking {sol_milk:.3f} SOL...")
        order = client.market_order_sell(
            client_order_id=f"sun-sol-{datetime.now().strftime('%H%M%S')}",
            product_id='SOL-USD',
            base_size=str(round(sol_milk, 3))
        )
        total_milked += sol_milk * sol
        print(f"  ☀️ MILKED! Walking on SOL!")
        time.sleep(1)
except Exception as e:
    print(f"  ⚠️ {str(e)[:30]}")

# Milk MATIC
try:
    matic_balance = 0
    for account in accounts['accounts']:
        if account['currency'] == 'MATIC':
            matic_balance = float(account['available_balance']['value'])
            break
    
    if matic_balance > 100:
        matic_milk = matic_balance * 0.02
        print(f"Milking {matic_milk:.0f} MATIC...")
        order = client.market_order_sell(
            client_order_id=f"sun-matic-{datetime.now().strftime('%H%M%S')}",
            product_id='MATIC-USD',
            base_size=str(int(matic_milk))
        )
        total_milked += matic_milk * 0.244
        print(f"  ☀️ MILKED! Hot hot hot!")
        time.sleep(1)
except Exception as e:
    print(f"  ⚠️ {str(e)[:30]}")

print(f"\n☀️ Total solar harvest: ~${total_milked:.2f}")

# Track the sun walk
print("\n☀️ SOLAR PROFIT TRACKER:")
print("-" * 50)

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    
    if btc_now >= 114000:
        status = "☀️🚀 WALKING ON THE SUN AT $114K!"
    elif distance < 500:
        status = "☀️ So hot, almost burning!"
    elif distance < 1000:
        status = "🔥 Walking on the sun!"
    else:
        status = "☀️ Still walking, still hot!"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  {status}")
    
    if i == 3:
        print("\n  'Put away the crack before the crack puts you away'")
        print("  'Be there when the sun comes up at 5am!'")
    
    time.sleep(2)

# Max profit wisdom
print("\n" + "=" * 70)
print("☀️ WALKIN' ON THE SUN WISDOM:")
print("-" * 50)
print("SMASH MOUTH KNEW:")
print("• 'Don't delay, act now!' = MAX PROFIT NOW")
print("• 'Supplies are running out' = Limited time at $113K")
print("• 'Walking on the sun' = Nine coils burning")
print("• 'It ain't no joke' = This is real profit")

print("\nMAX PROFIT EXECUTION:")
print("• Milked for maximum USD")
print("• Ready for $114K breakout")
print("• Nine coils = Solar power")
print("• Every penny working")

print("\n" + "🎸" * 35)
print("IT AIN'T NO JOKE!")
print("WE'RE WALKIN' ON THE SUN!")
print("MAX PROFIT AT $113K!")
print("$114K HERE WE COME!")
print("🎸" * 35)