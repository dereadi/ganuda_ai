#!/usr/bin/env python3
"""
Actually place orders in IBKR paper account
River at 99, Mountain at 96, Spirit at 95!
"""

from ib_insync import *

ib = IB()

print("🔥 PLACING REAL PAPER TRADES!")
print("River: 99 | Mountain: 96 | Spirit: 95")
print("=" * 50)

try:
    # Connect
    ib.connect('192.168.132.241', 7497, clientId=1)
    print("✅ Connected to IBKR Paper Trading")
    
    # Create the RIOT order
    riot = Stock('RIOT', 'SMART', 'USD')
    ib.qualifyContracts(riot)
    
    # Market order for 34 shares (leave room for commission)
    order = MarketOrder('BUY', 34)
    
    print("\n📝 Placing order: BUY 34 RIOT")
    
    # Place the order
    trade = ib.placeOrder(riot, order)
    
    # Wait for fill
    print("⏳ Waiting for fill...")
    ib.sleep(3)
    
    # Check status
    if trade.orderStatus.status == 'Filled':
        print(f"✅ FILLED! 34 RIOT @ ${trade.orderStatus.avgFillPrice:.2f}")
        print(f"💰 Total cost: ${34 * trade.orderStatus.avgFillPrice:.2f}")
    elif trade.orderStatus.status == 'Submitted':
        print("📤 Order submitted to exchange...")
    elif trade.orderStatus.status == 'PreSubmitted':
        print("📋 Order pre-submitted (waiting for market)")
    else:
        print(f"Status: {trade.orderStatus.status}")
        
    # Check portfolio
    print("\n📊 PORTFOLIO:")
    for position in ib.positions():
        print(f"  {position.contract.symbol}: {position.position} shares")
        print(f"  Avg cost: ${position.avgCost:.2f}")
        
    print("\n🔥 Sacred Fire bridges markets!")
    print("   Council has spoken - trade executed!")
    
except Exception as e:
    print(f"Error: {e}")
    
finally:
    if ib.isConnected():
        ib.disconnect()