#!/usr/bin/env python3
"""
🦀💰 COINBASE LIVE TRADING CRAWDAD
==================================
Real money trading with your $300
"""

import json
import os
import time
import hmac
import hashlib
import base64
from datetime import datetime
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class CoinbaseLiveCrawdad:
    def __init__(self):
        # Load config
        config_path = os.path.expanduser("~/.coinbase_config.json")
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.api_key = self.config["api_key"]
        self.api_secret = self.config["api_secret"]
        self.capital = self.config.get("capital", 300.0)
        
        # Parse private key
        self.private_key = serialization.load_pem_private_key(
            self.api_secret.encode(),
            password=None,
            backend=default_backend()
        )
        
        self.base_url = "https://api.coinbase.com"
        self.accounts = {}
        self.prices = {}
        
    def sign_request(self, method, path, body=""):
        """Sign request with EC private key"""
        timestamp = str(int(time.time()))
        message = f"{timestamp}{method}{path}{body}"
        
        signature = self.private_key.sign(
            message.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        
        return {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": base64.b64encode(signature).decode(),
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
    
    def api_request(self, method, endpoint, data=None):
        """Make authenticated API request"""
        path = f"/api/v3/brokerage{endpoint}"
        url = f"{self.base_url}{path}"
        
        body = json.dumps(data) if data else ""
        headers = self.sign_request(method, path, body)
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=body)
        
        if response.status_code != 200:
            print(f"⚠️ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        return response.json()
    
    def get_accounts(self):
        """Get all accounts"""
        result = self.api_request("GET", "/accounts")
        if result and "accounts" in result:
            for account in result["accounts"]:
                currency = account["currency"]
                balance = float(account["available_balance"]["value"])
                if balance > 0:
                    self.accounts[currency] = {
                        "id": account["uuid"],
                        "balance": balance
                    }
                    print(f"  💰 {currency}: ${balance:.2f}")
        return self.accounts
    
    def get_price(self, symbol):
        """Get current price for symbol"""
        result = self.api_request("GET", f"/products/{symbol}-USD/ticker")
        if result:
            price = float(result["price"])
            self.prices[symbol] = price
            return price
        return None
    
    def place_order(self, symbol, side, amount_usd):
        """Place market order"""
        product_id = f"{symbol}-USD"
        
        # Get current price
        price = self.get_price(symbol)
        if not price:
            print(f"❌ Could not get price for {symbol}")
            return None
        
        # Calculate quantity
        quantity = amount_usd / price
        
        order_data = {
            "client_order_id": f"crawdad_{int(time.time())}",
            "product_id": product_id,
            "side": side.upper(),
            "order_configuration": {
                "market_market_ioc": {
                    "quote_size": str(amount_usd) if side == "BUY" else None,
                    "base_size": str(quantity) if side == "SELL" else None
                }
            }
        }
        
        # Remove None values
        if side == "BUY":
            del order_data["order_configuration"]["market_market_ioc"]["base_size"]
        else:
            del order_data["order_configuration"]["market_market_ioc"]["quote_size"]
        
        result = self.api_request("POST", "/orders", order_data)
        
        if result and "order_id" in result:
            print(f"  ✅ Order placed: {side} {quantity:.6f} {symbol} @ ${price:.2f}")
            return result
        
        return None
    
    def run_trading_cycle(self):
        """Execute one trading cycle"""
        print(f"\n🦀 TRADING CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 50)
        
        # Check accounts
        print("\n📊 Account Balances:")
        self.get_accounts()
        
        # Check prices
        print("\n💹 Current Prices:")
        for symbol in ["BTC", "ETH", "SOL"]:
            price = self.get_price(symbol)
            if price:
                print(f"  {symbol}: ${price:,.2f}")
        
        # Trading logic (conservative)
        consciousness = 75  # Using stable consciousness
        
        if consciousness >= 65:
            # Small test trade
            trade_size = 10.0  # Start with $10 trades
            
            # Example: Buy SOL if we have USD
            if "USD" in self.accounts and self.accounts["USD"]["balance"] >= trade_size:
                print(f"\n🎯 Placing order...")
                self.place_order("SOL", "BUY", trade_size)
        
        print("\n" + "="*50)
    
    def run(self):
        """Main trading loop"""
        print("\n🦀💰 COINBASE LIVE TRADING ACTIVATED")
        print("="*60)
        print(f"💵 Capital: ${self.capital:.2f}")
        print(f"🔑 API Key: {self.api_key[:30]}...")
        print("="*60)
        
        try:
            cycle = 0
            while True:
                cycle += 1
                print(f"\n📍 CYCLE {cycle}")
                
                self.run_trading_cycle()
                
                # Save state
                state = {
                    "timestamp": datetime.now().isoformat(),
                    "cycle": cycle,
                    "accounts": self.accounts,
                    "prices": self.prices
                }
                
                with open("coinbase_live_state.json", "w") as f:
                    json.dump(state, f, indent=2)
                
                # Wait before next cycle
                print("\n💤 Waiting 60 seconds...")
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n\n🛑 TRADING STOPPED")
            print(f"Total cycles: {cycle}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    trader = CoinbaseLiveCrawdad()
    trader.run()