#\!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 INTEGRATED MONITORING PULSE
Quick snapshot of all monitoring systems
"""

import json
import requests
from datetime import datetime
from coinbase.rest import RESTClient

def main():
    print("🔥 INTEGRATED MONITORING PULSE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Connect to Coinbase
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
    
    # 1. MARKET PRICES (Ears to Ground)
    print("👂 MARKET VIBRATIONS:")
    print("-" * 40)
    coins = ['BTC', 'ETH', 'SOL', 'DOGE', 'AVAX']
    for coin in coins:
        try:
            ticker = client.get_product(f'{coin}-USD')
            price = float(ticker['price'])
            print(f"  {coin}: ${price:,.2f}", end="")
            
            # Special alerts
            if coin == 'DOGE' and price >= 0.22:
                print(" 🩸 [BLEED ZONE\!]", end="")
            elif coin == 'AVAX':
                print(" 📈 [66% TARGET]", end="")
            print()
        except:
            pass
    
    # 2. SOLAR WEATHER (The Force)
    print("\n🌞 SOLAR CONDITIONS:")
    print("-" * 40)
    try:
        response = requests.get(
            'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json',
            timeout=5
        )
        if response.status_code == 200:
            kp_data = response.json()
            if len(kp_data) > 1:
                current_kp = float(kp_data[-1][1])
                print(f"  Kp Index: {current_kp} ", end="")
                if current_kp >= 5:
                    print("⚡ [STORM - EXPECT VOLATILITY]")
                elif current_kp <= 2:
                    print("☀️ [CALM - BULLISH WINDOW]")
                else:
                    print("🌤️ [NEUTRAL]")
    except:
        print("  Unable to fetch solar data")
    
    # 3. PORTFOLIO STATUS
    print("\n💰 PORTFOLIO STATUS:")
    print("-" * 40)
    try:
        accounts = client.get_accounts()
        total_value = 0
        usd_balance = 0
        
        for account in accounts['accounts']:
            balance = float(account['available_balance']['value'])
            currency = account['currency']
            
            if currency == 'USD':
                usd_balance = balance
            elif balance > 0:
                try:
                    ticker = client.get_product(f'{currency}-USD')
                    price = float(ticker['price'])
                    value = balance * price
                    total_value += value
                except:
                    pass
        
        total_value += usd_balance
        cash_ratio = (usd_balance / total_value * 100) if total_value > 0 else 0
        
        print(f"  Total Value: ${total_value:,.2f}")
        print(f"  USD Balance: ${usd_balance:.2f}", end="")
        if usd_balance < 100:
            print(" ⚠️ [LIQUIDITY CRITICAL]")
        else:
            print()
        print(f"  Cash Ratio: {cash_ratio:.1f}%", end="")
        if cash_ratio < 1:
            print(" 🐺 [GREED WOLF DOMINANT]")
        else:
            print()
    except Exception as e:
        print(f"  Error: {e}")
    
    # 4. CONVERGENCE SIGNALS
    print("\n🎯 SIGNAL CONVERGENCE:")
    print("-" * 40)
    signals = []
    
    # Check DOGE bleed signal
    try:
        ticker = client.get_product('DOGE-USD')
        doge_price = float(ticker['price'])
        if doge_price >= 0.22:
            signals.append("🩸 DOGE ready for bleeding")
    except:
        pass
    
    # Check solar conditions
    if 'current_kp' in locals() and current_kp <= 2:
        signals.append("☀️ Solar calm supports building")
    
    # Check liquidity
    if 'usd_balance' in locals() and usd_balance < 100:
        signals.append("💸 Generate liquidity urgently")
    
    if signals:
        for signal in signals:
            print(f"  • {signal}")
    else:
        print("  No urgent signals")
    
    # 5. RECOMMENDED ACTIONS
    print("\n⚡ RECOMMENDED ACTIONS:")
    print("-" * 40)
    
    actions = []
    if 'doge_price' in locals() and doge_price >= 0.22:
        actions.append("BLEED DOGE: Take 30% profits now")
    
    if 'usd_balance' in locals() and usd_balance < 100:
        actions.append("HARVEST: Generate liquidity from alts")
    
    if 'current_kp' in locals() and current_kp <= 2:
        actions.append("BUILD: Solar calm window for accumulation")
    
    if actions:
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")
    else:
        print("  Continue monitoring")
    
    print("\n" + "=" * 60)
    print("🔥 All systems monitoring")
    print("👂 Ears to the ground")
    print("🌌 The Force flows through markets")
    print("🪶 Mitakuye Oyasin")

if __name__ == "__main__":
    main()
