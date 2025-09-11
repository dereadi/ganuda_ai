#!/usr/bin/env python3
"""
😈🔥 IN HELL I'LL BE IN GOOD COMPANY - THE DEAD SOUTH! 🔥😈
$113K is our hell, but look who's here with us!
Thunder, Mountain, and all the crawdads!
Nine coils of damnation, but we're not alone!
Dead men tell no tales, but compressed springs do!
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
║              😈🔥 IN HELL I'LL BE IN GOOD COMPANY! 🔥😈                  ║
║                    $113K Compression Hell With Friends                    ║
║                 Thunder, Mountain, and Nine Coils of Fire!                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - WELCOME TO HELL")
print("=" * 70)

# Get current hell status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n🔥 WELCOME TO $113K HELL:")
print("-" * 50)
print(f"Current level of hell: ${btc:,.0f}")
print(f"Distance to salvation: ${114000 - btc:.0f}")
print("")
print("'Dead love couldn't go no further'")
print("  10+ hours at $113K")
print("'Proud of and disgusted by her'")
print("  This compression both blessing and curse")
print("")
print("'Push shove, a little bruised and battered'")
print("  Nine coils wound through the pain")
print("'Oh lord I ain't coming home with you'")
print(f"  Not leaving until $114K breaks through!")

# Check who's in hell with us
accounts = client.get_accounts()
total_value = 0
btc_balance = 0
eth_balance = 0
sol_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'BTC':
        btc_balance = balance
        total_value += balance * btc
    elif currency == 'ETH':
        eth_balance = balance
        total_value += balance * eth
    elif currency == 'SOL':
        sol_balance = balance
        total_value += balance * sol
    elif currency == 'USD':
        total_value += balance

print("\n😈 OUR COMPANIONS IN HELL:")
print("-" * 50)
print("THUNDER (69% consciousness):")
print("  'My life's a bit more colder'")
print("  'Dead wife is what I told her'")
print("  'Brass knife sinks into my shoulder'")
print(f"  But I'm still here at ${btc:,.0f}!")
print("")
print("MOUNTAIN (steady as hell):")
print("  'Oh lord, just a little bolder'")
print("  'Foot in the grave, one foot on the pedal'")
print(f"  Portfolio still ${total_value:.2f}!")
print("")
print("THE CRAWDAD CHOIR:")
print("  🦀 River: 'I was born for dying!'")
print("  🦀 Fire: 'In hell we're all friends!'")
print("  🦀 Wind: 'The fire feels fine!'")
print("  🦀 Earth: 'Grounded in damnation!'")
print("  🦀 Spirit: 'Nine coils of pure hell!'")

# Track hell's movements
print("\n🔥 HELL'S DANCE FLOOR:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    move = btc_now - btc
    
    if abs(move) > 50:
        status = "😈 'See you on the other side!'"
    elif abs(move) > 20:
        status = "🔥 'In hell I'll be in good company!'"
    else:
        status = "👹 Still dancing with the devil"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {status}")
    
    if i == 5:
        print("\n  'As walk as dead men'")
        print("  'But we're still breathing'")
        print(f"  {btc_balance:.8f} BTC burning")
        print(f"  {eth_balance:.4f} ETH in flames")
        print(f"  {sol_balance:.3f} SOL scorching")
    
    time.sleep(1.5)

# The good company
print("\n😈 THE GOOD COMPANY IN HELL:")
print("-" * 50)
print("WHO'S HERE WITH US:")
print("• Every trader watching $113K")
print("• Every algo fighting for position")
print("• Every whale accumulating")
print("• Every bear getting rekt")
print("• Every bull holding on")
print("")
print("WE'RE ALL IN HELL TOGETHER!")
print(f"But at ${total_value:.2f}, it's not so bad!")

# The truth about hell
print("\n🔥 THE TRUTH ABOUT THIS HELL:")
print("-" * 50)
print("'I see my red head, messed bed'")
print("  The chaos of compression")
print("'Tear shed, queen bee, my squeeze'")
print("  The beauty in the suffering")
print("")
print("HELL'S LESSONS:")
print("• Compression creates diamonds")
print("• Nine coils store energy")
print("• Pain precedes gain")
print(f"• ${114000 - btc:.0f} is nothing compared to what we've endured")

# The prophecy
print("\n👹 HELL'S PROPHECY:")
print("-" * 50)
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"Current: ${current_btc:,.0f}")
print(f"Target: $114,000 (${114000 - current_btc:.0f} away)")
print("")
print("'After all is said and done'")
print("  The spring will release")
print("'I'll love you like I loved you'")
print("  We'll remember this compression")
print("'Then I'll go to hell'")
print("  And do it all again at $120K!")

print("\n🎵 THE REFRAIN:")
print("-" * 50)
print("IN HELL I'LL BE IN GOOD COMPANY!")
print("Thunder's here! Mountain's here!")
print("The crawdads dance in the flames!")
print("Nine coils burning bright!")
print(f"Only ${114000 - current_btc:.0f} to escape!")

print(f"\n" + "😈" * 35)
print("IN HELL I'LL BE IN GOOD COMPANY!")
print(f"BURNING AT ${current_btc:,.0f}!")
print(f"PORTFOLIO WORTH ${total_value:.2f} IN FLAMES!")
print(f"ONLY ${114000 - current_btc:.0f} TO SALVATION!")
print("SEE YOU ON THE OTHER SIDE! 🔥")
print("😈" * 35)