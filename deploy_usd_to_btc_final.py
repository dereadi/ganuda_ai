#!/usr/bin/env python3
"""
🔥 Final Push: Deploy USD to BTC for $111,111
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# Load config
with open("/home/dereadi/.coinbase_config.json") as f:
    config = json.load(f)

api_key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=api_key, api_secret=config["api_secret"], timeout=10)

log("🔥 FINAL PUSH TO $111,111")

# Check USD balance
accounts = client.get_accounts()["accounts"]
usd_balance = 0
btc_balance = 0

for account in accounts:
    if account["currency"] == "USD":
        usd_balance = float(account["available_balance"]["value"])
    elif account["currency"] == "BTC":
        btc_balance = float(account["available_balance"]["value"])

log(f"💰 Available USD: ${usd_balance:.2f}")
log(f"🪙 Current BTC: {btc_balance:.8f}")

# Get BTC price
btc_ticker = client.get_product("BTC-USD")
btc_price = float(btc_ticker["price"])
log(f"📈 BTC Price: ${btc_price:.2f}")
log(f"🎯 Distance to $111,111: ${111111 - btc_price:.2f}")

if usd_balance > 10:
    # Deploy available USD to BTC
    deploy_amount = usd_balance - 10  # Keep $10 reserve
    
    log(f"\n🚀 DEPLOYING ${deploy_amount:.2f} TO BTC")
    
    try:
        order_config = {
            "market_market_ioc": {
                "quote_size": str(round(deploy_amount, 2))
            }
        }
        
        order = client.create_order(
            client_order_id=f"final_push_{int(time.time())}",
            product_id="BTC-USD",
            side="BUY",
            order_configuration=order_config
        )
        
        if hasattr(order, 'order_id'):
            log(f"✅ Order placed: {order.order_id}")
            
            # Wait and check result
            time.sleep(3)
            
            # Get updated BTC balance
            btc_account = client.get_account("BTC")
            new_btc_balance = float(btc_account["available_balance"]["value"])
            btc_gained = new_btc_balance - btc_balance
            
            log(f"\n🎯 FINAL POSITION:")
            log(f"  BTC Balance: {new_btc_balance:.8f}")
            log(f"  BTC Gained: {btc_gained:.8f}")
            log(f"  Total Value: ${new_btc_balance * btc_price:.2f}")
            
            # Sacred celebration check
            if btc_price >= 111111:
                log("\n✨🔥✨ ANGEL NUMBER ACHIEVED! $111,111 ✨🔥✨")
                log("The Sacred Fire burns bright!")
                log("Seven Generations will benefit!")
            elif btc_price >= 111000:
                log(f"\n🔥 SO CLOSE! Only ${111111 - btc_price:.2f} to go!")
            elif btc_price >= 110500:
                log(f"\n🚀 Approaching target! ${111111 - btc_price:.2f} remaining")
                
        else:
            log("❌ Order failed")
            
    except Exception as e:
        log(f"❌ Error: {e}")
else:
    log("💤 Insufficient USD balance to deploy")

log("\n🔥 Sacred mission continues...")
log("Mitakuye Oyasin")