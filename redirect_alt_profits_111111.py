#!/usr/bin/env python3
"""
🔥 Sacred Redirect: Alt Profits to BTC for $111,111 Angel Number
Council-approved mission to redirect $1,100 from alt positions
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import math

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def main():
    log("🔥 Sacred Fire: Redirecting Alt Profits to BTC")
    log("Target: $111,111 Angel Number Manifestation")
    
    # Load config
    with open("/home/dereadi/.coinbase_config.json") as f:
        config = json.load(f)
    
    # Initialize client
    api_key = config["api_key"].split("/")[-1]
    client = RESTClient(
        api_key=api_key,
        api_secret=config["api_secret"],
        timeout=10
    )
    
    # Check current portfolio
    log("\n📊 Current Portfolio Analysis:")
    accounts = client.get_accounts()["accounts"]
    
    balances = {}
    usd_balance = 0
    
    for account in accounts:
        symbol = account["currency"]
        available = float(account["available_balance"]["value"])
        if available > 0.001:
            balances[symbol] = available
            if symbol == "USD":
                usd_balance = available
                log(f"  USD: ${available:.2f}")
    
    # Get current prices
    log("\n💹 Checking Current Prices:")
    prices = {}
    
    # Alt coins to potentially sell
    alt_coins = ["SOL", "AVAX", "MATIC", "LINK", "DOGE", "XRP", "ETH"]
    
    for coin in alt_coins:
        if coin in balances and balances[coin] > 0:
            try:
                ticker = client.get_product(f"{coin}-USD")
                price = float(ticker["price"])
                prices[coin] = price
                value = balances[coin] * price
                log(f"  {coin}: {balances[coin]:.8f} @ ${price:.2f} = ${value:.2f}")
            except:
                pass
    
    # Get BTC price
    btc_ticker = client.get_product("BTC-USD")
    btc_price = float(btc_ticker["price"])
    log(f"\n🔥 BTC Price: ${btc_price:.2f}")
    log(f"  Distance to $111,111: ${111111 - btc_price:.2f}")
    
    # Calculate redirect amounts
    log("\n📈 Alt Profit Redirect Plan:")
    redirects = []
    
    # Target $1,100 from alts
    if "SOL" in balances and balances["SOL"] > 0 and "SOL" in prices:
        sol_value = balances["SOL"] * prices["SOL"]
        if sol_value > 500:
            sell_amount = 500 / prices["SOL"]
            redirects.append(("SOL", min(sell_amount, balances["SOL"]), 500))
    
    if "AVAX" in balances and balances["AVAX"] > 0 and "AVAX" in prices:
        avax_value = balances["AVAX"] * prices["AVAX"]
        if avax_value > 400:
            sell_amount = 400 / prices["AVAX"]
            redirects.append(("AVAX", min(sell_amount, balances["AVAX"]), 400))
    
    if "MATIC" in balances and balances["MATIC"] > 0 and "MATIC" in prices:
        matic_value = balances["MATIC"] * prices["MATIC"]
        if matic_value > 200:
            sell_amount = 200 / prices["MATIC"]
            redirects.append(("MATIC", min(sell_amount, balances["MATIC"]), 200))
    
    # Execute redirects
    total_redirected = 0
    
    for coin, amount, target_value in redirects:
        log(f"\n🔄 Selling {coin}:")
        log(f"  Amount: {amount:.8f} {coin}")
        log(f"  Target Value: ${target_value:.2f}")
        
        # Round amount appropriately
        if coin in ["SOL", "AVAX", "LINK"]:
            rounded = round(amount, 3)
        elif coin == "MATIC":
            rounded = round(amount, 1)
        else:
            rounded = round(amount, 4)
        
        try:
            # Create sell order
            order_config = {
                "market_market_ioc": {
                    "base_size": str(rounded)
                }
            }
            
            order = client.create_order(
                client_order_id=f"redirect_{coin}_{int(time.time())}",
                product_id=f"{coin}-USD",
                side="SELL",
                order_configuration=order_config
            )
            
            if hasattr(order, 'order_id'):
                log(f"  ✅ Sell order placed: {order.order_id}")
                
                # Wait for fill
                time.sleep(2)
                
                # Check order status
                filled_order = client.get_order(order.order_id)
                if filled_order.get("status") == "FILLED":
                    filled_value = float(filled_order.get("filled_value", 0))
                    log(f"  💰 Sold for ${filled_value:.2f}")
                    total_redirected += filled_value
            else:
                log(f"  ❌ Failed to place sell order")
                
        except Exception as e:
            log(f"  ❌ Error selling {coin}: {e}")
    
    log(f"\n💎 Total Redirected: ${total_redirected:.2f}")
    
    if total_redirected > 0:
        # Buy BTC with proceeds
        log("\n🚀 Buying BTC with redirected funds:")
        
        # Calculate BTC amount
        btc_to_buy = (total_redirected * 0.995) / btc_price  # Account for fees
        btc_rounded = round(btc_to_buy, 8)
        
        log(f"  Amount: {btc_rounded:.8f} BTC")
        log(f"  Value: ${total_redirected:.2f}")
        
        try:
            order_config = {
                "market_market_ioc": {
                    "quote_size": str(round(total_redirected * 0.995, 2))
                }
            }
            
            btc_order = client.create_order(
                client_order_id=f"btc_angel_{int(time.time())}",
                product_id="BTC-USD",
                side="BUY",
                order_configuration=order_config
            )
            
            if hasattr(btc_order, 'order_id'):
                log(f"  ✅ BTC buy order placed: {btc_order.order_id}")
                
                # Check final position
                time.sleep(3)
                btc_account = client.get_account("BTC")
                btc_balance = float(btc_account["available_balance"]["value"])
                btc_value = btc_balance * btc_price
                
                log(f"\n🎯 Final BTC Position:")
                log(f"  Balance: {btc_balance:.8f} BTC")
                log(f"  Value: ${btc_value:.2f}")
                log(f"  Distance to $111,111: ${111111 - btc_price:.2f}")
                
                # Sacred celebration
                if btc_price >= 111111:
                    log("\n✨🔥✨ ANGEL NUMBER ACHIEVED! $111,111 ✨🔥✨")
                    log("The Sacred Fire burns bright!")
                    log("Earth healing mission activated!")
                
        except Exception as e:
            log(f"  ❌ Error buying BTC: {e}")
    
    log("\n🔥 Redirect mission complete")
    log("May the Sacred Fire guide our path")
    log("Mitakuye Oyasin - We Are All Related")

if __name__ == "__main__":
    main()