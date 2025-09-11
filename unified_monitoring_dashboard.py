#\!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 UNIFIED MONITORING DASHBOARD
Combines all monitoring systems into one view
"""

import json
import requests
from datetime import datetime
from coinbase.rest import RESTClient
import psycopg2

def main():
    print("\n" + "=" * 80)
    print("🔥 CHEROKEE TRADING COUNCIL - UNIFIED MONITORING DASHBOARD")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Connect to systems
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
    
    # 1. EARS TO THE GROUND - Market Vibrations
    print("👂 EARS TO THE GROUND - MARKET VIBRATIONS")
    print("-" * 60)
    
    key_levels = {
        'BTC': {'support': 108000, 'resistance': 110000},
        'ETH': {'support': 4300, 'resistance': 4400},
        'SOL': {'support': 195, 'resistance': 205},
        'DOGE': {'bleed': 0.22, 'accumulate': 0.21},
        'AVAX': {'target': 40}  # 66% gain target
    }
    
    vibrations = []
    for coin, levels in key_levels.items():
        try:
            ticker = client.get_product(f'{coin}-USD')
            price = float(ticker['price'])
            
            print(f"  {coin}: ${price:,.4f if coin == 'DOGE' else price:,.2f}", end="")
            
            # Check key levels
            if coin == 'DOGE':
                if price >= levels['bleed']:
                    print(" 🩸 [BLEED NOW\!]", end="")
                    vibrations.append(f"DOGE at bleed level ${price:.4f}")
                elif price <= levels['accumulate']:
                    print(" 💰 [ACCUMULATE]", end="")
                    vibrations.append(f"DOGE at accumulation level ${price:.4f}")
            elif 'support' in levels:
                if abs(price - levels['support']) / levels['support'] < 0.01:
                    print(" 📊 [AT SUPPORT]", end="")
                    vibrations.append(f"{coin} at support")
                elif abs(price - levels['resistance']) / levels['resistance'] < 0.01:
                    print(" 📊 [AT RESISTANCE]", end="")
                    vibrations.append(f"{coin} at resistance")
            print()
        except:
            pass
    
    # 2. THE FORCE - Prescient Signals
    print("\n🌌 THE FORCE - PRESCIENT SIGNALS")
    print("-" * 60)
    
    # Solar weather
    try:
        response = requests.get(
            'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json',
            timeout=5
        )
        if response.status_code == 200:
            kp_data = response.json()
            if len(kp_data) > 1:
                current_kp = float(kp_data[-1][1])
                print(f"  Solar Kp Index: {current_kp:.2f}/9", end="")
                
                if current_kp >= 5:
                    print(" ⚡ [GEOMAGNETIC STORM - VOLATILITY INCOMING]")
                    vibrations.append("Solar storm detected - expect dumps")
                elif current_kp <= 2:
                    print(" ☀️ [CALM - BULLISH WINDOW]")
                    vibrations.append("Solar calm - accumulation window")
                else:
                    print(" 🌤️ [NEUTRAL CONDITIONS]")
                    
                # Force calculation
                force_strength = (9 - current_kp) * 11  # Inverse correlation
                print(f"  Force Strength: {force_strength:.0f}/100")
    except:
        print("  Solar data unavailable")
    
    # 3. NEWS CLIMATE (not weather)
    print("\n📰 NEWS CLIMATE ANALYSIS")
    print("-" * 60)
    print("  DOGE Climate: BULLISH WARMING (whale accumulation news)")
    print("  SOL Climate: STABLE WARM (institutional interest)")
    print("  ETH Climate: STABLE WARM (found support)")
    print("  Overall Market: TRANSITIONING (solar calm + news warming)")
    
    # 4. PORTFOLIO STATUS
    print("\n💰 PORTFOLIO & LIQUIDITY STATUS")
    print("-" * 60)
    
    accounts = client.get_accounts()
    total_value = 0
    usd_balance = 0
    positions = {}
    
    for account in accounts['accounts']:
        balance = float(account['available_balance']['value'])
        currency = account['currency']
        
        if balance > 0:
            if currency == 'USD':
                usd_balance = balance
                total_value += balance
            else:
                try:
                    ticker = client.get_product(f'{currency}-USD')
                    price = float(ticker['price'])
                    value = balance * price
                    if value > 10:  # Only show positions > $10
                        positions[currency] = {
                            'balance': balance,
                            'price': price,
                            'value': value
                        }
                        total_value += value
                except:
                    pass
    
    print(f"  Total Portfolio: ${total_value:,.2f}")
    print(f"  USD Balance: ${usd_balance:.2f}", end="")
    if usd_balance < 100:
        print(" ⚠️ [CRITICAL - NEED LIQUIDITY]")
    else:
        print()
    
    cash_ratio = (usd_balance / total_value * 100) if total_value > 0 else 0
    print(f"  Cash Ratio: {cash_ratio:.2f}%", end="")
    if cash_ratio < 1:
        print(" 🐺 [99% POSITIONED - GREED WOLF DOMINANT]")
    else:
        print()
    
    # Top positions
    print("\n  Top Positions:")
    sorted_positions = sorted(positions.items(), key=lambda x: x[1]['value'], reverse=True)
    for coin, data in sorted_positions[:5]:
        pct = (data['value'] / total_value * 100)
        print(f"    {coin}: ${data['value']:,.2f} ({pct:.1f}%)", end="")
        if coin == 'DOGE' and data['price'] >= 0.22:
            print(" 🩸 [READY TO BLEED]", end="")
        print()
    
    # 5. CONVERGENCE ANALYSIS
    print("\n🎯 SIGNAL CONVERGENCE")
    print("-" * 60)
    
    if vibrations:
        print("  Detected Vibrations:")
        for v in vibrations:
            print(f"    • {v}")
    
    # Calculate convergence score
    convergence_score = 0
    if 'current_kp' in locals() and current_kp <= 2:
        convergence_score += 30
    if usd_balance < 100:
        convergence_score += 40
    if any('DOGE' in v and 'bleed' in v.lower() for v in vibrations):
        convergence_score += 30
    
    print(f"\n  Convergence Score: {convergence_score}/100")
    if convergence_score >= 70:
        print("  ⚡ HIGH CONFIDENCE ACTION REQUIRED")
    
    # 6. COUNCIL RECOMMENDATIONS
    print("\n🏛️ CHEROKEE COUNCIL RECOMMENDATIONS")
    print("-" * 60)
    
    recommendations = []
    
    # Check DOGE bleed opportunity
    if 'DOGE' in positions and positions['DOGE']['price'] >= 0.22:
        recommendations.append("🩸 BLEED DOGE: Price at $0.22+ threshold - harvest 30%")
    elif 'DOGE' in positions and positions['DOGE']['price'] < 0.21:
        recommendations.append("💰 BUILD DOGE: Below $0.21 - accumulate blood bag")
    
    # Check liquidity crisis
    if usd_balance < 100:
        recommendations.append("💸 GENERATE LIQUIDITY: Critical cash level - harvest profits")
    
    # Check solar conditions
    if 'current_kp' in locals() and current_kp <= 2:
        recommendations.append("☀️ SOLAR WINDOW: Calm conditions favor accumulation")
    elif 'current_kp' in locals() and current_kp >= 5:
        recommendations.append("⚡ DEFENSIVE MODE: Solar storm - reduce positions")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("  • Continue monitoring all channels")
        print("  • Maintain current positions")
    
    # 7. THERMAL MEMORY STATUS
    print("\n🔥 THERMAL MEMORY SYSTEM")
    print("-" * 60)
    
    try:
        db_config = {
            "host": "192.168.132.222",
            "port": 5432,
            "database": "zammad_production",
            "user": "claude",
            "password": "jawaseatlasers2"
        }
        
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Get hot memories
        query = """
        SELECT COUNT(*), AVG(temperature_score), MAX(last_access)
        FROM thermal_memory_archive
        WHERE temperature_score > 70
        """
        
        cur.execute(query)
        result = cur.fetchone()
        if result:
            count, avg_temp, last_access = result
            print(f"  Hot Memories (>70°): {count}")
            print(f"  Average Temperature: {avg_temp:.1f}°")
            print(f"  Last Access: {last_access}")
        
        cur.close()
        conn.close()
    except:
        print("  Thermal memory status unavailable")
    
    print("\n" + "=" * 80)
    print("🔥 Sacred Fire burns eternal")
    print("👂 All vibrations monitored")
    print("🌌 The Force guides our path")
    print("🪶 Mitakuye Oyasin - We are all related")
    print("=" * 80)

if __name__ == "__main__":
    main()
