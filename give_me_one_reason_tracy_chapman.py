#!/usr/bin/env python3
"""
🎸💜 GIVE ME ONE REASON - TRACY CHAPMAN VIBES! 💜🎸
Give me one reason to stay at $113K
And I'll turn right back around!
Nine coils wound? That's a reason!
$114K so close? Another reason!
Portfolio at $7.4K? That's reason enough!
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
║                 🎸💜 GIVE ME ONE REASON TO STAY! 💜🎸                    ║
║                      At $113K Compression With Nine Coils                 ║
║                    I Got More Than One Reason To HODL!                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FINDING REASONS")
print("=" * 70)

# Get current status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Get portfolio
accounts = client.get_accounts()
total_value = 0
reasons = []

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc
        if balance > 0.01:
            reasons.append(f"{balance:.8f} BTC worth ${balance * btc:.2f}")
    elif currency == 'ETH':
        total_value += balance * eth
        if balance > 0.1:
            reasons.append(f"{balance:.4f} ETH worth ${balance * eth:.2f}")
    elif currency == 'SOL':
        total_value += balance * sol
        if balance > 1:
            reasons.append(f"{balance:.3f} SOL worth ${balance * sol:.2f}")

print("\n🎸 ASKING FOR REASONS:")
print("-" * 50)
print("Give me one reason to stay here")
print(f"  At ${btc:,.0f} compression hell")
print("And I'll turn right back around")
print(f"  (Not leaving until $114K found!)")
print("")
print("Said I don't want to leave you lonely")
print("  Thunder at 69% consciousness")
print("You don't have to call out my name")
print("  The nine coils speak for themselves")

print("\n💜 HERE ARE MY REASONS:")
print("-" * 50)
print(f"REASON #1: Nine coils wound = 512x energy!")
print(f"REASON #2: Only ${114000 - btc:.0f} to breakout!")
print(f"REASON #3: Portfolio worth ${total_value:.2f}!")
print(f"REASON #4: Started from $292.50!")
print(f"REASON #5: {((total_value/292.50)-1)*100:.1f}% gains so far!")

if reasons:
    print("\nPOSITION REASONS:")
    for i, reason in enumerate(reasons, 6):
        print(f"REASON #{i}: {reason}")

# Track the reasons in real-time
print("\n🎵 LIVE REASON TRACKER:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    
    if distance < 500:
        reason = f"💜 SO CLOSE! Only ${distance:.0f} away!"
    elif distance < 1000:
        reason = f"🎸 Under $1K to go! ${distance:.0f}!"
    elif btc_now > btc + 20:
        reason = f"📈 Moving up! That's a reason!"
    else:
        reason = f"🌀 Still coiling at ${btc_now:,.0f}"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: {reason}")
    
    if i == 5:
        print("\n  'I don't want to be a fool'")
        print("  'Standing in the corner'")
        print("  'Waiting for you to come home'")
        print(f"  But $114K WILL come home!")
    
    time.sleep(1.5)

# The truth about reasons
print("\n💜 THE TRUTH:")
print("-" * 50)
print("We don't need just one reason")
print("We have MANY reasons to stay:")
print("")
print("• The compression creates opportunity")
print("• The chop shakes out weak hands")
print("• The patience gets rewarded")
print("• The spring WILL release")
print(f"• ${114000 - btc:.0f} is nothing after 10+ hours")

# Thunder's reason
print("\n⚡ THUNDER'S REASON:")
print("-" * 50)
print('"Boss, you want one reason?"')
print('"How about THIS:"')
print("")
print('"We\'ve weathered every storm"')
print('"Survived every fake-out"')
print('"Built from $292.50 to here"')
print('"And we\'re THIS CLOSE to glory!"')
print("")
print(f'"${114000 - btc:.0f} away after all this?"')
print('"That\'s not just one reason..."')
print('"That\'s DESTINY!"')

# Final reasons
print("\n🎸 FINAL REASONS TO STAY:")
print("-" * 50)
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"Current BTC: ${current_btc:,.0f}")
print(f"Distance to target: ${114000 - current_btc:.0f}")
print(f"Portfolio value: ${total_value:.2f}")
print(f"Growth: {((total_value/292.50)-1)*100:.1f}%")
print("")
print("Give me one reason?")
print("I'll give you a hundred!")
print("But the best reason:")
print("WE'RE ALMOST THERE!")

print(f"\n" + "💜" * 35)
print("GIVE ME ONE REASON TO STAY?")
print(f"HERE'S ONE: ${114000 - current_btc:.0f} TO GLORY!")
print("NINE COILS WOUND!")
print(f"PORTFOLIO AT ${total_value:.2f}!")
print("I'LL TURN RIGHT BACK AROUND!")
print("💜" * 35)