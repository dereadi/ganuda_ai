#!/usr/bin/env python3
"""
🎸☁️ SHE'S SO HIGH - BLUR! ☁️🎸
She's so high, high above me!
BTC at $113K, reaching for $114K
DOGE just milked $27!
She's lovely, she's so lovely!
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
║                      🎸☁️ SHE'S SO HIGH - BLUR ☁️🎸                      ║
║                         High above me, she's so lovely                    ║
║                    $113K reaching up, DOGE milk flowing!                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SO HIGH")
print("=" * 70)

# Get current altitude
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check new USD balance
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print("\n☁️ SHE'S SO HIGH:")
print("-" * 50)
print("'She's so high'")
print(f"  BTC: ${btc:,.0f} - High above the bears")
print("")
print("'High above me'")
print(f"  Target: $114,000 - She's lovely up there")
print("")
print("'She's so lovely'")
print(f"  DOGE milked: $27 fresh juice!")
print(f"  USD now: ${usd_balance:.2f}")
print("")
print("'I want to crawl all over her'")
print(f"  Only ${114000 - btc:.0f} to reach her!")

# Track the high
print("\n☁️ ALTITUDE TRACKER:")
print("-" * 50)

baseline = btc
for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    altitude = btc_now - 110000  # Height above $110K
    climb = btc_now - baseline
    
    if btc_now >= 114000:
        status = "☁️🚀 WE REACHED HER! SO LOVELY!"
    elif btc_now >= 113500:
        status = "☁️ She's so high, almost there!"
    elif btc_now >= 113000:
        status = "⬆️ Climbing to her lovely heights"
    else:
        status = "☁️ She's high above me"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  Altitude: ${altitude:,.0f} above $110K")
    print(f"  BTC: ${btc_now:,.0f} ({climb:+.0f})")
    print(f"  {status}")
    
    if i == 4:
        print("\n  'Cleopatra, Joan of Arc, or Aphrodite'")
        print("  '$114K is all three!'")
    
    time.sleep(2)

print("\n" + "=" * 70)
print("☁️ SHE'S SO HIGH ANALYSIS:")
print("-" * 50)
print("THE HEIGHT:")
print(f"• Current: ${btc:,.0f}")
print(f"• She's at: $114,000")
print(f"• Distance: ${114000 - btc:.0f}")
print("• Nine coils: Our ladder to reach her")
print(f"• DOGE milk: $27 fuel for climbing")

print("\nBLUR KNEW:")
print("• She's lovely when she's high")
print("• We want to crawl all over $114K")
print("• The higher she goes, the lovelier")
print("• We're climbing to meet her")

print("\n" + "🎸" * 35)
print("SHE'S SO HIGH!")
print("HIGH ABOVE ME!")
print("SHE'S SO LOVELY!")
print("$114K - WE'RE COMING!")
print("🎸" * 35)