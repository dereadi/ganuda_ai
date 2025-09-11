#!/usr/bin/env python3
"""
🚨 EXECUTE EMERGENCY LIQUIDITY RESTORATION
Selling 10% of top positions to restore $500 buffer
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

print("🚨 EXECUTING EMERGENCY LIQUIDITY RESTORATION")
print("=" * 60)
print(f"Start Time: {datetime.now().strftime('%H:%M:%S')}")
print()

try:
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=10)
    
    print("📊 EXECUTING BALANCED LIQUIDITY PLAN:")
    print("-" * 40)
    
    orders_executed = []
    total_raised = 0
    
    # 1. Sell 1.215 SOL (10% of position)
    print("1. Selling SOL...")
    try:
        sol_order = client.market_order_sell(
            client_order_id=f"liquidity_sol_{int(time.time()*1000)}",
            product_id="SOL-USD",
            base_size="1.215"
        )
        print(f"   ✅ Sold 1.215 SOL")
        orders_executed.append(("SOL", 1.215, sol_order))
        total_raised += 250  # Estimate
        time.sleep(1)  # Avoid rate limits
    except Exception as e:
        print(f"   ❌ SOL sell failed: {str(e)[:50]}")
    
    # 2. Sell 0.055 ETH (10% of position)
    print("2. Selling ETH...")
    try:
        eth_order = client.market_order_sell(
            client_order_id=f"liquidity_eth_{int(time.time()*1000)}",
            product_id="ETH-USD",
            base_size="0.055"
        )
        print(f"   ✅ Sold 0.055 ETH")
        orders_executed.append(("ETH", 0.055, eth_order))
        total_raised += 178  # Estimate
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ ETH sell failed: {str(e)[:50]}")
    
    # 3. Sell 22 XRP (10% of position)
    print("3. Selling XRP...")
    try:
        xrp_order = client.market_order_sell(
            client_order_id=f"liquidity_xrp_{int(time.time()*1000)}",
            product_id="XRP-USD",
            base_size="22"
        )
        print(f"   ✅ Sold 22 XRP")
        orders_executed.append(("XRP", 22, xrp_order))
        total_raised += 50  # Estimate
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ XRP sell failed: {str(e)[:50]}")
    
    print()
    print("📋 EXECUTION SUMMARY:")
    print("-" * 40)
    
    if orders_executed:
        print(f"Orders executed: {len(orders_executed)}")
        for coin, amount, order in orders_executed:
            print(f"   • {coin}: {amount} units")
        print(f"Estimated raised: ~${total_raised}")
    else:
        print("⚠️ NO ORDERS EXECUTED - Manual intervention needed!")
    
    # Check new balance
    print()
    print("💰 CHECKING NEW BALANCE:")
    print("-" * 40)
    
    time.sleep(2)  # Wait for orders to settle
    
    accounts = client.get_accounts()["accounts"]
    new_cash = 0
    
    for account in accounts:
        if account["currency"] == "USD":
            new_cash = float(account["available_balance"]["value"])
            break
    
    print(f"Previous cash: $17.96")
    print(f"Current cash:  ${new_cash:.2f}")
    print(f"Change:        ${new_cash - 17.96:.2f}")
    
    print()
    
    if new_cash > 400:
        print("✅ SUCCESS - Liquidity restored!")
        print(f"   New liquidity: ${new_cash:.2f}")
    elif new_cash > 200:
        print("🟡 PARTIAL SUCCESS - Liquidity improved")
        print(f"   Current: ${new_cash:.2f}")
        print(f"   Still need: ${500 - new_cash:.2f}")
    else:
        print("⚠️ ORDERS MAY BE PENDING")
        print("   Check again in a few minutes")
    
    # Save execution log
    execution_log = {
        "timestamp": datetime.now().isoformat(),
        "orders": len(orders_executed),
        "estimated_raised": total_raised,
        "new_balance": new_cash,
        "status": "completed" if new_cash > 400 else "partial"
    }
    
    with open("liquidity_restoration_log.json", "w") as f:
        json.dump(execution_log, f, indent=2)
    
    print()
    print("=" * 60)
    print("📝 Log saved to liquidity_restoration_log.json")
    print(f"End Time: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ CRITICAL ERROR: {str(e)}")
    print()
    print("MANUAL ACTION REQUIRED:")
    print("1. Log into Coinbase")
    print("2. Sell 1.2 SOL")
    print("3. Sell 0.055 ETH")
    print("4. Sell 22 XRP")
    print("5. Verify $500 cash balance")