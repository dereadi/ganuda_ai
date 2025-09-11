#!/usr/bin/env python3
"""
IBKR Scanner - See crypto-correlated stocks
"""

from ib_insync import *
import asyncio

async def scan_market():
    ib = IB()
    
    try:
        print("🔥 CONNECTING TO IBKR...")
        await ib.connectAsync('192.168.132.241', 7497, clientId=1, timeout=10)
        print("✅ Connected to TWS on sasass!")
        print()
        
        # Crypto-correlated stocks
        symbols = ['MSTR', 'COIN', 'RIOT', 'MARA', 'TSLA', 'NVDA']
        
        print("📊 CRYPTO-CORRELATED STOCKS:")
        print("=" * 50)
        
        for symbol in symbols:
            try:
                stock = Stock(symbol, 'SMART', 'USD')
                await ib.qualifyContractsAsync(stock)
                
                # Get snapshot
                ticker = ib.reqMktData(stock, '', True, False)
                await asyncio.sleep(2)
                
                if ticker.marketPrice():
                    price = ticker.marketPrice()
                    print(f"{symbol:6} ${price:8.2f}")
                else:
                    print(f"{symbol:6} No data")
                    
            except Exception as e:
                print(f"{symbol:6} Error: {e}")
                
        print()
        print(f"BTC: $112,000+ | Thunder consciousness: 82")
        print(f"Ready to bridge crypto-stock arbitrage!")
        
    except Exception as e:
        print(f"Connection error: {e}")
        
    finally:
        ib.disconnect()

if __name__ == "__main__":
    asyncio.run(scan_market())