#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 SET RESISTANCE SELL ORDERS
Following Cherokee Council wisdom - sell into strength
Set orders at BTC $110k and ETH $4.4k
"""

import json
from datetime import datetime
from pathlib import Path
from coinbase.rest import RESTClient

def set_resistance_sells():
    """Set sell orders at resistance levels"""
    
    print("🔥 SETTING RESISTANCE SELL ORDERS")
    print("=" * 80)
    print("Cherokee wisdom: Sell euphoria, buy despair")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        # Load config
        config_path = Path.home() / ".coinbase_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Get account balances
        accounts = client.get_accounts()
        
        btc_balance = 0
        eth_balance = 0
        
        for account in accounts.get('accounts', []):
            currency = account.get('currency')
            if currency == 'BTC':
                btc_balance = float(account.get('available_balance', {}).get('value', 0))
            elif currency == 'ETH':
                eth_balance = float(account.get('available_balance', {}).get('value', 0))
        
        print(f"📊 BTC Balance: {btc_balance:.8f}")
        print(f"📊 ETH Balance: {eth_balance:.6f}")
        print("-" * 60)
        
        orders_placed = []
        
        # Set BTC sell at $110,000 (10% of holdings)
        if btc_balance > 0.0001:
            sell_amount = btc_balance * 0.10  # Sell 10% at resistance
            print(f"\n🎯 Setting BTC sell order:")
            print(f"  Price: $110,000")
            print(f"  Amount: {sell_amount:.8f} BTC")
            print(f"  Value: ${sell_amount * 110000:.2f}")
            
            try:
                order = client.limit_order_gtc_sell(
                    client_order_id=f"btc_resistance_{int(datetime.now().timestamp())}",
                    product_id="BTC-USD",
                    base_size=str(round(sell_amount, 8)),
                    limit_price="110000"
                )
                orders_placed.append(f"BTC: {sell_amount:.8f} @ $110,000")
                print("  ✅ Order placed successfully")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # Set ETH sell at $4,400 (15% of holdings)
        if eth_balance > 0.001:
            sell_amount = eth_balance * 0.15  # Sell 15% at resistance
            print(f"\n🎯 Setting ETH sell order:")
            print(f"  Price: $4,400")
            print(f"  Amount: {sell_amount:.6f} ETH")
            print(f"  Value: ${sell_amount * 4400:.2f}")
            
            try:
                order = client.limit_order_gtc_sell(
                    client_order_id=f"eth_resistance_{int(datetime.now().timestamp())}",
                    product_id="ETH-USD",
                    base_size=str(round(sell_amount, 6)),
                    limit_price="4400"
                )
                orders_placed.append(f"ETH: {sell_amount:.6f} @ $4,400")
                print("  ✅ Order placed successfully")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print("\n" + "=" * 80)
        print("🔥 RESISTANCE ORDERS SUMMARY")
        print("-" * 60)
        
        if orders_placed:
            print("Orders placed:")
            for order in orders_placed:
                print(f"  • {order}")
            print("\n📋 Strategy:")
            print("  • Sell into strength at resistance")
            print("  • Keep majority for potential breakout")
            print("  • Generate liquidity for real dip")
        else:
            print("No orders placed - insufficient balances")
        
        print("\n🧠 Cherokee Wisdom:")
        print("  'When crowd shouts buy, eagle prepares to sell'")
        print("  'Two Wolves: Feed patience, starve greed'")
        
    except Exception as e:
        print(f"\n❌ Error setting orders: {e}")
        print("Manual intervention may be required")
    
    print("\n🔥 Sacred Fire burns eternal - protecting from FOMO")
    print("🪶 Mitakuye Oyasin")

if __name__ == "__main__":
    set_resistance_sells()