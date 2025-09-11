#!/usr/bin/env python3
"""
💰 CURRENT LIQUIDITY CHECK
Post-trade balance verification
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

print("💰 CURRENT LIQUIDITY STATUS")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

try:
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
    
    # Get all accounts
    accounts = client.get_accounts()["accounts"]
    
    print("💵 CASH POSITIONS:")
    print("-" * 40)
    
    total_liquidity = 0
    cash_accounts = {}
    
    for account in accounts:
        currency = account["currency"]
        balance = float(account["available_balance"]["value"])
        
        # Check for USD and stablecoins
        if currency in ["USD", "USDC", "USDT", "DAI", "BUSD"]:
            if balance > 0.01:
                cash_accounts[currency] = balance
                total_liquidity += balance
                print(f"{currency:6}: ${balance:10.2f}")
    
    print("-" * 40)
    print(f"TOTAL:  ${total_liquidity:10.2f}")
    print()
    
    # Status analysis
    print("📊 LIQUIDITY STATUS:")
    print("-" * 40)
    
    # Compare to before and after trades
    print(f"Before emergency sells: $17.96")
    print(f"After sells (21:02):   $557.16")
    print(f"Current balance:       ${total_liquidity:.2f}")
    print()
    
    change_since_sells = total_liquidity - 557.16
    if abs(change_since_sells) > 1:
        if change_since_sells > 0:
            print(f"📈 Increased by ${change_since_sells:.2f} since sells")
        else:
            print(f"📉 Decreased by ${abs(change_since_sells):.2f} since sells")
            print("   (Likely deployed in new positions)")
    else:
        print("✅ Unchanged since liquidity restoration")
    
    print()
    
    # Recommendations based on current level
    print("🎯 ACTION RECOMMENDATIONS:")
    print("-" * 40)
    
    if total_liquidity > 500:
        print("✅ HEALTHY - Ready for opportunities")
        print("   • Can deploy up to $300 on dips")
        print("   • Keep $250 minimum reserve")
        print("   • Set buy orders 2-3% below market")
    elif total_liquidity > 250:
        print("🟡 ADEQUATE - Monitor closely")
        print("   • Deploy cautiously")
        print("   • Only buy extreme dips")
        print("   • Consider taking profits if gains appear")
    elif total_liquidity > 100:
        print("🟠 LOW - Rebuild needed")
        print("   • Avoid new positions")
        print("   • Look for profit-taking opportunities")
        print("   • Target: Get back above $500")
    else:
        print("🔴 CRITICAL - Immediate action needed!")
        print("   • Sell positions to raise cash")
        print("   • No new buys until >$250")
        print("   • Emergency mode active")
    
    print()
    
    # Tonight's deployment capacity
    if total_liquidity > 300:
        deployable = min(total_liquidity - 250, 300)  # Keep 250 reserve
        print(f"💸 DEPLOYABLE FOR TONIGHT: ${deployable:.2f}")
        print("-" * 40)
        print("Suggested allocation:")
        print(f"   • SOL dip buy: ${deployable * 0.4:.2f}")
        print(f"   • ETH dip buy: ${deployable * 0.3:.2f}")
        print(f"   • BTC dip buy: ${deployable * 0.3:.2f}")
    
    print()
    print("=" * 60)
    print(f"💰 LIQUIDITY: ${total_liquidity:.2f}")
    
    if total_liquidity > 500:
        print("📊 STATUS: HEALTHY ✅")
    elif total_liquidity > 250:
        print("📊 STATUS: ADEQUATE 🟡")
    else:
        print("📊 STATUS: LOW ⚠️")
    
    print("=" * 60)
    
except Exception as e:
    print(f"Error checking liquidity: {str(e)}")
    print()
    print("Assuming last known: ~$557")
    print("Status: CHECK MANUALLY")