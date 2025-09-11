#!/usr/bin/env python3
"""
💰 LIQUIDITY CHECK
Real-time cash position analysis
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

print("💰 LIQUIDITY STATUS CHECK")
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
    
    if not cash_accounts:
        print("⚠️  NO LIQUIDITY FOUND!")
    
    print("-" * 40)
    print(f"TOTAL:  ${total_liquidity:10.2f}")
    print()
    
    # Liquidity analysis
    print("📊 LIQUIDITY ANALYSIS:")
    print("-" * 40)
    
    target_liquidity = 500  # Your target
    
    if total_liquidity < 50:
        print("🔴 CRITICAL - Almost no liquidity!")
        print("   ACTION: Urgent - sell some positions")
    elif total_liquidity < 250:
        print("🟠 LOW - Below minimum threshold")
        print("   ACTION: Consider taking some profits")
    elif total_liquidity < 500:
        print("🟡 MODERATE - Below target")
        print(f"   Need ${500 - total_liquidity:.2f} more for target")
    elif total_liquidity < 1000:
        print("🟢 GOOD - Target met")
        print("   Ready for opportunities")
    else:
        print("💚 EXCELLENT - Strong cash position")
        print("   Ready to deploy on dips")
    
    print()
    
    # Check crypto positions for potential liquidity
    print("🪙 POTENTIAL LIQUIDITY (if needed):")
    print("-" * 40)
    
    crypto_positions = []
    for account in accounts:
        currency = account["currency"]
        balance = float(account["available_balance"]["value"])
        
        if balance > 0.00001 and currency not in ["USD", "USDC", "USDT", "DAI", "BUSD"]:
            try:
                ticker = client.get_product(f"{currency}-USD")
                price = float(ticker.get("price", 0))
                value = balance * price
                if value > 10:  # Only show positions worth >$10
                    crypto_positions.append((currency, balance, price, value))
            except:
                pass
    
    # Sort by value
    crypto_positions.sort(key=lambda x: x[3], reverse=True)
    
    # Show top 5 positions that could be liquidated
    for i, (coin, amount, price, value) in enumerate(crypto_positions[:5]):
        print(f"{i+1}. {coin:6}: {amount:.4f} @ ${price:.2f} = ${value:.2f}")
    
    print()
    
    # Recommendations
    print("🎯 RECOMMENDATIONS:")
    print("-" * 40)
    
    if total_liquidity < 250:
        print("⚠️  IMMEDIATE ACTION NEEDED:")
        print("   1. Your liquidity is dangerously low")
        print("   2. Consider selling 10% of a position")
        print("   3. Target: Get back to $500 minimum")
        
        if crypto_positions:
            # Suggest which to sell
            suggested = crypto_positions[0]  # Largest position
            ten_percent = suggested[3] * 0.1
            print(f"\n   SUGGESTION: Sell 10% of {suggested[0]} (~${ten_percent:.2f})")
    
    elif total_liquidity < 500:
        print("📌 SUGGESTED ACTIONS:")
        print("   • Monitor for profit-taking opportunities")
        print("   • Set alerts for 5%+ gains to harvest")
        print(f"   • Need ${500 - total_liquidity:.2f} to reach target")
    
    else:
        print("✅ Liquidity healthy - maintain current levels")
        print("   • Ready to buy dips")
        print("   • Can weather volatility")
        print("   • Consider deploying if opportunities arise")
    
    print()
    print("=" * 60)
    print(f"💰 CURRENT LIQUIDITY: ${total_liquidity:.2f}")
    
    if total_liquidity < 250:
        print("🚨 STATUS: URGENT - INCREASE LIQUIDITY")
    elif total_liquidity < 500:
        print("⚠️  STATUS: MONITOR CLOSELY")
    else:
        print("✅ STATUS: HEALTHY")
    
    print("=" * 60)
    
except Exception as e:
    print(f"Error checking liquidity: {str(e)}")
    print()
    print("FALLBACK ESTIMATE:")
    print("Based on portfolio value of ~$12,774")
    print("Assuming ~$500 target liquidity")
    print("Status: CHECK MANUALLY")