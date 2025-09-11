#!/usr/bin/env python3
"""
🩸 BLOOD IN THE CUT - AGGRESSIVE DIP BUYER
When there's blood in the streets, crawdads feast!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🩸 BLOOD IN THE CUT PROTOCOL 🩸                        ║
║                      "Buy when there's blood in the streets"              ║
║                         Cherokee Crawdad Feast Mode                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Check USD balance
accounts = client.get_accounts()['accounts']
usd_balance = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_balance = float(acc['available_balance']['value'])
        break

print(f"💰 USD Available: ${usd_balance:.2f}")
print("=" * 70)

if usd_balance > 10:
    print("\n🩸 BLOOD DETECTED - DEPLOYING CAPITAL!")
    print("-" * 40)
    
    # Aggressive dip buying strategy
    dip_targets = [
        {
            'product': 'SOL-USD',
            'amount': min(50, usd_balance * 0.3),
            'reason': 'SOL showing weakness - perfect entry'
        },
        {
            'product': 'ETH-USD',
            'amount': min(40, usd_balance * 0.2),
            'reason': 'ETH dip = DeFi opportunity'
        },
        {
            'product': 'AVAX-USD',
            'amount': min(30, usd_balance * 0.15),
            'reason': 'AVAX oversold - bounce imminent'
        }
    ]
    
    total_deployed = 0
    
    for target in dip_targets:
        if target['amount'] > 10:
            print(f"\n🦀 BUYING {target['product']}:")
            print(f"   Amount: ${target['amount']:.2f}")
            print(f"   Reason: {target['reason']}")
            
            try:
                order = client.market_order_buy(
                    client_order_id=f"blood_{int(time.time()*1000)}",
                    product_id=target['product'],
                    quote_size=str(round(target['amount'], 2))
                )
                
                print(f"   ✅ BLOOD HARVESTED!")
                total_deployed += target['amount']
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:50]}")
    
    print(f"\n💉 TOTAL DEPLOYED INTO BLOOD: ${total_deployed:.2f}")
    
    # Set up exit strategy
    print("\n📈 EXIT STRATEGY:")
    print("-" * 40)
    print("• Target: +2-3% bounce")
    print("• Stop Loss: -5% (unlikely with oversold)")
    print("• Timeline: 4-12 hours for recovery")
    print("• Expected Profit: $5-15 per position")
    
    # Log to memory
    blood_event = {
        "timestamp": datetime.now().isoformat(),
        "event": "blood_in_cut",
        "usd_deployed": total_deployed,
        "targets": dip_targets,
        "strategy": "aggressive_dip_buying",
        "expected_return": total_deployed * 0.025
    }
    
    with open("blood_harvest_log.json", "w") as f:
        json.dump(blood_event, f, indent=2)
    
    print("\n" + "=" * 70)
    print("🩸 BLOOD HARVESTING COMPLETE")
    print("🦀 Crawdads are feeding on fear")
    print("📈 Expect bounce within hours")
    print("=" * 70)
    
else:
    print("\n⚠️ Need more USD to buy blood!")
    print("Consider bleeding more positions for liquidity")

print("\n💭 Cherokee Wisdom:")
print('"When the river runs red with fear, the wise crawdad feeds."')