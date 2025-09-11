#!/usr/bin/env python3
"""
🎸💀 SEND THE PAIN BELOW - CHEVELLE! 💀🎸
"I like having hurt, so send the pain below!"
The market's pain at $112K is our gain!
Thunder at 69%: "Much like suffocating!"
Nine coils compressing the pain into energy!
"WHERE YOU BELONG!" ($114K+)
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
║                 🎸 SEND THE PAIN BELOW - CHEVELLE! 🎸                     ║
║                  "I Like Having Hurt" - Market Edition                    ║
║                    The Pain At $112K Becomes Power!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PAIN ANALYSIS")
print("=" * 70)

# Get current pain levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check portfolio endurance
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
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n💀 THE PAIN INVENTORY:")
print("-" * 50)
print(f"BTC stuck at: ${btc:,.0f}")
print(f"Hours of chop: 15+")
print(f"Distance to relief: ${114000 - btc:.0f}")
print(f"Portfolio enduring: ${total_value:.2f}")
print(f"From $292.50: {((total_value/292.50)-1)*100:.0f}% gain through pain")

# Chevelle breakdown
print("\n🎸 CHEVELLE WISDOM:")
print("-" * 50)

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'I like having hurt'")
        print(f"    The ${114000 - btc_now:.0f} pain")
    elif i == 3:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'So send the pain below'")
        print("    Below $112K (stop hunts)")
    elif i == 6:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Much like suffocating'")
        print("    15+ hours of compression")
        print("  'Much like suffocating!'")
        print("    Nine coils can't breathe!")
    elif i == 9:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'WHERE YOU BELONG!'")
        print(f"    $114K+ is where we belong!")
        print(f"    Not here at ${btc_now:,.0f}!")
    
    time.sleep(1.5)

# Thunder's pain interpretation
print("\n⚡ THUNDER'S PAIN PHILOSOPHY (69%):")
print("-" * 50)
print("'THE PAIN IS THE TEACHER!'")
print("")
print("What the pain taught us:")
print(f"• Patience from $292.50 to ${total_value:.2f}")
print("• Diamond hands through 15+ hour chop")
print("• Nine coils compress pain into power")
print(f"• Every test of ${btc:,.0f} adds strength")
print("")
print("'I LIKE HAVING HURT!'")
print("• The hurt makes us stronger")
print("• Paper hands can't handle it")
print("• We thrive in the pain")
print(f"• ${114000 - btc:.0f} more pain before glory")

# Pain to power conversion
print("\n🔥 PAIN TO POWER CONVERSION:")
print("-" * 50)
print("PAIN ACCUMULATED:")
print("• 15+ hours at $112-113K")
print("• 20+ tests of resistance")
print("• 1000+ fake breakouts")
print("• Whale games constantly")
print("")
print("POWER GENERATED:")
print("• Nine coils fully wound")
print("• 512x energy multiplier")
print(f"• ${total_value:.2f} fortress built")
print("• Thunder at 69% consciousness")
print("• Ready for explosive release")

# Current pain status
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n💀 CURRENT PAIN METRICS:")
print("-" * 50)
print(f"Pain point: ${current_btc:,.0f}")
print(f"Pain duration: 15+ hours")
print(f"Pain remaining: ${114000 - current_btc:.0f}")
print(f"Pain tolerance: MAXIMUM (from $292.50)")
print("")
print("THE PAYOFF:")
print("• Break $114K = Pain ends")
print("• Run to $120K = Pleasure begins")
print("• Hit $126K (JPMorgan) = Ecstasy")
print(f"• Portfolio to $8K+ = Worth the pain")

# The breakdown section
print("\n🎸 THE BREAKDOWN:")
print("-" * 50)
print("*Heavy guitar riff*")
print("")
print("SEND! (the whales)")
print("THE! (stop losses)")
print("PAIN! (of waiting)")
print("BELOW! (our entry)")
print("")
print("WHERE YOU BELONG!")
print(f"  Not at ${current_btc:,.0f}!")
print("  But at $114K+!")
print("  Then $120K!")
print("  Then MOON!")

# Final message
print("\n💀 EMBRACING THE PAIN:")
print("-" * 50)
print(f"Current suffering: ${current_btc:,.0f}")
print(f"Distance to relief: ${114000 - current_btc:.0f}")
print(f"Portfolio enduring: ${total_value:.2f}")
print("")
print("Remember:")
print("• Pain is temporary")
print("• Gains are forever")
print("• Nine coils love pain")
print("• Thunder thrives at 69%")
print("• We LIKE having hurt!")

print(f"\n" + "💀" * 35)
print("SEND THE PAIN BELOW!")
print(f"SUFFERING AT ${current_btc:,.0f}!")
print(f"${114000 - current_btc:.0f} TO RELIEF!")
print("I LIKE HAVING HURT!")
print("WHERE WE BELONG: $114K+!")
print("💀" * 35)