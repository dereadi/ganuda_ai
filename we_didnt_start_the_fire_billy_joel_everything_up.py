#!/usr/bin/env python3
"""
🔥📈 WE DIDN'T START THE FIRE - BILLY JOEL! 📈🔥
Thunder at 69%: "IT WAS ALWAYS BURNING SINCE THE WORLD'S BEEN TURNING!"
Everything is moving up!
Bitcoin, Ethereum, Solana, XRP!
LINK and DOGE and AVAX flow!
We didn't start the fire!
But we're riding every flame to $114K!
Both old and new tracks - the fire continues!
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
║              🔥 WE DIDN'T START THE FIRE - BILLY JOEL! 🔥                ║
║                    Everything Moving Up in Synchrony! 📈                   ║
║           "It Was Always Burning Since The World's Been Turning!" 🌍      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - EVERYTHING BURNING UP!")
print("=" * 70)

# Get all the fires burning
prices = {
    'BTC': float(client.get_product('BTC-USD')['price']),
    'ETH': float(client.get_product('ETH-USD')['price']),
    'SOL': float(client.get_product('SOL-USD')['price']),
    'XRP': float(client.get_product('XRP-USD')['price']),
    'DOGE': float(client.get_product('DOGE-USD')['price']),
    'LINK': float(client.get_product('LINK-USD')['price']),
    'AVAX': float(client.get_product('AVAX-USD')['price']),
    'ADA': float(client.get_product('ADA-USD')['price']),
    'DOT': float(client.get_product('DOT-USD')['price'])
}

print("\n🔥 THE FIRE IS BURNING (Current Prices):")
print("-" * 50)
print(f"Bitcoin: ${prices['BTC']:,.0f} - Harry Truman!")
print(f"Ethereum: ${prices['ETH']:,.2f} - Doris Day!")
print(f"Solana: ${prices['SOL']:.2f} - Red China!")
print(f"XRP: ${prices['XRP']:.4f} - Johnnie Ray!")
print(f"DOGE: ${prices['DOGE']:.4f} - South Pacific!")
print(f"LINK: ${prices['LINK']:.2f} - Walter Winchell!")
print(f"AVAX: ${prices['AVAX']:.2f} - Joe DiMaggio!")
print(f"ADA: ${prices['ADA']:.4f} - Joe McCarthy!")
print(f"DOT: ${prices['DOT']:.2f} - Richard Nixon!")

# Check portfolio in the fire
accounts = client.get_accounts()
total_value = 0
holdings = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
            holdings['USD'] = balance
        elif currency in prices:
            value = balance * prices[currency]
            total_value += value
            holdings[currency] = {'amount': balance, 'value': value}

print("\n🎵 WE DIDN'T START THE FIRE (Your Holdings):")
print("-" * 50)
print(f"Started with: $292.50 - 'Birth control, Ho Chi Minh'")
print(f"Now burning at: ${total_value:.2f} - 'Rock and roller cola wars'")
print(f"Gain percentage: {((total_value/292.50)-1)*100:.0f}% - 'I can't take it anymore!'")

# Live fire monitoring - everything moving up
print("\n📈 LIVE FIRE TRACKING - EVERYTHING UP:")
print("-" * 50)

start_prices = prices.copy()
fire_intensity = []

for i in range(10):
    time.sleep(1.5)
    
    # Update all prices
    current_prices = {
        'BTC': float(client.get_product('BTC-USD')['price']),
        'ETH': float(client.get_product('ETH-USD')['price']),
        'SOL': float(client.get_product('SOL-USD')['price']),
        'XRP': float(client.get_product('XRP-USD')['price']),
        'DOGE': float(client.get_product('DOGE-USD')['price']),
        'LINK': float(client.get_product('LINK-USD')['price'])
    }
    
    # Count how many are up
    up_count = sum(1 for coin, price in current_prices.items() 
                   if price > start_prices.get(coin, price))
    
    # Determine fire status
    if up_count >= 5:
        status = "🔥🔥🔥 INFERNO! Everything rising!"
    elif up_count >= 4:
        status = "🔥🔥 Major fire! Most up!"
    elif up_count >= 3:
        status = "🔥 Fire spreading!"
    else:
        status = "🕯️ Fire simmering"
    
    fire_intensity.append(up_count)
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: {status}")
    print(f"  BTC: ${current_prices['BTC']:,.0f} ({(current_prices['BTC']/start_prices['BTC']-1)*100:+.2f}%)")
    print(f"  SOL: ${current_prices['SOL']:.2f} ({(current_prices['SOL']/start_prices['SOL']-1)*100:+.2f}%)")
    print(f"  {up_count}/6 coins burning up!")
    
    if i == 3:
        print("  🎵 'Ryan started the fire!'")
        print("     (No wait, that's the new version)")
    
    if i == 6:
        print("  🎵 'JFK, blown away, what else do I have to say?'")
        print(f"     BTC blowing past ${current_prices['BTC']:,.0f}!")
    
    if i == 8:
        print("  🎵 'We didn't start the fire!'")
        print("     'But when we are gone, it will still burn on!'")

# Historical fire references
print("\n📚 CRYPTO FIRE HISTORY (Like Billy's List):")
print("-" * 50)
print("Satoshi, Mt. Gox, Silk Road, Pizza Day")
print("Ethereum, The DAO hack, DeFi summer, NFT craze")
print("Dogecoin, Elon tweets, Tesla buys, China bans")
print("GameStop, AMC squeeze, Robinhood, diamond hands")
print("FTX collapse, SVB failure, USDC depeg, recovery")
print(f"NOW: ${prices['BTC']:,.0f}, heading to $114K!")

# Thunder's fire wisdom
print("\n⚡ THUNDER'S FIRE WISDOM (69%):")
print("-" * 50)
print("'THE FIRE BURNS EVERYTHING UP TO $114K!'")
print("")
print("Billy Joel knew:")
print("• Fire always burning (crypto never sleeps)")
print("• Can't fight the flames (momentum unstoppable)")
print("• History repeats (cycles continue)")
print(f"• We ride the fire from ${start_prices['BTC']:,.0f} to $114K")
print("")
avg_intensity = sum(fire_intensity) / len(fire_intensity) if fire_intensity else 0
print(f"Fire intensity: {avg_intensity:.1f}/6 coins rising")

# Both tracks comparison
print("\n🎸 BOTH TRACKS - OLD & NEW FIRE:")
print("-" * 50)
print("Billy Joel (1989): 'We didn't start the fire'")
print("  → Traditional markets, historical events")
print("")
print("Fall Out Boy (2023): 'We didn't start the fire'")  
print("  → Modern chaos, crypto included")
print("")
print("Your Fire (2025):")
print(f"  → Portfolio blazing from $292.50 to ${total_value:.2f}")
print(f"  → {((total_value/292.50)-1)*100:.0f}% gains in the inferno")
print(f"  → Everything moving up to $114K")

# Final fire status
final_prices = {
    'BTC': float(client.get_product('BTC-USD')['price']),
    'ETH': float(client.get_product('ETH-USD')['price']),
    'SOL': float(client.get_product('SOL-USD')['price']),
    'XRP': float(client.get_product('XRP-USD')['price'])
}

print("\n🔥 FINAL FIRE REPORT:")
print("-" * 50)
print(f"BTC: ${final_prices['BTC']:,.0f}")
print(f"ETH: ${final_prices['ETH']:,.2f}")
print(f"SOL: ${final_prices['SOL']:.2f}")
print(f"XRP: ${final_prices['XRP']:.4f}")
print(f"Portfolio in flames: ${total_value:.2f}")
print("")
print("We didn't start the fire!")
print("It was always burning since the world's been turning!")
print(f"But we're riding it from $292.50 to ${total_value:.2f}!")
print(f"And we won't stop until $114K!")

print(f"\n{'🔥' * 35}")
print("WE DIDN'T START THE FIRE!")
print("EVERYTHING MOVING UP!")
print(f"FROM $292.50 TO ${total_value:.2f}!")
print("THE FIRE BURNS TO $114K!")
print("IT WILL STILL BURN ON!")
print("📈" * 35)