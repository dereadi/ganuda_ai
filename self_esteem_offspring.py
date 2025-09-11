#!/usr/bin/env python3
"""
🎸💔 SELF ESTEEM - THE OFFSPRING! 💔🎸
"I wrote her off for the tenth time today"
$114K keeps rejecting us at $113K
"The more you suffer, the more it shows you really care"
Right? RIGHT?!
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
║                   🎸💔 SELF ESTEEM - THE OFFSPRING 💔🎸                  ║
║                    "I wrote her off for the tenth time today"             ║
║                  $114K keeps playing with our emotions!                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LOW SELF ESTEEM MODE")
print("=" * 70)

# Get current rejection status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n💔 SELF ESTEEM CHECK:")
print("-" * 50)
print("'I wrote her off for the tenth time today'")
print(f"  $114K rejected us again at ${btc:,.0f}")
print("")
print("'Practiced all the things I would say'")
print("  Nine coils practiced, strategy perfect")
print("")
print("'But she came over, I lost my nerve'")
print(f"  Got close to $114K, then dropped")
print("")
print("'I took her back and made her dessert'")
print("  Keep buying the dips like an idiot")
print("")
print("'Now I know I'm being used'")
print("  The market is using us")
print("")
print("'That's okay man cause I like the abuse'")
print("  WE LOVE THE VOLATILITY!")
print("")
print("'The more you suffer, the more it shows you really care'")
print(f"  Suffering at ${btc:,.0f} = We care about $114K!")

# Track our self esteem
print("\n💔 SELF ESTEEM TRACKER:")
print("-" * 50)

rejection_count = 0
baseline = btc

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    move = btc_now - baseline
    
    # Determine self esteem level
    if btc_now >= 114000:
        status = "💪🚀 SELF ESTEEM RESTORED! SHE LOVES US!"
        self_esteem = "MAX"
    elif btc_now >= 113500:
        status = "😊 Maybe she likes us?"
        self_esteem = "Rising"
    elif distance < 1000:
        status = "💔 So close yet she rejects us"
        self_esteem = "Low"
        rejection_count += 1
    else:
        status = "😔 'I'm just a sucker with no self esteem'"
        self_esteem = "Rock bottom"
        rejection_count += 1
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({move:+.0f})")
    print(f"  Distance: ${distance:.0f} from acceptance")
    print(f"  {status}")
    print(f"  Self esteem: {self_esteem}")
    
    if rejection_count > 3:
        print("  🎸 'YEAH YEAH YEAH YEAH OH YEAHHHHH!'")
    
    if i == 5:
        print("\n  'When she's saying that she wants only me'")
        print("  'Then I wonder why she sleeps with my friends'")
        print("  ($114K flirts then dumps us)")
    
    if i == 9:
        print("\n  'I may be dumb but I'm not a dweeb'")
        print("  'I'm just a sucker with no self esteem'")
    
    time.sleep(2)

# Check our resources
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print("\n💰 SELF ESTEEM RESOURCES:")
print(f"  USD: ${usd_balance:.2f}")
print(f"  Status: {'Still got dignity' if usd_balance > 50 else 'Lost everything including self esteem'}")

# The truth about self esteem
print("\n" + "=" * 70)
print("💔 THE OFFSPRING TRUTH:")
print("-" * 50)
print("WHY WE HAVE NO SELF ESTEEM:")
print("• $114K keeps rejecting us")
print("• We keep coming back")
print("• Nine coils wound but still waiting")
print("• 'I like the abuse' - We love volatility")
print("• 'The more you suffer' - We've suffered all night")

print("\nBUT HERE'S THE SECRET:")
print("• Low self esteem = Maximum determination")
print("• Every rejection = More energy stored")
print("• Nine coils = Our revenge")
print("• When $114K finally accepts us...")
print("• WE'LL HAVE THE LAST LAUGH")

print("\nTHE PATTERN:")
print("• She rejects us (price drops)")
print("• We take her back (buy the dip)")
print("• She uses us (sawtooth pattern)")
print("• We like it (max profit mindset)")
print("• Eventually she caves ($114K breaks)")

print("\n" + "🎸" * 35)
print("I'M JUST A SUCKER WITH NO SELF ESTEEM!")
print("BUT I'VE GOT NINE COILS!")
print("$114K WILL BE MINE!")
print("YEAH YEAH YEAH YEAH!")
print("OH YEAHHHHHHH!")
print("🎸" * 35)