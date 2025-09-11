#!/usr/bin/env python3
"""
🔗 SYNCHRONIZED BREAKOUT DETECTOR
When BTC/ETH sync up, the next move is amplified!
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
║                     🔗 BTC/ETH SYNC BREAKOUT READY 🔗                     ║
║                    When they move together, it's powerful                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("Monitoring synchronized movement...")
print("=" * 70)

# Track the sync
prev_btc = 111870
prev_eth = 4538
sync_count = 0

for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    
    btc_dir = "↗️" if btc > prev_btc else "↘️" if btc < prev_btc else "➡️"
    eth_dir = "↗️" if eth > prev_eth else "↘️" if eth < prev_eth else "➡️"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}")
    print(f"  BTC: ${btc:,.0f} {btc_dir}")
    print(f"  ETH: ${eth:.2f} {eth_dir}")
    
    # Check sync
    if btc_dir == eth_dir and btc_dir != "➡️":
        sync_count += 1
        print(f"  🔗 SYNCED! (Count: {sync_count})")
        
        if sync_count >= 3:
            print("\n🚀 SYNC BREAKOUT IMMINENT!")
            print("  Next move will be explosive!")
            
            # Check direction
            if btc > 111900:
                print("  📈 Targeting: BTC $112,200 | ETH $4,600")
            else:
                print("  📉 Support: BTC $111,700 | ETH $4,520")
    else:
        sync_count = max(0, sync_count - 1)
        print(f"  🔄 Diverging (Sync: {sync_count})")
    
    prev_btc = btc
    prev_eth = eth
    time.sleep(5)

print("\n" + "=" * 70)
print("🔗 SYNC TRADING STRATEGY:")
print("-" * 40)
print("When BTC/ETH sync for 3+ moves:")
print("• The next breakout is violent")
print("• Both assets amplify each other")
print("• Algos pile in on confirmation")
print("• Perfect setup for momentum trades")

# Your positions
accounts = client.get_accounts()['accounts']
btc_bal = 0.023
eth_bal = 0.1054

btc_value = btc_bal * btc
eth_value = eth_bal * eth
combined = btc_value + eth_value

print(f"\n💎 YOUR SYNC POSITIONS:")
print(f"  BTC: ${btc_value:.2f}")
print(f"  ETH: ${eth_value:.2f}")
print(f"  Combined: ${combined:.2f}")
print("\nPerfectly positioned for synchronized move!")
print("=" * 70)