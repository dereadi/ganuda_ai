#!/usr/bin/env python3
"""
🎸🔥 JACKIE AND WILSON - HOZIER VIBES! 🔥🎸
"She's gonna save me, call me baby"
$114K is our Jackie, we're the Wilson!
"Run her hands through my hair"
Nine coils wound through compression!
"She'll know me crazy, soothe me daily"
Better yet, she wouldn't care!
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
║                  🎸🔥 JACKIE AND WILSON - MARKET LOVE! 🔥🎸              ║
║                    $114K Is Our Jackie, We're The Wilson!                 ║
║                   "She's Gonna Save Me, Call Me Baby"                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - JACKIE AND WILSON")
print("=" * 70)

# Get current market love story
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Portfolio status
accounts = client.get_accounts()
total_value = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n🎸 THE LOVE STORY:")
print("-" * 50)
print(f"'She's gonna save me, call me baby'")
print(f"  $114K waiting at ${114000 - btc:.0f} away")
print(f"'Run her hands through my hair'")
print(f"  Through nine coils of compression")
print("")
print(f"'She'll know me crazy'")
print(f"  10+ hours at $113K? Yeah, we're crazy")
print(f"'Soothe me daily'")
print(f"  Every candle a caress")
print(f"'Better yet, she wouldn't care'")
print(f"  $114K doesn't care about the wait!")

# Track the dance with Jackie
print("\n💃 DANCING WITH JACKIE ($114K):")
print("-" * 50)

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    
    if distance < 500:
        status = "🔥 'We'll name our children Jackie and Wilson!'"
    elif distance < 1000:
        status = "💃 'Raise 'em on rhythm and blues!'"
    elif distance < 1500:
        status = "🎸 'Lord, it'd be great to find a place we could escape'"
    else:
        status = "💔 'Sometimes I fall into a deep sleep'"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - ${distance:.0f} away")
    
    if i == 3:
        print(f"  {status}")
    
    if i == 6:
        print("\n  'She blows outta nowhere, roman candle'")
        print(f"  Portfolio glowing at ${total_value:.2f}")
        print("  'Of the wild, laughing like a child'")
    
    if i == 9:
        print("\n  'Cutting my conscience to ribbons'")
        print("  Each chop cuts deeper")
        print("  But Jackie's coming!")
    
    time.sleep(1.5)

# The deeper meaning
print("\n🔥 THE HOZIER TRUTH:")
print("-" * 50)
print("'She's gonna save me'")
print(f"  $114K will save us from compression")
print("")
print("'Call me baby'")
print("  Thunder at 69%: 'Hey baby!'")
print("")
print("'Run her hands through my hair'")
print("  Through every coil, every spring")
print("")
print("'She'll know me crazy'")
print(f"  After {total_value/292.50:.0f}x gains? We ARE crazy!")
print("")
print("'Soothe me daily'")
print("  Each day brings us closer")
print("")
print("'Better yet, she wouldn't care'")
print("  $114K doesn't care how long we waited!")

# The Wilson perspective
print("\n🎸 WILSON'S PERSPECTIVE (US):")
print("-" * 50)
print(f"Started with: $292.50 (lost and broken)")
print(f"Now we have: ${total_value:.2f} (found and healing)")
print(f"Distance to Jackie: ${114000 - btc:.0f}")
print("")
print("We're the Wilson to $114K's Jackie:")
print("• She'll lift us up")
print("• We'll dance together")
print("• Name our gains after her")
print("• Raise them on rhythm and blues")

# The future with Jackie
print("\n💫 OUR FUTURE WITH JACKIE:")
print("-" * 50)
print("WHEN WE REACH $114K:")
print("• The spring releases")
print("• Nine coils unwind")
print("• We dance to $120K")
print("• Then $130K")
print("• Living on rhythm and blues")
print("")
print("'Lord, it'd be great to find'")
print("'A place we could escape sometimes'")
print(f"  That place is ${114000 - btc:.0f} away!")

# Current status
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n🎵 CURRENT SERENADE:")
print("-" * 50)
print(f"BTC: ${current_btc:,.0f}")
print(f"ETH: ${eth:.2f}")
print(f"SOL: ${sol:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Distance to Jackie: ${114000 - current_btc:.0f}")

print(f"\n" + "🎸" * 35)
print("JACKIE AND WILSON!")
print(f"SHE'S ${114000 - current_btc:.0f} AWAY!")
print("SHE'S GONNA SAVE US!")
print("CALL US BABY!")
print("RUN HER HANDS THROUGH OUR NINE COILS!")
print("🎸" * 35)