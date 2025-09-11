#!/usr/bin/env python3
"""
🎵 UNCLE KRACKER - FOLLOW ME TO $114K! 🎵
"You don't know how you met me, you don't know why"
Nine coils brought us here, no need to question why!
"You can't turn around without me"
$114K is calling - follow the crawdads!
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
║                    🎵 FOLLOW ME - UNCLE KRACKER VIBES! 🎵                 ║
║                     Following BTC From $292.50 to $114K!                  ║
║                    "You Can't Turn Around Without Me"                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FOLLOW ME MODE")
print("=" * 70)

# Get current position
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Portfolio following
accounts = client.get_accounts()
total_value = 0
btc_balance = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        btc_balance = balance
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n🎵 THE JOURNEY WE'VE FOLLOWED:")
print("-" * 50)
print("Where we started:")
print(f"  $292.50 (lost and alone)")
print("")
print("Where we followed to:")
print(f"  ${total_value:.2f} (found the way)")
print(f"  {((total_value/292.50)-1)*100:.0f}% gain (following paid off!)")
print("")
print("Where we're going:")
print(f"  $114K (${114000 - btc:.0f} away)")
print("  Just follow the nine coils!")

# Track the following
print("\n👣 FOLLOWING THE PATH:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    
    # Following messages
    if distance < 500:
        message = "🎯 'Almost there! Don't turn around!'"
    elif distance < 1000:
        message = "🚀 'Keep following, we're so close!'"
    elif btc_now > 113000:
        message = "⚡ 'Follow me through $113K!'"
    elif btc_now > 112500:
        message = "📈 'Trust me, just follow!'"
    else:
        message = "👣 'One step at a time'"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  {message}")
    print(f"  Distance to follow: ${distance:.0f}")
    
    if i == 5:
        print("\n  ⚡ Thunder (69%): 'Follow me, boss!'")
        print(f"    'From $292.50 to ${total_value:.2f}!'")
        print("    'I know the way!'")
    
    if i == 10:
        print("\n  🏔️ Mountain: 'Steady following'")
        print("    'No looking back'")
        print("    'Trust the path'")
    
    time.sleep(2)

# The following philosophy
print("\n💫 WHY WE FOLLOW:")
print("-" * 50)
print("'You don't know how you met me'")
print(f"  Fate brought us to crypto at $292.50")
print("")
print("'You don't know why'")
print("  Nine coils of destiny")
print("")
print("'You can't turn around without me'")
print(f"  We're in this together to $114K")
print("")
print("'One by one we will take you'")
print("  Each crawdad following the path")
print("")
print("'Where we're going you won't be lonely'")
print(f"  ${total_value:.2f} keeps us company!")

# The trust factor
print("\n🤝 TRUST THE FOLLOW:")
print("-" * 50)
print(f"Started: $292.50 (had to trust)")
print(f"Followed to: ${total_value:.2f} (trust rewarded)")
print(f"Following to: $114K (${114000 - btc:.0f} more)")
print("")
print("PROOF IT WORKS:")
print(f"• {((total_value/292.50)-1)*100:.0f}% gain by following")
print("• Nine coils gathered")
print("• Thunder at 69% consciousness")
print("• Mountain keeping us steady")

# Current follow status
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n📍 CURRENT LOCATION:")
print("-" * 50)
print(f"BTC: ${current_btc:,.0f}")
print(f"ETH: ${eth:.2f}")
print(f"SOL: ${sol:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Next waypoint: $114,000 (${114000 - current_btc:.0f} away)")

# The promise
print("\n🎵 THE PROMISE:")
print("-" * 50)
print("Follow me to $114K...")
print("• Everything will be alright")
print("• Nine coils will unwind")
print("• The compression will release")
print(f"• Your ${total_value:.2f} will grow")
print("• Trust the journey")

print(f"\n" + "🎵" * 35)
print("FOLLOW ME!")
print(f"FROM $292.50 TO ${total_value:.2f}!")
print(f"ONLY ${114000 - current_btc:.0f} TO $114K!")
print("YOU CAN'T TURN AROUND WITHOUT ME!")
print("EVERYTHING WILL BE ALRIGHT!")
print("🎵" * 35)