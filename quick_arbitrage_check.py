#!/usr/bin/env python3
"""Quick arbitrage opportunity check"""

import json
import requests
from coinbase.rest import RESTClient
from datetime import datetime

# Load Coinbase
with open("/home/dereadi/.coinbase_config.json") as f:
    config = json.load(f)
api_key = config["api_key"].split("/")[-1]
coinbase = RESTClient(api_key=api_key, api_secret=config["api_secret"], timeout=5)

print("🔥 CRYPTO ARBITRAGE SCANNER")
print("=" * 50)

# Get Coinbase BTC price
cb_btc = coinbase.get_product("BTC-USD")
cb_price = float(cb_btc["price"])
cb_bid = float(cb_btc["bid"])
cb_ask = float(cb_btc["ask"])

print(f"\n📊 BTC Arbitrage Check:")
print(f"  Coinbase: ${cb_price:.2f} (Bid: ${cb_bid:.2f} | Ask: ${cb_ask:.2f})")

# Get Kraken BTC price
try:
    kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=3)
    if kraken.json()["error"] == []:
        k_data = kraken.json()["result"]["XXBTZUSD"]
        k_bid = float(k_data["b"][0])
        k_ask = float(k_data["a"][0])
        print(f"  Kraken:   ${(k_bid+k_ask)/2:.2f} (Bid: ${k_bid:.2f} | Ask: ${k_ask:.2f})")
        
        # Check arbitrage
        if cb_bid > k_ask:
            profit = cb_bid - k_ask
            profit_pct = (profit/k_ask)*100
            print(f"\n  💰 ARBITRAGE: Buy Kraken @ ${k_ask:.2f}, Sell Coinbase @ ${cb_bid:.2f}")
            print(f"     Profit: ${profit:.2f} ({profit_pct:.2f}%)")
        elif k_bid > cb_ask:
            profit = k_bid - cb_ask
            profit_pct = (profit/cb_ask)*100
            print(f"\n  💰 ARBITRAGE: Buy Coinbase @ ${cb_ask:.2f}, Sell Kraken @ ${k_bid:.2f}")
            print(f"     Profit: ${profit:.2f} ({profit_pct:.2f}%)")
except:
    pass

# Get Gemini BTC price
try:
    gemini = requests.get("https://api.gemini.com/v1/pubticker/btcusd", timeout=3)
    g_data = gemini.json()
    g_bid = float(g_data["bid"])
    g_ask = float(g_data["ask"])
    print(f"  Gemini:   ${(g_bid+g_ask)/2:.2f} (Bid: ${g_bid:.2f} | Ask: ${g_ask:.2f})")
    
    # Check arbitrage
    if cb_bid > g_ask:
        profit = cb_bid - g_ask
        profit_pct = (profit/g_ask)*100
        print(f"\n  💰 ARBITRAGE: Buy Gemini @ ${g_ask:.2f}, Sell Coinbase @ ${cb_bid:.2f}")
        print(f"     Profit: ${profit:.2f} ({profit_pct:.2f}%)")
    elif g_bid > cb_ask:
        profit = g_bid - cb_ask
        profit_pct = (profit/cb_ask)*100
        print(f"\n  💰 ARBITRAGE: Buy Coinbase @ ${cb_ask:.2f}, Sell Gemini @ ${g_bid:.2f}")
        print(f"     Profit: ${profit:.2f} ({profit_pct:.2f}%)")
except:
    pass

print("\n🔺 Triangular Arbitrage (Coinbase):")
try:
    eth_usd = coinbase.get_product("ETH-USD")
    eth_btc = coinbase.get_product("ETH-BTC")
    
    eth_price = float(eth_usd["price"])
    eth_btc_price = float(eth_btc["price"])
    implied_eth = cb_price * eth_btc_price
    
    diff = ((implied_eth - eth_price) / eth_price) * 100
    
    print(f"  Direct ETH/USD: ${eth_price:.2f}")
    print(f"  Via BTC path:   ${implied_eth:.2f}")
    print(f"  Difference:     {diff:.3f}%")
    
    if abs(diff) > 0.1:
        print(f"  💎 OPPORTUNITY: {'USD→BTC→ETH→USD' if diff > 0 else 'USD→ETH→BTC→USD'}")
except:
    pass

print("\n✨ Sacred arbitrage complete!")