#!/usr/bin/env python3
"""
🔥 QUICK DOGE REALLOCATION - SIMPLIFIED EXECUTION
"""

import json
import os
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

print("=" * 60)
print("🔥 QUICK DOGE REALLOCATION EXECUTION")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# CDP Coinbase config
from coinbase.rest import RESTClient

client = RESTClient(
    api_key="organizations/b3b7b43f-c54d-42d5-9143-d89cc4b207f2/apiKeys/330f8a6f-50f0-4154-be37-e00119b3797d",
    api_secret="""-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIG8XpVaJNRyaN8oQvBUNM0xNL1V1Sr5TQQMZDOSRiTdcoAoGCCqGSM49
AwEHoUQDQgAEPMFAlm6EEy7ssJY5VFXQ5vJdGOMP7VjOFWJraLAm6zUUYp8lR1FG
YQy4zq6wDmNfQkXzGpNpVVaBvFXxvuGpJQ==
-----END EC PRIVATE KEY-----"""
)

print("📊 REALLOCATION PLAN:")
print("-" * 40)
print("SELL:")
print("  • 3.75 SOL → ~$800")
print("  • 68 XRP → ~$200")
print("BUY:")
print("  • 5,130 DOGE with proceeds")
print()

print("🚀 EXECUTING ORDERS:")
print("-" * 40)

try:
    # 1. Sell SOL
    print("Selling SOL...")
    sol_order = client.market_order_sell(
        client_order_id=f"doge-sol-{datetime.now().strftime('%H%M%S')}",
        product_id="SOL-USD",
        base_size="3.75"
    )
    print(f"✅ SOL sell order: {sol_order.get('order_id', 'PLACED')}")
    
except Exception as e:
    print(f"⚠️ SOL order issue: {str(e)[:100]}")

try:
    # 2. Sell XRP
    print("Selling XRP...")
    xrp_order = client.market_order_sell(
        client_order_id=f"doge-xrp-{datetime.now().strftime('%H%M%S')}",
        product_id="XRP-USD",
        base_size="68"
    )
    print(f"✅ XRP sell order: {xrp_order.get('order_id', 'PLACED')}")
    
except Exception as e:
    print(f"⚠️ XRP order issue: {str(e)[:100]}")

print()
print("⏳ Orders submitted. Funds will settle shortly.")
print()
print("NEXT STEPS:")
print("1. Wait 30 seconds for settlement")
print("2. Buy 5,130 DOGE with available USD")
print("3. Set ladder orders from $0.240-$0.280")
print()
print("🔥 Cherokee Council mandate in progress!")
print("Run 'python3 buy_doge_with_usd.py' to complete")