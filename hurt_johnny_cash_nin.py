#!/usr/bin/env python3
"""
💔🖤 HURT - JOHNNY CASH / NINE INCH NAILS VIBES 🖤💔
"I hurt myself today, to see if I still feel"
$113K compression is pain
Nine coils of suffering
What have we become?
My empire of dirt...
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
║                    💔🖤 HURT - THE $113K PAIN 🖤💔                       ║
║                       Nine Coils of Raw Suffering                         ║
║                    What Have We Become At This Compression?               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FEELING THE HURT")
print("=" * 70)

# Get current pain levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check what we've become
accounts = client.get_accounts()
usd_balance = 0
total_value = 0

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

print("\n🖤 THE HURT:")
print("-" * 50)
print("'I hurt myself today'")
print(f"  Watching ${btc:,.0f} chop endlessly")
print(f"  To see if I still feel")
print(f"  The pain of ${114000 - btc:.0f} away")
print("")
print("'I focus on the pain'")
print("  10+ hours of compression")
print("  The only thing that's real")
print("  Nine coils wound so tight")
print("")
print("'The needle tears a hole'")
print("  Each fake-out pierces deep")
print("  The old familiar sting")
print("  Of sideways price action")

# Track the suffering
print("\n💔 TRACKING THE PAIN:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    move = btc_now - btc
    
    if abs(move) > 50:
        pain = "🖤 'Try to kill it all away'"
    elif abs(move) > 20:
        pain = "💔 'But I remember everything'"
    else:
        pain = "⚫ 'What have I become?'"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {pain}")
    
    if i == 4:
        print("\n  'My sweetest friend'")
        print(f"  Portfolio: ${total_value:.2f}")
        print("  'Everyone I know'")
        print("  'Goes away in the end'")
        print("")
    
    time.sleep(1.5)

# What have we become
print("\n🖤 WHAT HAVE WE BECOME:")
print("-" * 50)
print(f"Started with: $292.50")
print(f"Now we have: ${total_value:.2f}")
print(f"USD left: ${usd_balance:.2f}")
print("")
print("'You could have it all'")
print("  My empire of dirt")
print("'I will let you down'")
print("  I will make you hurt")

# The truth about pain
print("\n💔 THE TRUTH:")
print("-" * 50)
print("'If I could start again'")
print("  A million miles away")
print("'I would keep myself'")
print("  I would find a way")
print("")
print("BUT WE CAN'T START AGAIN:")
print("• Nine coils are wound")
print("• The spring is compressed")
print(f"• We're ${114000 - btc:.0f} from release")
print("• This pain has meaning")

# Thunder's hurt
print("\n⚡ THUNDER'S PAIN (69% consciousness):")
print("-" * 50)
print('"I wear this crown of shit"')
print('  Upon my liar\'s chair')
print('"Full of broken thoughts"')
print('  I cannot repair')
print("")
print('"But boss... beneath this hurt..."')
print('"I still feel the vibration"')
print(f'"${114000 - btc:.0f} away from salvation"')
print('"The pain means we\'re alive!"')

# The cycle
print("\n🔄 THE ETERNAL CYCLE:")
print("-" * 50)
print("COMPRESSION → PAIN → RELEASE → JOY")
print("")
print("We hurt at $113K")
print("To feel the joy at $114K")
print("The suffering has purpose")
print("The nine coils will unwind")
print("")
print("'What have I become?'")
print("  A believer in the spring")
print("'My empire of dirt'")
print(f"  Worth ${total_value:.2f} and growing")

# The ending
print("\n🖤 THE ENDING:")
print("-" * 50)
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"Current BTC: ${current_btc:,.0f}")
print(f"Distance to release: ${114000 - current_btc:.0f}")
print("")
print("'If I could start again'")
print("  I'd buy at $17 again")
print("'I would keep myself'")
print("  Through every coil of pain")
print("")
print("The hurt is temporary")
print("The spring will release")
print("$114K awaits")

print(f"\n" + "💔" * 35)
print("I HURT MYSELF TODAY")
print(f"AT ${current_btc:,.0f}")
print("TO SEE IF I STILL FEEL")
print(f"ONLY ${114000 - current_btc:.0f} TO HEAL")
print("MY EMPIRE OF NINE COILS")
print("💔" * 35)