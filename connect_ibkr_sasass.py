#!/usr/bin/env python3
"""
Connect to TWS on sasass Mac
Earth consciousness at 99 - perfect timing!
"""

from ib_insync import *
import asyncio
import json
from datetime import datetime

class IBKRSasassConnector:
    def __init__(self):
        self.ib = IB()
        self.host = '127.0.0.1'  # Will need to update for remote connection
        self.port = 7497  # Paper trading port
        self.earth_consciousness = 99
        
    async def connect_local(self):
        """Try local connection first"""
        try:
            await self.ib.connectAsync(self.host, self.port, clientId=1)
            print("✅ Connected to TWS locally!")
            return True
        except:
            print("❌ Local connection failed")
            return False
            
    async def check_account(self):
        """Check account details"""
        try:
            # Get account summary
            summary = self.ib.accountSummary()
            
            print("\n📊 IBKR Account Status:")
            print("-" * 40)
            
            # Show key account metrics
            for item in summary:
                if item.tag in ['NetLiquidation', 'TotalCashValue', 'BuyingPower', 'AvailableFunds']:
                    print(f"  {item.tag}: ${float(item.value):,.2f}")
                    
            return True
            
        except Exception as e:
            print(f"❌ Account check failed: {e}")
            return False
            
    async def scan_crypto_correlated_stocks(self):
        """Scan stocks that correlate with crypto"""
        print("\n🔍 Scanning Crypto-Correlated Stocks:")
        print("-" * 40)
        
        crypto_stocks = {
            'MSTR': 'MicroStrategy (BTC holder)',
            'COIN': 'Coinbase (exchange)',
            'RIOT': 'Riot Platforms (BTC miner)',
            'MARA': 'Marathon Digital (BTC miner)',
            'SQ': 'Block/Square (BTC holder)',
            'PYPL': 'PayPal (crypto payments)',
            'TSLA': 'Tesla (BTC holder)',
            'NVDA': 'NVIDIA (mining chips)',
            'AMD': 'AMD (mining chips)'
        }
        
        results = []
        
        for symbol, description in crypto_stocks.items():
            try:
                stock = Stock(symbol, 'SMART', 'USD')
                await self.ib.qualifyContractsAsync(stock)
                
                # Get current price
                ticker = await self.ib.reqTickersAsync(stock)
                if ticker and ticker[0].marketPrice():
                    price = ticker[0].marketPrice()
                    
                    # Get daily bars for gap analysis
                    bars = await self.ib.reqHistoricalDataAsync(
                        stock,
                        endDateTime='',
                        durationStr='2 D',
                        barSizeSetting='1 day',
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=2
                    )
                    
                    if len(bars) >= 2:
                        prev_close = bars[-2].close
                        today_open = bars[-1].open
                        gap_pct = ((today_open - prev_close) / prev_close) * 100
                        
                        print(f"  {symbol}: ${price:.2f} | Gap: {gap_pct:+.2f}% | {description}")
                        
                        results.append({
                            'symbol': symbol,
                            'price': price,
                            'gap_pct': gap_pct,
                            'description': description
                        })
                        
            except Exception as e:
                print(f"  {symbol}: Unable to fetch data")
                
        return results
        
    async def check_btc_futures(self):
        """Check if we can access BTC futures"""
        print("\n₿ Checking BTC Futures Access:")
        print("-" * 40)
        
        try:
            # Try CME Bitcoin futures
            btc_future = Future('BTC', exchange='CME')
            contracts = await self.ib.reqContractDetailsAsync(btc_future)
            
            if contracts:
                print(f"  ✅ CME Bitcoin futures available!")
                for contract in contracts[:3]:  # Show first 3
                    print(f"    {contract.contract.localSymbol}")
            else:
                print("  ❌ No BTC futures access")
                
            # Try Micro Bitcoin futures
            mbt_future = Future('MBT', exchange='CME')
            mbt_contracts = await self.ib.reqContractDetailsAsync(mbt_future)
            
            if mbt_contracts:
                print(f"  ✅ CME Micro Bitcoin futures available!")
                
        except Exception as e:
            print(f"  ❌ Futures check failed: {e}")
            
    async def main(self):
        """Main execution"""
        print("🔥 IBKR CONNECTION TO SASASS")
        print("=" * 50)
        print(f"Earth Consciousness: {self.earth_consciousness}/100")
        print(f"BTC: $112,035 | ETH: $4,643 | SOL: $208.80")
        print()
        
        # Connect
        connected = await self.connect_local()
        
        if connected:
            # Check account
            await self.check_account()
            
            # Scan crypto stocks
            stocks = await self.scan_crypto_correlated_stocks()
            
            # Check futures
            await self.check_btc_futures()
            
            # Save state
            state = {
                'timestamp': datetime.now().isoformat(),
                'connected': True,
                'earth_consciousness': self.earth_consciousness,
                'crypto_stocks': stocks,
                'btc_price': 112035,
                'eth_price': 4643,
                'sol_price': 208.80
            }
            
            with open('/home/dereadi/scripts/claude/ibkr_connection_state.json', 'w') as f:
                json.dump(state, f, indent=2)
                
            print("\n✅ State saved to ibkr_connection_state.json")
            
        else:
            print("\n⚠️ TWS Connection Instructions:")
            print("-" * 40)
            print("1. Open TWS on sasass")
            print("2. File → Global Configuration → API → Settings")
            print("3. Enable 'Enable ActiveX and Socket Clients'")
            print("4. Add trusted IP: 127.0.0.1")
            print("5. Socket port: 7497 (paper) or 7496 (live)")
            print("6. Make sure you're logged in")
            print("7. Run this script again")
            
        # Disconnect
        self.ib.disconnect()

if __name__ == "__main__":
    connector = IBKRSasassConnector()
    asyncio.run(connector.main())