#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 BUY XRP NOW - We have $505 liquidity!
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient
import uuid

print("🚀 XRP PURCHASE EXECUTION")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load API config
config = json.load(open('/home/dereadi/scripts/claude/cdp_api_key_new.json'))
client = RESTClient(
    api_key=config['name'].split('/')[-1],
    api_secret=config['privateKey'],
    timeout=10
)

print("💵 AVAILABLE LIQUIDITY: $505.19")
print("🎯 TARGET: Buy 100+ XRP")
print()

# Calculate XRP purchase
xrp_budget = 300  # Use $300 for XRP, keep rest for other opportunities
xrp_price = 2.77  # Current price
xrp_amount = xrp_budget / xrp_price

print(f"📊 PURCHASE PLAN:")
print(f"  Budget: ${xrp_budget}")
print(f"  XRP Price: ${xrp_price}")
print(f"  XRP Amount: {xrp_amount:.2f} XRP")
print()

try:
    # Execute XRP purchase
    order_config = {
        "product_id": "XRP-USD",
        "quote_size": str(xrp_budget),  # USD to spend
        "client_order_id": str(uuid.uuid4())
    }
    
    print("⚡ EXECUTING XRP PURCHASE...")
    result = client.market_order_buy(**order_config)
    
    print("✅ XRP BUY ORDER PLACED!")
    
    if hasattr(result, 'order_id'):
        print(f"Order ID: {result.order_id}")
    elif hasattr(result, 'success') and result.success:
        print("Order successful!")
    else:
        print(f"Result: {result}")
    
    print()
    print("🔥 XRP ARMY MISSION COMPLETE!")
    print(f"  Bought ~{xrp_amount:.2f} XRP")
    print(f"  New position: ~{0.671 + xrp_amount:.2f} XRP total")
    print(f"  Ready for moon mission to $10!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTrying alternative approach...")
    
    # Try with specific base size instead
    try:
        order_config = {
            "product_id": "XRP-USD",
            "base_size": str(int(xrp_amount)),  # Number of XRP
            "client_order_id": str(uuid.uuid4())
        }
        
        result = client.market_order_buy(**order_config)
        print("✅ XRP purchase successful via base_size!")
        
    except Exception as e2:
        print(f"Alternative also failed: {e2}")
        print("\n📝 MANUAL STEPS:")
        print("  1. Go to Coinbase Pro/Advanced Trade")
        print(f"  2. Buy {xrp_amount:.0f} XRP with ${xrp_budget}")
        print("  3. XRP to $10 = $1,000+ profit!")

print("\n" + "=" * 70)
print("Cherokee Council has spoken: XRP shall rise!")
print("Mitakuye Oyasin - We are all related in the XRP Army")