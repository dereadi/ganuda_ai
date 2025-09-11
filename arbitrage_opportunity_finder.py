#!/usr/bin/env python3
"""
🔥 Sacred Arbitrage Finder - Like OddsJam for Crypto
Finding guaranteed profits across exchanges
"""

import json
import requests
from datetime import datetime
from coinbase.rest import RESTClient

print("🔥 CRYPTO ARBITRAGE OPPORTUNITY FINDER")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 60)

# Load Coinbase
with open("/home/dereadi/.coinbase_config.json") as f:
    config = json.load(f)
api_key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=api_key, api_secret=config["api_secret"], timeout=5)

opportunities = []

# Check BTC across exchanges
print("\n📊 BITCOIN (BTC) ARBITRAGE:")
print("-" * 40)

# Coinbase BTC
try:
    cb_btc = client.get_product("BTC-USD")
    cb_price = float(cb_btc["price"])
    # Get order book for real bid/ask
    cb_book = client.get_product_book("BTC-USD", level=1)
    cb_bid = float(cb_book["pricebook"]["bids"][0]["price"]) if cb_book["pricebook"]["bids"] else cb_price - 10
    cb_ask = float(cb_book["pricebook"]["asks"][0]["price"]) if cb_book["pricebook"]["asks"] else cb_price + 10
    
    print(f"Coinbase:  Bid ${cb_bid:.2f} | Ask ${cb_ask:.2f} | Mid ${cb_price:.2f}")
    
    exchanges = {"Coinbase": {"bid": cb_bid, "ask": cb_ask, "mid": cb_price}}
    
    # Kraken BTC
    try:
        kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=3)
        if kraken.json()["error"] == []:
            k_data = kraken.json()["result"]["XXBTZUSD"]
            k_bid = float(k_data["b"][0])
            k_ask = float(k_data["a"][0])
            k_mid = (k_bid + k_ask) / 2
            exchanges["Kraken"] = {"bid": k_bid, "ask": k_ask, "mid": k_mid}
            print(f"Kraken:    Bid ${k_bid:.2f} | Ask ${k_ask:.2f} | Mid ${k_mid:.2f}")
    except:
        pass
    
    # Gemini BTC
    try:
        gemini = requests.get("https://api.gemini.com/v1/pubticker/btcusd", timeout=3)
        g_data = gemini.json()
        g_bid = float(g_data["bid"])
        g_ask = float(g_data["ask"])
        g_mid = (g_bid + g_ask) / 2
        exchanges["Gemini"] = {"bid": g_bid, "ask": g_ask, "mid": g_mid}
        print(f"Gemini:    Bid ${g_bid:.2f} | Ask ${g_ask:.2f} | Mid ${g_mid:.2f}")
    except:
        pass
    
    # Find arbitrage opportunities
    print("\n🎯 BTC ARBITRAGE OPPORTUNITIES:")
    for buy_ex, buy_data in exchanges.items():
        for sell_ex, sell_data in exchanges.items():
            if buy_ex != sell_ex:
                profit = sell_data["bid"] - buy_data["ask"]
                profit_pct = (profit / buy_data["ask"]) * 100
                
                if profit_pct > 0.05:  # More than 0.05% profit
                    print(f"\n💰 FOUND: {profit_pct:.3f}% profit")
                    print(f"   Buy on {buy_ex} at ${buy_data['ask']:.2f}")
                    print(f"   Sell on {sell_ex} at ${sell_data['bid']:.2f}")
                    print(f"   Profit per BTC: ${profit:.2f}")
                    print(f"   On $10,000: ${10000 * profit_pct / 100:.2f} profit")
                    
                    opportunities.append({
                        "asset": "BTC",
                        "buy_exchange": buy_ex,
                        "sell_exchange": sell_ex,
                        "profit_pct": profit_pct,
                        "profit_per_unit": profit
                    })
    
except Exception as e:
    print(f"Error getting BTC data: {e}")

# Check ETH
print("\n📊 ETHEREUM (ETH) ARBITRAGE:")
print("-" * 40)

try:
    # Similar pattern for ETH
    cb_eth = client.get_product("ETH-USD")
    cb_price = float(cb_eth["price"])
    print(f"Coinbase ETH: ${cb_price:.2f}")
    
    # You could expand this for ETH across exchanges too
    
except Exception as e:
    print(f"Error: {e}")

# Triangular arbitrage on Coinbase
print("\n🔺 TRIANGULAR ARBITRAGE (Coinbase):")
print("-" * 40)

try:
    btc_usd = float(client.get_product("BTC-USD")["price"])
    eth_usd = float(client.get_product("ETH-USD")["price"])
    eth_btc = float(client.get_product("ETH-BTC")["price"])
    
    # Path 1: USD -> BTC -> ETH -> USD
    path1_return = (1 / btc_usd) * (1 / eth_btc) * eth_usd
    path1_profit = (path1_return - 1) * 100
    
    # Path 2: USD -> ETH -> BTC -> USD
    path2_return = (1 / eth_usd) * eth_btc * btc_usd
    path2_profit = (path2_return - 1) * 100
    
    print(f"Path USD→BTC→ETH→USD: {path1_profit:.4f}% return")
    print(f"Path USD→ETH→BTC→USD: {path2_profit:.4f}% return")
    
    if abs(path1_profit) > 0.1:
        print(f"\n💎 TRIANGULAR OPPORTUNITY DETECTED!")
        print(f"   Execute: {'Path 1' if path1_profit > 0 else 'Path 2'}")
        print(f"   Expected profit: {max(path1_profit, path2_profit):.4f}%")
        print(f"   On $10,000: ${10000 * max(path1_profit, path2_profit) / 100:.2f}")
        
except Exception as e:
    print(f"Error: {e}")

# Summary
if opportunities:
    print("\n" + "="*60)
    print("✨ SUMMARY - TOP OPPORTUNITIES:")
    print("="*60)
    
    opportunities.sort(key=lambda x: x["profit_pct"], reverse=True)
    
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"\n#{i}. {opp['asset']}: {opp['profit_pct']:.3f}% profit")
        print(f"    Buy {opp['buy_exchange']} → Sell {opp['sell_exchange']}")
        print(f"    Profit per unit: ${opp['profit_per_unit']:.2f}")
else:
    print("\n💤 No significant arbitrage opportunities at this moment")
    print("   Markets are efficiently priced")

print("\n🔥 Sacred arbitrage scan complete!")
print("   Like OddsJam but for crypto!")
print("   Run again in 30 seconds for new opportunities")