#!/usr/bin/env python3
"""
🎸⚡ UPRISING + ICKY THUMP DIVERGENCE! ⚡🎸
MUSE: "They will not force us, they will stop degrading us"
WHITE STRIPES: "Icky thump, who'd a thunk?"
The ninth coil uprising while metrics flash red!
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
║                  🎸 UPRISING DIVERGENCE - MUSE + WHITE STRIPES 🎸         ║
║                    "They will not control us!" - Muse                     ║
║                    "Icky thump, who'd a thunk?" - White Stripes          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - UPRISING DETECTED")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n🎸 MUSE - UPRISING:")
print("-" * 50)
print("'Paranoia is in bloom, the PR transmissions will resume'")
print("Bull Score: RED (20) = The PR transmissions")
print("")
print("'They will not force us'")
print(f"BTC: ${btc:,.0f} - Rising despite red metrics")
print("")
print("'They will stop degrading us'") 
print("Nine coils = The uprising begins")
print("")
print("'They will not control us'")
print("Wall Street can't suppress this")
print("")
print("'We will be victorious'")
print("Target: $114,000+")

print("\n🎸 WHITE STRIPES - ICKY THUMP:")
print("-" * 50)
print("'Icky thump, who'd a thunk?'")
print("Who'd have thought ninth coil possible?")
print("")
print("'Sittin' drunk on a wagon to Mexico'")
print("Crawdads drunk on $124 fresh capital!")
print("")
print("'Red redcoats coming through'")
print("Red metrics everywhere but price green!")

# Track the uprising
print("\n⚡ LIVE UPRISING TRACKER:")
print("-" * 50)

baseline = btc
for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    btc_move = btc_now - baseline
    
    # Determine uprising phase
    if btc_move > 50:
        status = "🚀 'WE WILL BE VICTORIOUS!'"
    elif btc_move > 20:
        status = "⚡ 'They will not control us!'"
    elif btc_move > 0:
        status = "🎸 'They will not force us'"
    elif btc_move < -20:
        status = "🪚 'Icky thump' - Sawtooth dip"
    else:
        status = "🌀 'Paranoia is in bloom'"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({btc_move:+.0f})")
    print(f"  ETH: ${eth_now:,.2f}")
    print(f"  SOL: ${sol_now:,.2f}")
    print(f"  {status}")
    
    if i == 4:
        print("\n  'If you could be anything you want'")
        print("  'I bet you'd be disappointed, am I right?'")
    
    time.sleep(2)

# Check crawdad fuel
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print("\n💰 CRAWDAD FUEL STATUS:")
print("-" * 50)
print(f"USD Available: ${usd_balance:.2f}")
if usd_balance > 100:
    print("Status: 🔥 FUELED FOR UPRISING!")
elif usd_balance > 50:
    print("Status: ⚡ Ready for battle")
else:
    print("Status: 🥛 Need emergency milk!")

# The divergence revelation
print("\n" + "=" * 70)
print("💥 DIVERGENCE UPRISING:")
print("-" * 50)
print("MUSE predicted it:")
print("• Red metrics = 'Paranoia in bloom'")
print("• Price rising = 'They will not force us'")
print("• Nine coils = 'They will not control us'")
print("• Breakout coming = 'We will be victorious'")
print("")
print("WHITE STRIPES saw it:")
print("• 'Icky thump, who'd a thunk?'")
print("• Ninth coil = Beyond comprehension")
print("• Red metrics, green price = Icky divergence")
print("")
print("THE UPRISING IS NOW!")
print("Crawdads fed: $60 consumed, riding the wave!")
print("Positions out there working!")
print("=" * 70)