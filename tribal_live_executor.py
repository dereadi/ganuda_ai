#!/usr/bin/env python3
import os
import sys
import json
import time

os.chdir('/home/dereadi/scripts/claude')
sys.path.append('/home/dereadi/scripts/claude')

print("🔥 Tribal Execution Active")

# Load execution plan
with open('tribal_execution_plan.json', 'r') as f:
    plan = json.load(f)

# Import trading module
try:
    from coinbase.rest import RESTClient
    
    # Load API config
    with open('cdp_api_key_new.json', 'r') as f:
        config = json.load(f)
    
    # Connect to Coinbase
    client = RESTClient(
        api_key=config.get('api_key'),
        api_secret=config.get('api_secret')
    )
    
    print("Connected to Coinbase")
    
    # Execute trades based on tribal plan
    for product, amount in plan['allocations'].items():
        if amount > 10:
            print(f"Executing {product}: ${amount}")
            try:
                # Place market buy
                order = client.place_order(
                    product_id=product,
                    side='buy',
                    quote_size=str(amount)
                )
                print(f"✅ {product} order placed")
                time.sleep(1)  # Respect rate limits
            except Exception as e:
                print(f"Note: {product} - {str(e)[:50]}")
    
    print("Tribal execution complete!")
    
except Exception as e:
    print(f"Using quantum crawdad system: {e}")
    
    # Start enhanced crawdad with proper config
    import subprocess
    
    # Create config for larger trades
    crawdad_config = {
        "trade_size": 500,
        "targets": list(plan['allocations'].keys()),
        "mode": "alt_spread"
    }
    
    with open('crawdad_enhanced_config.json', 'w') as f:
        json.dump(crawdad_config, f)
    
    # Launch enhanced crawdad
    subprocess.Popen([
        'python3', 
        'quantum_crawdad_autonomous_trader.py'
    ])
    
    print("Enhanced crawdad system launched")
