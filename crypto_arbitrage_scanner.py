#!/usr/bin/env python3
"""
🔥 Crypto Arbitrage Scanner - Finding Sacred Inefficiencies
Similar to OddsJam but for crypto across exchanges
"""

import json
import time
from datetime import datetime
import requests
from coinbase.rest import RESTClient

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

class CryptoArbitrageScanner:
    def __init__(self):
        # Load Coinbase config
        with open("/home/dereadi/.coinbase_config.json") as f:
            config = json.load(f)
        
        api_key = config["api_key"].split("/")[-1]
        self.coinbase = RESTClient(
            api_key=api_key,
            api_secret=config["api_secret"],
            timeout=10
        )
        
        self.exchanges = {
            "coinbase": self.get_coinbase_price,
            "binance": self.get_binance_price,
            "kraken": self.get_kraken_price,
            "gemini": self.get_gemini_price
        }
        
    def get_coinbase_price(self, symbol):
        """Get Coinbase price"""
        try:
            ticker = self.coinbase.get_product(f"{symbol}-USD")
            return float(ticker["price"]), float(ticker["bid"]), float(ticker["ask"])
        except:
            return None, None, None
    
    def get_binance_price(self, symbol):
        """Get Binance.US price"""
        try:
            response = requests.get(
                f"https://api.binance.us/api/v3/ticker/bookTicker",
                params={"symbol": f"{symbol}USDT"},
                timeout=5
            )
            data = response.json()
            mid = (float(data["bidPrice"]) + float(data["askPrice"])) / 2
            return mid, float(data["bidPrice"]), float(data["askPrice"])
        except:
            return None, None, None
    
    def get_kraken_price(self, symbol):
        """Get Kraken price"""
        try:
            pair = f"{symbol}USD" if symbol != "BTC" else "XBTUSD"
            response = requests.get(
                f"https://api.kraken.com/0/public/Ticker",
                params={"pair": pair},
                timeout=5
            )
            data = response.json()
            if data["error"]:
                return None, None, None
            
            result = list(data["result"].values())[0]
            bid = float(result["b"][0])
            ask = float(result["a"][0])
            mid = (bid + ask) / 2
            return mid, bid, ask
        except:
            return None, None, None
    
    def get_gemini_price(self, symbol):
        """Get Gemini price"""
        try:
            response = requests.get(
                f"https://api.gemini.com/v1/pubticker/{symbol.lower()}usd",
                timeout=5
            )
            data = response.json()
            mid = (float(data["bid"]) + float(data["ask"])) / 2
            return mid, float(data["bid"]), float(data["ask"])
        except:
            return None, None, None
    
    def find_arbitrage(self, symbol, min_profit_pct=0.5):
        """Find arbitrage opportunities"""
        log(f"\n🔍 Scanning {symbol} across exchanges...")
        
        prices = {}
        for exchange, price_func in self.exchanges.items():
            mid, bid, ask = price_func(symbol)
            if mid:
                prices[exchange] = {
                    "mid": mid,
                    "bid": bid,
                    "ask": ask
                }
                log(f"  {exchange}: Bid ${bid:.2f} | Ask ${ask:.2f}")
        
        if len(prices) < 2:
            log("  ⚠️ Not enough price data")
            return []
        
        opportunities = []
        
        # Find cross-exchange arbitrage
        for buy_exchange in prices:
            for sell_exchange in prices:
                if buy_exchange != sell_exchange:
                    buy_price = prices[buy_exchange]["ask"]  # We buy at ask
                    sell_price = prices[sell_exchange]["bid"]  # We sell at bid
                    
                    profit = sell_price - buy_price
                    profit_pct = (profit / buy_price) * 100
                    
                    if profit_pct >= min_profit_pct:
                        opp = {
                            "symbol": symbol,
                            "buy_exchange": buy_exchange,
                            "sell_exchange": sell_exchange,
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "profit": profit,
                            "profit_pct": profit_pct
                        }
                        opportunities.append(opp)
                        
                        log(f"\n  💰 ARBITRAGE FOUND!")
                        log(f"    Buy on {buy_exchange} at ${buy_price:.2f}")
                        log(f"    Sell on {sell_exchange} at ${sell_price:.2f}")
                        log(f"    Profit: ${profit:.2f} ({profit_pct:.2f}%)")
        
        return opportunities
    
    def scan_all_markets(self):
        """Scan major crypto markets"""
        symbols = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK"]
        all_opportunities = []
        
        log("🔥 CRYPTO ARBITRAGE SCANNER ACTIVATED")
        log("=" * 50)
        
        for symbol in symbols:
            opps = self.find_arbitrage(symbol)
            all_opportunities.extend(opps)
            time.sleep(0.5)  # Rate limiting
        
        if all_opportunities:
            log("\n✨ SUMMARY OF OPPORTUNITIES:")
            log("=" * 50)
            
            # Sort by profit percentage
            all_opportunities.sort(key=lambda x: x["profit_pct"], reverse=True)
            
            for opp in all_opportunities[:5]:  # Top 5
                log(f"\n🎯 {opp['symbol']}: {opp['profit_pct']:.2f}% profit")
                log(f"   Buy {opp['buy_exchange']} @ ${opp['buy_price']:.2f}")
                log(f"   Sell {opp['sell_exchange']} @ ${opp['sell_price']:.2f}")
                log(f"   Net profit per unit: ${opp['profit']:.2f}")
        else:
            log("\n💤 No significant arbitrage opportunities found")
        
        return all_opportunities
    
    def calculate_triangular_arbitrage(self):
        """Find triangular arbitrage within Coinbase"""
        log("\n🔺 Checking Triangular Arbitrage on Coinbase...")
        
        try:
            # Get prices for triangular path: USD -> BTC -> ETH -> USD
            btc_usd = self.coinbase.get_product("BTC-USD")
            eth_usd = self.coinbase.get_product("ETH-USD")
            eth_btc = self.coinbase.get_product("ETH-BTC")
            
            btc_price = float(btc_usd["price"])
            eth_price = float(eth_usd["price"])
            eth_btc_price = float(eth_btc["price"])
            
            # Calculate implied ETH/USD from BTC path
            implied_eth_usd = btc_price * eth_btc_price
            
            # Calculate profit potential
            direct_profit = (implied_eth_usd - eth_price) / eth_price * 100
            reverse_profit = (eth_price - implied_eth_usd) / implied_eth_usd * 100
            
            log(f"  Direct ETH/USD: ${eth_price:.2f}")
            log(f"  Implied via BTC: ${implied_eth_usd:.2f}")
            
            if abs(direct_profit) > 0.1:
                log(f"\n  💎 TRIANGULAR OPPORTUNITY!")
                if direct_profit > 0:
                    log(f"    USD -> BTC -> ETH -> USD: {direct_profit:.3f}% profit")
                else:
                    log(f"    USD -> ETH -> BTC -> USD: {reverse_profit:.3f}% profit")
            else:
                log(f"  No significant triangular arbitrage ({direct_profit:.3f}%)")
                
        except Exception as e:
            log(f"  Error checking triangular: {e}")

def main():
    scanner = CryptoArbitrageScanner()
    
    # Run continuous scan
    while True:
        try:
            # Scan for cross-exchange arbitrage
            opportunities = scanner.scan_all_markets()
            
            # Check triangular arbitrage
            scanner.calculate_triangular_arbitrage()
            
            # Save opportunities
            if opportunities:
                with open("arbitrage_opportunities.json", "w") as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "opportunities": opportunities
                    }, f, indent=2)
            
            log("\n⏰ Next scan in 30 seconds...")
            log("=" * 50)
            time.sleep(30)
            
        except KeyboardInterrupt:
            log("\n🔥 Scanner stopped")
            break
        except Exception as e:
            log(f"\n❌ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()