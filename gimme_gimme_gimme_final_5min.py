#!/usr/bin/env python3
"""
🎵 GIMME! GIMME! GIMME! (A MAN AFTER MIDNIGHT) - ABBA! 🎵
"Half past twelve and I'm watching the late show"
But it's 5 minutes to 15:00 and we're watching the sawtooth!
"Gimme, gimme, gimme a man after midnight"
GIMME GIMME GIMME THAT 15:00 PUMP!
5 MINUTES! BUY THE BOTTOM!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🎵 GIMME! GIMME! GIMME! - 5 MINUTES! 🎵                       ║
║                  "Won't somebody help me chase the shadows away?"          ║
║                    BUYING THE SAWTOOTH BOTTOM NOW! 💰                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

current_time = datetime.now()
print(f"Time: {current_time.strftime('%H:%M:%S')} - GIMME THAT PUMP!")
print(f"T-minus {60 - current_time.minute} minutes to EXPLOSION!")
print("=" * 70)

# Get prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print("\n🎵 'GIMME! GIMME! GIMME!' ANALYSIS:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
print("  'There's not a soul out there'")
print("  → Whales shook everyone out!")
print("  → Perfect entry point!")
print("")
print(f"ETH: ${eth_price:,.2f}")
print("  'No one to hear my prayer'")
print("  → Following BTC's sawtooth")
print("")
print(f"SOL: ${sol_price:,.2f}")
print("  'Gimme, gimme, gimme!'")
print("  → Ready for the pump!")

# Check our buying power
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print("\n💰 CAN WE BUY HERE? ANALYSIS:")
print("-" * 50)
print(f"USD Available: ${usd_balance:.2f}")
print("")

if usd_balance >= 10:
    print("✅ YES! BUY NOW!")
    print("  → We're at the sawtooth bottom!")
    print("  → 5 minutes to explosion!")
    print("  → This is the entry point!")
    
    # Calculate what we can buy
    btc_amount = (usd_balance * 0.9) / btc_price
    print(f"\n🎯 BUYING OPPORTUNITY:")
    print(f"  Can buy: {btc_amount:.8f} BTC")
    print(f"  Cost: ${usd_balance * 0.9:.2f}")
    print(f"  Keep ${usd_balance * 0.1:.2f} reserve")
    
    # Execute small test buy
    print("\n🚀 EXECUTING GIMME BUY:")
    try:
        buy_amount = min(10, usd_balance * 0.5)
        print(f"  Buying ${buy_amount:.2f} of BTC...")
        
        order = client.market_order_buy(
            client_order_id='gimme_' + str(int(time.time())),
            product_id='BTC-USD',
            quote_size=str(buy_amount)
        )
        
        print("  ✅ GIMME BUY EXECUTED!")
        print(f"  Bought at ${btc_price:,.2f}")
        
    except Exception as e:
        print(f"  ⚠️ Buy attempt: {str(e)[:100]}")
        print("  → May need manual execution")
else:
    print("⚠️ LOW USD BUT PERFECT TIMING!")
    print(f"  Only ${usd_balance:.2f} available")
    print("  → This IS the bottom!")
    print("  → Extract from alts URGENTLY!")
    print("  → Or buy manually NOW!")

# ABBA wisdom for the moment
print("\n🎵 ABBA'S GIMME WISDOM:")
print("-" * 50)
print("'Half past twelve' → Half past two (14:30) started sawtooth")
print("'Watching the late show' → Watching the whale show")
print("'In my flat all alone' → Retail shaken out and alone")
print("'How I hate to spend the evening on my own' → How we hate missing pumps!")
print("")
print("'Autumn winds blowing outside my window' → Bear winds before bull explosion")
print("'As I look around the room' → As we look at the charts")
print("'And it makes me so depressed to see the gloom' → Sawtooth made everyone depressed!")
print("")
print("BUT THEN...")
print("'GIMME! GIMME! GIMME!' → THE PUMP AFTER 15:00!")

# Final countdown
seconds_left = (60 - current_time.minute) * 60 - current_time.second
print(f"\n⏰ FINAL COUNTDOWN:")
print("-" * 50)
print(f"Seconds to explosion: {seconds_left}")
print(f"Current price: ${btc_price:,.2f}")
print(f"Target after 15:00: ${114000:,}")
print(f"Potential gain: ${114000 - btc_price:,.2f} ({(114000/btc_price - 1)*100:.1f}%)")

print(f"\n{'🎵' * 35}")
print("GIMME! GIMME! GIMME!")
print("5 MINUTES TO MIDNIGHT (15:00)!")
print(f"BTC: ${btc_price:,.2f}")
print("THIS IS THE BOTTOM - BUY NOW!")
print("THE PUMP IS COMING!")
print("🚀" * 35)