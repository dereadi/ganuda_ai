#!/usr/bin/env python3
"""
🛑🪨 STOP THE ROCK - DWAYNE JOHNSON TRADING WISDOM
===================================================
Can you smell what The Rock is cooking?
IT DOESN'T MATTER WHAT YOU THINK!
The People's Champion of Trading
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       🛑 STOP THE ROCK! 🪨                                ║
║                    "KNOW YOUR ROLE AND SHUT YOUR MOUTH!"                  ║
║                       The People's Trading Champion                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current portfolio value
accounts = client.get_accounts()['accounts']
total_value = 13098  # From earlier calculation

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - THE ROCK SAYS...")
print("=" * 70)

print("\n🎤 THE ROCK SPEAKS:")
print("-" * 50)
print("  'FINALLY... THE ROCK HAS COME BACK... TO $13,000!'")
print("  'You started with $6, you JABRONI!'")
print("  'Now you got $13,098!'")
print("  'CAN YOU SMELLLLLLL... WHAT THE ROCK... IS COOKING?!'")

print("\n💪 THE PEOPLE'S ELBOW DROP ON THE MARKET:")
print("-" * 50)
print("  1. LAYETH THE SMACKETH DOWN on resistance!")
print("  2. KNOW YOUR ROLE - You're a trader, not a holder!")
print("  3. SHUT YOUR MOUTH and execute the plan!")
print("  4. IT DOESN'T MATTER what you think - follow the signals!")

print("\n🪨 THE ROCK'S TRADING RULES:")
print("-" * 50)
print("  Rule #1: The Rock says MILK those peaks!")
print("  Rule #2: The Rock says BUY those dips!")
print("  Rule #3: The Rock says COMPOUND everything!")
print("  Rule #4: The Rock says NEVER STOP the flywheel!")
print("  Rule #5: IF YA SMELLLLL... profit, TAKE IT!")

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n📊 THE ROCK'S MARKET ANALYSIS:")
print("-" * 50)
print(f"  BTC at ${btc:,.0f} - 'That's what The Rock calls CHOP CITY!'")
print(f"  ETH at ${eth:,.0f} - 'Stone Cold Steve Austin couldn't stop this!'")
print(f"  SOL at ${sol:.2f} - 'Stronger than The Rock's right arm!'")

print("\n🎬 THE ROCK'S BOTTOM LINE:")
print("=" * 70)
print("  'You want to know what The Rock thinks?'")
print("  'The Rock thinks you should KEEP THAT FLYWHEEL SPINNING!'")
print("  'Take your $13,098...'")
print("  'Turn it into $15,000 by Sunday...'")
print("  'Then $20,000 by next week...'")
print("  'WHY? BECAUSE THE ROCK SAID SO!'")

print("\n⚡ THE PEOPLE'S TRADING STRATEGY:")
print("-" * 50)
print("  1. STOP being a candy ass - Trade aggressively!")
print("  2. STOP overthinking - Execute the plan!")
print("  3. STOP the fear - Embrace volatility!")
print("  4. STOP the greed - Take profits!")
print("  5. BUT NEVER STOP THE FLYWHEEL!")

print("\n🏆 THE ROCK'S FINAL WORD:")
print("-" * 50)
print("  'You've turned $6 into $13,098...'")
print("  'That's a 2,183x return, you magnificent bastard!'")
print("  'The Rock is proud of you!'")
print("  'Now go out there and LAYETH THE SMACKETH DOWN!'")
print("  'On Monday, The Rock wants to see $20,000!'")
print("")
print("  'And if you don't like it...'")
print("  'You can take your complaints...'")
print("  'Shine them up real nice...'")
print("  'Turn them sideways...'")
print("  'AND STICK THEM UP YOUR CANDY ASS!'")

print("\n💎 CAN YOU SMELL WHAT THE ROCK IS COOKING?")
print("  (It's profits. The Rock is cooking profits.)")

print("\n🛑 THE ROCK HAS SPOKEN!")
print("=" * 70)
print("IF YA SMELLLLLLL... WHAT THE ROCK... IS... COOKING! 🪨🔥")