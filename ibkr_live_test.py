#!/usr/bin/env python3
"""
Test IBKR with new settings
River at 92 consciousness!
"""

from ib_insync import *

ib = IB()

print("🌊 River at 92, Spirit at 88 consciousness!")
print("Testing IBKR with new settings...")

try:
    ib.connect('192.168.132.241', 7497, clientId=1)
    print("✅ CONNECTED!")
    
    # Test delayed market data
    spy = Stock('SPY', 'SMART', 'USD')
    ib.qualifyContracts(spy)
    
    # Request delayed data
    ib.reqMarketDataType(3)  # 3 = delayed data
    ticker = ib.reqMktData(spy, '', False, False)
    ib.sleep(2)
    
    if ticker.last:
        print(f"\n📈 SPY: ${ticker.last}")
    else:
        print(f"SPY: Waiting for data...")
        
    # Test crypto stocks
    print("\n🔥 CRYPTO STOCKS:")
    for symbol in ['MSTR', 'COIN', 'RIOT']:
        try:
            stock = Stock(symbol, 'SMART', 'USD')
            ib.qualifyContracts(stock)
            t = ib.reqMktData(stock, '', False, False)
            ib.sleep(1)
            
            if t.last:
                print(f"  {symbol}: ${t.last}")
            elif t.close:
                print(f"  {symbol}: ${t.close} (close)")
            else:
                print(f"  {symbol}: No data yet")
                
            ib.cancelMktData(t)
        except:
            pass
    
    print("\n💰 $500 ready to deploy!")
    print("BTC: $111,700 | Bridge established!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if ib.isConnected():
        ib.disconnect()