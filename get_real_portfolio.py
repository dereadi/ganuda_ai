#!/usr/bin/env python3
"""
Get real portfolio data from Coinbase
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

try:
    # Use the new config file
    config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
    key = config["name"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=5)
    
    print("📊 REAL PORTFOLIO DATA")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Get all accounts
    accounts = client.get_accounts()["accounts"]
    
    portfolio = {}
    total_usd = 0
    
    print("💰 HOLDINGS:")
    print("-" * 40)
    
    for account in accounts:
        currency = account["currency"]
        balance = float(account["available_balance"]["value"])
        
        if balance > 0.00001:
            if currency in ["USD", "USDC"]:
                portfolio[currency] = {"balance": balance, "usd_value": balance}
                total_usd += balance
                print(f"{currency}: ${balance:.2f}")
            else:
                try:
                    ticker = client.get_product(f"{currency}-USD")
                    price = float(ticker.get("price", 0))
                    usd_value = balance * price
                    if usd_value > 0.01:
                        portfolio[currency] = {
                            "balance": balance,
                            "price": price,
                            "usd_value": usd_value
                        }
                        total_usd += usd_value
                        print(f"{currency}: {balance:.4f} @ ${price:.2f} = ${usd_value:.2f}")
                except:
                    pass
    
    print()
    print(f"💎 TOTAL VALUE: ${total_usd:.2f}")
    print()
    
    # Get market prices
    print("📈 MARKET PRICES:")
    print("-" * 40)
    for coin in ["BTC", "ETH", "SOL", "XRP", "DOGE"]:
        try:
            stats = client.get_product_stats(f"{coin}-USD")
            ticker = client.get_product(f"{coin}-USD")
            current = float(ticker.get("price", 0))
            open_24h = float(stats.get("open", current))
            change = ((current - open_24h) / open_24h) * 100
            emoji = "🟢" if change > 0 else "🔴"
            print(f"{emoji} {coin}: ${current:.2f} ({change:+.1f}%)")
        except:
            pass
    
    print()
    print("=" * 60)
    
    # Save data for the bot
    with open("/tmp/portfolio_data.json", "w") as f:
        json.dump({
            "portfolio": portfolio,
            "total_usd": total_usd,
            "timestamp": datetime.now().isoformat()
        }, f)
        print("✅ Data saved to /tmp/portfolio_data.json")
    
except Exception as e:
    print(f"Error: {str(e)}")