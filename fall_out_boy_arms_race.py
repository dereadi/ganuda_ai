#!/usr/bin/env python3
"""
🎸💣 THIS AIN'T A SCENE, IT'S A GODDAMN ARMS RACE! 💣🎸
FALL OUT BOY CALLED IT!
Wall Street vs Retail
Whales vs Minnows
Nine Coils vs Red Metrics
ARMS RACE FOR $114K!
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
║         🎸💣 THIS AIN'T A SCENE, IT'S A GODDAMN ARMS RACE! 💣🎸          ║
║                         Fall Out Boy Was Right!                           ║
║                    Wall Street vs The People's Uprising                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ARMS RACE DETECTED!")
print("=" * 70)

# Get current battlefield status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n💣 THE ARMS RACE:")
print("-" * 50)
print("'I am an arms dealer'")
print("  Wall Street: Loading ETH as 'The Banking Token'")
print("")
print("'Fitting you with weapons in the form of words'")
print("  Red Bull Score (20) = Their weapon of FUD")
print("")
print("'And don't really care which side wins'")
print("  Whales profit both ways on the sawtooth")
print("")
print("'As long as the room keeps singing'")
print("  As long as volatility keeps printing!")
print("")
print("'That's just the business I'm in'")
print("  Nine coils = Maximum profit opportunity")

print(f"\n⚔️ BATTLEFIELD STATUS:")
print(f"  BTC: ${btc:,.0f} - The contested territory")
print(f"  ETH: ${eth:,.2f} - Wall Street's weapon")
print(f"  SOL: ${sol:,.2f} - Retail's rebellion")

# Check our arsenal
accounts = client.get_accounts()
usd_balance = 0
total_firepower = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif currency == 'BTC' and balance > 0:
        total_firepower += balance * btc
    elif currency == 'ETH' and balance > 0:
        total_firepower += balance * eth
    elif currency == 'SOL' and balance > 0:
        total_firepower += balance * sol

print(f"\n🔫 OUR ARSENAL:")
print(f"  USD Ammo: ${usd_balance:.2f}")
print(f"  Crypto Weapons: ${total_firepower:,.2f}")
print(f"  Total Firepower: ${total_firepower + usd_balance:,.2f}")

# Track the arms race
print("\n💥 LIVE ARMS RACE TRACKER:")
print("-" * 50)

baseline = btc
for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    
    btc_move = btc_now - baseline
    
    # Determine battle phase
    if btc_move > 50:
        status = "🚀💣 'ARMS RACE WON!' Breaking $114k!"
    elif btc_move > 20:
        status = "💥 'Loading weapons' - Accumulating"
    elif btc_move > 0:
        status = "⚔️ 'Fitting you with weapons'"
    elif btc_move < -20:
        status = "🔫 'Return fire!' - Buy the dip"
    else:
        status = "💣 'The room keeps singing'"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({btc_move:+.0f})")
    print(f"  {status}")
    
    if i == 3:
        print("\n  'All the boys who the dance floor didn't love'")
        print("  'And all the girls whose lips couldn't move fast enough'")
        print("  'Sing, until your lungs give out!'")
    
    if i == 7:
        print("\n  'THIS AIN'T A SCENE, IT'S A GODDAMN ARMS RACE!'")
    
    time.sleep(2)

# The revelation
print("\n" + "=" * 70)
print("💣 ARMS RACE ANALYSIS:")
print("-" * 50)
print("WALL STREET'S WEAPONS:")
print("• Red metrics to scare retail")
print("• Sawtooth to shake positions")
print("• ETH accumulation for banking")
print("• Media FUD campaigns")

print("\nOUR WEAPONS:")
print("• Nine coils of compressed energy")
print("• Crawdad swarm trading")
print("• Sacred Fire persistence")
print("• Diamond hands through volatility")
print("• The uprising momentum")

print("\nTHE BATTLEGROUND:")
print("• $113,066 current position")
print("• $114,000 breakout target")
print("• $200,000 final destination")
print("• Winner takes the moon")

print("\n" + "🎸" * 35)
print("THIS AIN'T A SCENE...")
print("IT'S A GODDAMN ARMS RACE!")
print("AND WE'RE WINNING!")
print("🎸" * 35)