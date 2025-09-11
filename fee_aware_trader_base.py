#!/usr/bin/env python3
"""
💰 FEE-AWARE TRADER BASE CLASS
All trading bots should inherit from this to handle fees properly
"""

import json
from coinbase.rest import RESTClient

class FeeAwareTrader:
    """Base class for all trading bots with built-in fee awareness"""
    
    def __init__(self):
        self.config = json.load(open("/home/dereadi/.coinbase_config.json"))
        self.key = self.config["api_key"].split("/")[-1]
        self.client = RESTClient(api_key=self.key, api_secret=self.config["api_secret"], timeout=10)
        
        # Coinbase fee structure (as of 2025)
        self.TAKER_FEE = 0.006  # 0.6% for market orders
        self.MAKER_FEE = 0.004  # 0.4% for limit orders
        self.SPREAD_FEE = 0.005  # 0.5% spread on market orders
        
        # Total expected cost for market orders
        self.TOTAL_MARKET_FEE = self.TAKER_FEE + self.SPREAD_FEE  # 1.1% total
        
    def calculate_fees(self, amount, order_type="market"):
        """Calculate expected fees for a trade"""
        if order_type == "market":
            fee = amount * self.TOTAL_MARKET_FEE
        else:  # limit order
            fee = amount * self.MAKER_FEE
        
        return {
            "fee_amount": fee,
            "fee_percent": (fee / amount) * 100,
            "total_cost": amount + fee,
            "net_proceeds": amount - fee  # For sells
        }
    
    def calculate_buy_with_fees(self, usd_available, coin_price):
        """Calculate how much coin you can buy with fees included"""
        # Account for fees: actual_spend = base_amount * (1 + fee_rate)
        base_amount = usd_available / (1 + self.TOTAL_MARKET_FEE)
        fees = base_amount * self.TOTAL_MARKET_FEE
        coins_received = base_amount / coin_price
        
        return {
            "usd_spent": base_amount,
            "fees_paid": fees,
            "total_cost": usd_available,
            "coins_received": coins_received,
            "effective_price": usd_available / coins_received
        }
    
    def calculate_sell_with_fees(self, coins_to_sell, coin_price):
        """Calculate proceeds from selling with fees deducted"""
        gross_proceeds = coins_to_sell * coin_price
        fees = gross_proceeds * self.TOTAL_MARKET_FEE
        net_proceeds = gross_proceeds - fees
        
        return {
            "coins_sold": coins_to_sell,
            "gross_proceeds": gross_proceeds,
            "fees_paid": fees,
            "net_proceeds": net_proceeds,
            "effective_price": net_proceeds / coins_to_sell
        }
    
    def suggest_trade_with_fees(self, action, amount, coin, price):
        """Suggest a trade with full fee disclosure"""
        if action == "buy":
            calc = self.calculate_buy_with_fees(amount, price)
            return f"""
💸 BUY SUGGESTION FOR {coin}
================================
Requested: ${amount:.2f}
Coin Price: ${price:.2f}

FEE BREAKDOWN:
• Trade Amount: ${calc['usd_spent']:.2f}
• Fees (1.1%): ${calc['fees_paid']:.2f}
• Total Cost: ${calc['total_cost']:.2f}

YOU WILL RECEIVE:
• {calc['coins_received']:.6f} {coin}
• Effective Price: ${calc['effective_price']:.2f}
================================
"""
        else:  # sell
            calc = self.calculate_sell_with_fees(amount, price)
            return f"""
💰 SELL SUGGESTION FOR {amount:.6f} {coin}
================================
Coin Price: ${price:.2f}
Gross Value: ${calc['gross_proceeds']:.2f}

FEE BREAKDOWN:
• Fees (1.1%): ${calc['fees_paid']:.2f}
• Net Proceeds: ${calc['net_proceeds']:.2f}

YOU WILL RECEIVE:
• ${calc['net_proceeds']:.2f} USD
• Effective Price: ${calc['effective_price']:.2f}
================================
"""
    
    def validate_liquidity_for_buy(self, requested_amount, available_usd):
        """Check if we have enough USD including fees"""
        total_needed = requested_amount * (1 + self.TOTAL_MARKET_FEE)
        
        if available_usd < total_needed:
            shortfall = total_needed - available_usd
            return False, f"Insufficient funds! Need ${total_needed:.2f} (including ${requested_amount * self.TOTAL_MARKET_FEE:.2f} fees), have ${available_usd:.2f}. Short ${shortfall:.2f}"
        
        return True, f"Sufficient funds. Will use ${total_needed:.2f} total (${requested_amount:.2f} + ${requested_amount * self.TOTAL_MARKET_FEE:.2f} fees)"
    
    def adjust_size_for_fees(self, base_size, action="buy"):
        """Adjust order size to account for fees"""
        if action == "buy":
            # Reduce size to account for fees
            return base_size / (1 + self.TOTAL_MARKET_FEE)
        else:
            # For sells, the fee comes out of proceeds, not size
            return base_size


# Example usage for inheritance
class SmartTrader(FeeAwareTrader):
    def __init__(self):
        super().__init__()
        print("🧠 Smart Trader initialized with fee awareness")
        print(f"📊 Market order fees: {self.TOTAL_MARKET_FEE*100:.1f}%")
        print(f"📊 Limit order fees: {self.MAKER_FEE*100:.1f}%")
    
    def buy_with_disclosure(self, coin, usd_amount):
        """Buy with full fee disclosure"""
        # Get current price
        ticker = self.client.get_product(f"{coin}-USD")
        price = float(ticker.price)
        
        # Show fee impact
        print(self.suggest_trade_with_fees("buy", usd_amount, coin, price))
        
        # Calculate actual buy amount after fees
        adjusted_amount = self.adjust_size_for_fees(usd_amount, "buy")
        
        # Place order
        order = self.client.market_order_buy(
            client_order_id=f"smart_buy_{coin}_{int(time.time()*1000)}",
            product_id=f"{coin}-USD",
            quote_size=str(adjusted_amount)
        )
        
        return order


if __name__ == "__main__":
    # Demo the fee calculations
    trader = FeeAwareTrader()
    
    print("📊 FEE AWARENESS DEMO")
    print("=" * 50)
    
    # Example: Buying $100 of SOL at $206
    print(trader.suggest_trade_with_fees("buy", 100, "SOL", 206))
    
    # Example: Selling 1 SOL at $206
    print(trader.suggest_trade_with_fees("sell", 1, "SOL", 206))
    
    # Check liquidity sufficiency
    has_funds, message = trader.validate_liquidity_for_buy(100, 110)
    print(f"✅ {message}" if has_funds else f"❌ {message}")