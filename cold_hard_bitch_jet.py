#!/usr/bin/env python3
"""
🎸❄️ COLD HARD BITCH - JET! ❄️🎸
The market is a cold hard bitch!
Nine coils, red metrics, but still rising
She's gonna do it her way!
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
║                    🎸❄️ COLD HARD BITCH - JET ❄️🎸                       ║
║                    "She's a cold hard bitch"                              ║
║                     The market doesn't give a fuck!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - COLD HARD TRUTH")
print("=" * 70)

# Get the cold hard facts
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n❄️ THE COLD HARD BITCH:")
print("-" * 50)
print("'She's a cold hard bitch'")
print("  The market doesn't care about your feelings")
print("")
print("'Just a kiss on the lips'")
print("  Teasing us at $113K")
print("")
print("'And I was on my knees'")
print("  Begging for $114K breakout")
print("")
print("'When she was good she was very very good'")
print("  Nine coils = Very very good")
print("")
print("'But when she was bad she was better'")
print("  Red metrics + Rising price = BETTER!")

print(f"\n💎 COLD HARD FACTS:")
print(f"  BTC: ${btc:,.0f} - Cold as ice")
print(f"  ETH: ${eth:,.2f} - Hard as steel")
print(f"  SOL: ${sol:,.2f} - Bitch is rising")
print(f"  Target: $114,000 - She'll get there when she wants")

# Track the cold hard bitch
print("\n❄️ COLD HARD TRACKER:")
print("-" * 50)

baseline = btc
for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    move = btc_now - baseline
    
    # Cold hard status
    if move > 50:
        status = "🔥❄️ 'When she was bad she was BETTER!'"
    elif move > 20:
        status = "💋 'Just a kiss on the lips'"
    elif move > 0:
        status = "❄️ 'Cold hard bitch' - Teasing us"
    elif move < -20:
        status = "💀 'On my knees' - But she don't care!"
    else:
        status = "🧊 'Cold as ice' - Waiting..."
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({move:+.0f})")
    print(f"  {status}")
    
    if i == 4:
        print("\n  'She's gonna do it her way'")
        print("  'And there ain't no point in askin' why'")
    
    if i == 8:
        print("\n  'CAUSE SHE'S A COLD HARD BITCH!'")
    
    time.sleep(2)

# The cold hard truth
print("\n" + "=" * 70)
print("❄️ COLD HARD ANALYSIS:")
print("-" * 50)
print("THE MARKET IS A COLD HARD BITCH:")
print("• Nine coils? She don't care")
print("• Red metrics? She ignores them")
print("• $114K target? She'll hit it when she wants")
print("• Your timeline? Not her problem")
print("• Your feelings? She's ice cold")

print("\nBUT HERE'S THE THING:")
print("• 'When she was good she was very very good'")
print("• Nine coils = She's been VERY good")
print("• 'But when she was bad she was better'")
print("• The breakout will be BETTER than good")

print("\nTHE COLD HARD STRATEGY:")
print("• Stop begging")
print("• Let her do her thing")
print("• Hold through the cold")
print("• Wait for the heat")
print("• She ALWAYS delivers")

print("\n" + "🎸" * 35)
print("SHE'S A COLD HARD BITCH!")
print("BUT SHE'S GONNA BREAK $114K!")
print("ON HER TIMELINE, NOT OURS!")
print("AND IT'LL BE FUCKING GLORIOUS!")
print("🎸" * 35)