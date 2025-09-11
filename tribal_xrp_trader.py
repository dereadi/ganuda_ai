#!/usr/bin/env python3
import sys
import os
import json
import time

sys.path.append('/home/dereadi/scripts/claude')
os.chdir('/home/dereadi/scripts/claude')

print("🔥 Tribal XRP Integration Active")

# Load XRP config
with open('tribal_xrp_config.json', 'r') as f:
    config = json.load(f)

print(f"Trading core four: {config['core_positions']}")

# Import and initialize
try:
    from coinbase.rest import RESTClient
    
    with open('cdp_api_key_new.json', 'r') as f:
        api_config = json.load(f)
    
    client = RESTClient(
        api_key=api_config.get('api_key'),
        api_secret=api_config.get('api_secret')
    )
    
    print("Connected - XRP integration ready")
    
    # Check balances
    accounts = client.get_accounts()
    usd_available = 0
    
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd_available = float(account['available_balance']['value'])
            break
    
    if usd_available > 100:
        # Allocate to core four
        allocation = usd_available / 4
        
        core_orders = [
            ('BTC-USD', allocation),
            ('ETH-USD', allocation),
            ('SOL-USD', allocation),
            ('XRP-USD', allocation)  # XRP gets EQUAL allocation!
        ]
        
        for product, amount in core_orders:
            if amount > 10:
                print(f"Allocating ${amount:.2f} to {product}")
                try:
                    order = client.place_order(
                        product_id=product,
                        side='buy',
                        quote_size=str(round(amount, 2))
                    )
                    print(f"✅ {product} order placed")
                    time.sleep(1)
                except Exception as e:
                    print(f"Note: {product} - {str(e)[:50]}")
    
    print("XRP integrated into core trading!")
    
except Exception as e:
    print(f"Using enhanced crawdad system: {e}")
    
    # Start crawdad with XRP focus
    import subprocess
    subprocess.Popen([
        'python3',
        'quantum_crawdad_live_trader.py'
    ])
