#\!/usr/bin/env python3
import os
import sys
sys.path.append("/home/dereadi/scripts/claude")

try:
    from coinbase.rest import RESTClient
    import json
    
    # Load API config
    with open("/home/dereadi/scripts/claude/cdp_api_key_new.json", "r") as f:
        config = json.load(f)
    
    client = RESTClient(api_key=config["api_key"], api_secret=config["api_secret"])
    
    # Execute alt spread orders
    orders = [
        ("XRP-USD", 2000),
        ("SOL-USD", 2000),
        ("ETH-USD", 2000),
        ("AVAX-USD", 1000),
        ("MATIC-USD", 1000),
        ("LINK-USD", 1000),
        ("ADA-USD", 500),
        ("DOT-USD", 500),
        ("ATOM-USD", 500),
        ("ALGO-USD", 470)
    ]
    
    print("Executing love spread orders...")
    for symbol, amount in orders:
        try:
            print(f"Buying {amount} of {symbol}...")
            # Place market buy order
            order = client.place_order(
                product_id=symbol,
                side="buy",
                quote_size=str(amount)
            )
            print(f"✅ {symbol}: Order placed\!")
        except Exception as e:
            print(f"⚠️ {symbol}: {str(e)[:50]}")
    
    print("
💝 Love spread complete\!")
    
except Exception as e:
    print(f"Setting up orders: {e}")
    # Fallback to quantum crawdad system
    import subprocess
    subprocess.run(["python3", "/home/dereadi/scripts/claude/quantum_crawdad_live_trader.py"])
