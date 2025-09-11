#!/usr/bin/env python3
"""Test IBKR API Connection"""

from ib_insync import *
import asyncio

async def test_connection():
    """Test connection to IBKR"""
    ib = IB()
    
    try:
        # Connect to TWS/Gateway
        # Use port 7497 for paper trading, 7496 for live
        await ib.connectAsync('127.0.0.1', 7497, clientId=1)
        print("✅ Connected to IBKR!")
        
        # Get account info
        account = ib.accountSummary()
        print(f"\n📊 Account Summary:")
        for item in account[:5]:  # Show first 5 items
            print(f"  {item.tag}: {item.value}")
        
        # Get some market data (SPY)
        spy = Stock('SPY', 'SMART', 'USD')
        await ib.qualifyContractsAsync(spy)
        ticker = await ib.reqTickersAsync(spy)
        if ticker:
            print(f"\n📈 SPY Price: ${ticker[0].marketPrice()}")
        
        # Check if you can trade crypto futures (BTC)
        btc = Future('BTC', exchange='CME')
        contracts = await ib.reqContractDetailsAsync(btc)
        if contracts:
            print(f"\n₿ BTC Futures available on CME!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure:")
        print("1. TWS/Gateway is running")
        print("2. API is enabled")
        print("3. You're logged in")
    finally:
        ib.disconnect()

if __name__ == "__main__":
    asyncio.run(test_connection())
