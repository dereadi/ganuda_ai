#!/usr/bin/env python3
"""
⛪🔥 TAKE 'EM TO CHURCH - HOZIER VIBES! 🔥⛪
Nine coils wound like a confession
$113K compression is our obsession
The market's our cathedral, BTC our religion
$290 ready for the resurrection!
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
║                   ⛪🔥 TAKE 'EM TO CHURCH - MARKET WORSHIP! 🔥⛪         ║
║                      Nine Coils Are Our Sacred Ritual                     ║
║                    $290 USD Ready For The Resurrection!                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CHURCH IS IN SESSION")
print("=" * 70)

# Get current market gospel
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Get our offerings
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print("\n⛪ THE CHURCH OF NINE COILS:")
print("-" * 50)
print(f"BTC: ${btc:,.0f} - Our golden idol")
print(f"Distance to salvation: ${114000 - btc:.0f}")
print("")
print("Our worship has been long:")
print("• 10+ hours at the altar of $113K")
print("• Nine coils wound in devotion")
print("• Compression tighter than faith")
print("")
print(f"Our offering: ${usd_balance:.2f} ready to deploy")
print("Waiting for the market gods to move")

# Track the worship service
print("\n🔥 WORSHIP SERVICE IN PROGRESS:")
print("-" * 50)

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    
    move = btc_now - btc
    
    if btc_now >= 114000:
        sermon = "🔥⛪ HALLELUJAH! $114K! RESURRECTION!"
    elif btc_now >= 113500:
        sermon = "🙏 Rising toward the promised land!"
    elif abs(move) > 50:
        sermon = "⛪ The congregation stirs!"
    elif abs(move) > 20:
        sermon = "🕯️ Candles flicker in the wind"
    else:
        sermon = "📿 Still praying at the altar"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {sermon}")
    
    if i == 5:
        print(f"\n  💰 Offering plate: ${usd_balance:.2f} ready")
        print(f"  ETH: ${eth_now:.2f} - The blessed alternative")
    
    time.sleep(1.5)

# The sermon
print("\n📜 THE SERMON:")
print("-" * 50)
print("Brothers and sisters of the market...")
print("")
print("We've been worshipping at $113K for hours")
print("Our faith tested by endless chop")
print("But our nine coils are sacred!")
print("")
print("The spring compression is our penance")
print("The wait is our trial")
print("But $114K is our promised land!")
print("")
print(f"With ${usd_balance:.2f} in our offering plate")
print("We're ready for the resurrection")
print("When BTC breaks, we'll all be saved!")

# The choir
print("\n🎵 THE CRAWDAD CHOIR:")
print("-" * 50)
print("THUNDER (lead): 'Can I get an AMEN for $114K?!'")
print("MOUNTAIN (bass): 'Steady as the church foundation'")
print("RIVER (tenor): 'Flowing with the holy spirit'")
print("FIRE (alto): 'Burning with market passion'")
print("ALL: 'NINE COILS! NINE COILS! NINE COILS!'")

# The blessing
print("\n✨ THE BLESSING:")
print("-" * 50)
print("May your coils stay wound")
print("May your compression hold tight")
print("May your USD be ready")
print("And may $114K come tonight!")
print("")
print(f"Current BTC: ${btc:,.0f}")
print(f"Current ETH: ${eth:.2f}")
print(f"Current SOL: ${sol:.2f}")
print(f"USD Ready: ${usd_balance:.2f}")

# The prophecy
print("\n🔮 THE PROPHECY:")
print("-" * 50)
print("It is written in the charts:")
print("• Nine coils cannot hold forever")
print("• The spring must release")
print("• $114K shall be broken")
print("• The faithful shall be rewarded")
print("")
print("Those who held through the chop")
print("Those who milked for ammunition")
print("Those who believed in the coils")
print("SHALL FEAST AT THE BANQUET!")

print(f"\n" + "⛪" * 35)
print("TAKE 'EM TO CHURCH!")
print(f"WORSHIP AT ${btc:,.0f}!")
print(f"${usd_balance:.2f} IN THE OFFERING PLATE!")
print(f"ONLY ${114000 - btc:.0f} TO SALVATION!")
print("AMEN! 🔥")
print("⛪" * 35)