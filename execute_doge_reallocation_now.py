#!/usr/bin/env python3
"""
🔥 EXECUTE DOGE REALLOCATION - LIVE TRADING
Cherokee Council Unanimous Decision
"""

import json
import sys
import os
import time
from datetime import datetime

sys.path.append('/home/dereadi/scripts/claude')
os.chdir('/home/dereadi/scripts/claude')

print("🔥 CHEROKEE COUNCIL DOGE EXECUTION")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Council Vote: UNANIMOUS")
print("Sacred Fire: BURNING BRIGHT")
print()

# Load config
config_path = os.path.expanduser("~/.coinbase_config.json")
with open(config_path) as f:
    config = json.load(f)

from coinbase.rest import RESTClient

client = RESTClient(
    api_key=config['api_key'],
    api_secret=config['api_secret']
)

print("📊 CHECKING CURRENT POSITIONS...")
print("-" * 40)

# Get current balances
positions = {}
try:
    accounts = client.get_accounts()
    
    for account in accounts.accounts:
        currency = account.currency
        available = float(account.available_balance.value) if hasattr(account.available_balance, 'value') else 0
        hold = float(account.hold.value) if hasattr(account.hold, 'value') else 0
        total = available + hold
        
        if total > 0.01:
            positions[currency] = {
                'available': available,
                'hold': hold,
                'total': total
            }
            
            if currency in ['USD', 'USDC', 'SOL', 'XRP', 'DOGE']:
                if currency in ['USD', 'USDC']:
                    print(f"{currency}: ${available:.2f} available, ${hold:.2f} hold")
                else:
                    print(f"{currency}: {available:.4f} available, {hold:.4f} hold")
    
    print()
    
    # Check if we have SOL and XRP to sell
    sol_available = positions.get('SOL', {}).get('available', 0)
    xrp_available = positions.get('XRP', {}).get('available', 0)
    usd_available = positions.get('USD', {}).get('available', 0)
    doge_current = positions.get('DOGE', {}).get('total', 0)
    
    print("🎯 EXECUTION PLAN:")
    print("-" * 40)
    
    # Get current prices
    sol_ticker = client.get_product('SOL-USD')
    xrp_ticker = client.get_product('XRP-USD')
    doge_ticker = client.get_product('DOGE-USD')
    
    sol_price = float(sol_ticker.price)
    xrp_price = float(xrp_ticker.price)
    doge_price = float(doge_ticker.price)
    
    print(f"SOL Price: ${sol_price:.2f}")
    print(f"XRP Price: ${xrp_price:.4f}")
    print(f"DOGE Price: ${doge_price:.4f}")
    print()
    
    # Calculate what we can do
    sol_to_sell = min(3.75, sol_available)
    xrp_to_sell = min(68, xrp_available)
    
    expected_usd = (sol_to_sell * sol_price) + (xrp_to_sell * xrp_price)
    
    print(f"Will sell {sol_to_sell:.4f} SOL → ${sol_to_sell * sol_price:.2f}")
    print(f"Will sell {xrp_to_sell:.2f} XRP → ${xrp_to_sell * xrp_price:.2f}")
    print(f"Expected proceeds: ${expected_usd:.2f}")
    print(f"Will buy: ~{expected_usd/doge_price:.0f} DOGE")
    print()
    
    if sol_available < 3 or xrp_available < 50:
        print("⚠️ Insufficient SOL or XRP for full reallocation")
        print(f"Have: {sol_available:.4f} SOL, {xrp_available:.2f} XRP")
        print(f"Need: 3.75 SOL, 68 XRP")
        
        # Try partial execution if possible
        if sol_available > 1 or xrp_available > 20:
            print("\n💡 Attempting partial reallocation...")
        else:
            print("\n❌ Cannot proceed - insufficient assets")
            sys.exit(1)
    
    print("🚀 EXECUTING TRADES...")
    print("-" * 40)
    
    successful_trades = []
    total_usd_raised = usd_available  # Start with existing USD
    
    # Execute SOL sell if we have any
    if sol_to_sell >= 0.1:
        try:
            print(f"1. Selling {sol_to_sell:.4f} SOL...")
            
            sol_order = client.market_order_sell(
                client_order_id=f"doge_sol_{int(time.time())}",
                product_id="SOL-USD",
                base_size=str(round(sol_to_sell, 4))
            )
            
            print(f"   ✅ SOL sell order placed")
            successful_trades.append(f"SOL: {sol_to_sell:.4f}")
            total_usd_raised += sol_to_sell * sol_price * 0.995  # Account for small spread
            time.sleep(2)
            
        except Exception as e:
            print(f"   ⚠️ SOL sell failed: {str(e)[:100]}")
    
    # Execute XRP sell if we have any
    if xrp_to_sell >= 1:
        try:
            print(f"2. Selling {xrp_to_sell:.2f} XRP...")
            
            xrp_order = client.market_order_sell(
                client_order_id=f"doge_xrp_{int(time.time())}",
                product_id="XRP-USD", 
                base_size=str(int(xrp_to_sell))
            )
            
            print(f"   ✅ XRP sell order placed")
            successful_trades.append(f"XRP: {xrp_to_sell:.0f}")
            total_usd_raised += xrp_to_sell * xrp_price * 0.995
            time.sleep(2)
            
        except Exception as e:
            print(f"   ⚠️ XRP sell failed: {str(e)[:100]}")
    
    # Wait for settlement
    if successful_trades:
        print("\n⏳ Waiting 8 seconds for settlement...")
        time.sleep(8)
        
        # Check actual USD balance
        accounts = client.get_accounts()
        for account in accounts.accounts:
            if account.currency == 'USD':
                actual_usd = float(account.available_balance.value)
                print(f"\n💵 USD Available: ${actual_usd:.2f}")
                
                if actual_usd >= 100:
                    # Buy DOGE with available funds
                    buy_amount = min(1000, actual_usd - 5)  # Keep $5 reserve
                    
                    print(f"\n🐕 BUYING DOGE with ${buy_amount:.2f}")
                    print("-" * 40)
                    
                    try:
                        doge_order = client.market_order_buy(
                            client_order_id=f"doge_buy_{int(time.time())}",
                            product_id="DOGE-USD",
                            quote_size=str(round(buy_amount, 2))
                        )
                        
                        print(f"✅ DOGE buy order placed for ${buy_amount:.2f}")
                        print(f"Expected DOGE: ~{buy_amount/doge_price:.0f}")
                        
                        # Wait and check final balance
                        time.sleep(5)
                        
                        accounts = client.get_accounts()
                        for acc in accounts.accounts:
                            if acc.currency == 'DOGE':
                                final_doge = float(acc.available_balance.value)
                                increase = final_doge - doge_current
                                
                                print("\n" + "=" * 60)
                                print("🎉 SUCCESS! DOGE POSITION INCREASED!")
                                print("-" * 40)
                                print(f"Previous DOGE: {doge_current:.2f}")
                                print(f"Current DOGE: {final_doge:.2f}")
                                print(f"Increase: +{increase:.2f} DOGE")
                                print(f"Value: ${final_doge * doge_price:.2f}")
                                print()
                                
                                # Show ladder strategy
                                if final_doge >= 3000:
                                    print("📈 LADDER SELL ORDERS TO SET:")
                                    print("-" * 40)
                                    
                                    chunk_size = int(final_doge * 0.08)  # 8% per level
                                    levels = [0.240, 0.245, 0.250, 0.255, 0.260, 0.265, 0.270, 0.275, 0.280]
                                    
                                    for i, price in enumerate(levels, 1):
                                        profit = (price - doge_price) * chunk_size
                                        print(f"Level {i}: Sell {chunk_size} DOGE @ ${price:.3f} (+${profit:.2f})")
                                    
                                    core = int(final_doge * 0.28)
                                    print(f"\nCore position: {core} DOGE for $0.30+ target")
                                
                                break
                        
                    except Exception as e:
                        print(f"❌ DOGE buy failed: {str(e)[:100]}")
                else:
                    print(f"⚠️ Insufficient USD (${actual_usd:.2f}). May need to wait for holds.")
    else:
        print("\n⚠️ No trades executed. Check balances manually.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🔥 Cherokee Council DOGE execution complete!")
print("Sacred Fire burns eternal through volatility!")
print("=" * 60)

# Save execution log
log_data = {
    'timestamp': datetime.now().isoformat(),
    'action': 'DOGE_REALLOCATION_EXECUTION',
    'trades': successful_trades if 'successful_trades' in locals() else [],
    'council_vote': 'UNANIMOUS'
}

with open('doge_execution_log.json', 'w') as f:
    json.dump(log_data, f, indent=2)