#!/usr/bin/env python3
"""
🌞 Solar Weather Forecast & Market Impact Analysis
Cherokee Trading Council Solar Oracle
"""

import requests
import json
from datetime import datetime, timedelta

def get_solar_forecast():
    """Get comprehensive solar weather forecast"""
    print("🌞 CHEROKEE SOLAR ORACLE - SPACE WEATHER FORECAST")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get current solar conditions
    try:
        # Planetary K-index (geomagnetic activity)
        kp_url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        response = requests.get(kp_url, timeout=10)
        kp_data = response.json()
        
        if len(kp_data) > 1:
            latest_kp = kp_data[-1]  # Most recent reading
            kp_value = float(latest_kp[1])
            kp_time = latest_kp[0]
            
            print(f"📊 CURRENT GEOMAGNETIC CONDITIONS:")
            print(f"   Kp Index: {kp_value:.1f}")
            print(f"   Time: {kp_time}")
            
            # Interpret Kp level
            if kp_value < 3:
                print("   Status: 🟢 QUIET (Low volatility expected)")
                trading_impact = "BULLISH - Calm conditions favor risk-on"
            elif kp_value < 5:
                print("   Status: 🟡 UNSETTLED (Moderate volatility)")
                trading_impact = "NEUTRAL - Normal market conditions"
            elif kp_value < 7:
                print("   Status: 🟠 STORM (High volatility likely)")
                trading_impact = "CAUTIOUS - Expect sudden moves"
            else:
                print("   Status: 🔴 SEVERE STORM (Extreme volatility)")
                trading_impact = "BEARISH - Risk-off conditions"
            
            print(f"   Trading Impact: {trading_impact}")
    except Exception as e:
        print(f"   ⚠️ Could not get Kp index: {e}")
    
    print()
    
    # Get 3-day forecast
    try:
        forecast_url = "https://services.swpc.noaa.gov/text/3-day-forecast.txt"
        response = requests.get(forecast_url, timeout=10)
        forecast_text = response.text
        
        print("📅 3-DAY FORECAST:")
        print("-" * 40)
        
        # Parse the forecast text
        lines = forecast_text.split('\n')
        in_forecast = False
        
        for line in lines:
            if 'NOAA Kp index breakdown' in line:
                in_forecast = True
            elif in_forecast and line.strip():
                if any(date_str in line for date_str in ['Sep 01', 'Sep 02', 'Sep 03']):
                    print(f"   {line.strip()}")
                elif 'G1' in line or 'G2' in line or 'G3' in line:
                    print(f"   Storm Level: {line.strip()}")
    except:
        pass
    
    # Get solar wind data
    try:
        print()
        print("💨 SOLAR WIND CONDITIONS:")
        print("-" * 40)
        
        wind_url = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
        response = requests.get(wind_url, timeout=10)
        wind_data = response.json()
        
        if len(wind_data) > 1:
            latest = wind_data[-1]
            speed = float(latest[2]) if len(latest) > 2 else 0
            density = float(latest[1]) if len(latest) > 1 else 0
            
            print(f"   Speed: {speed:.0f} km/s")
            print(f"   Density: {density:.1f} p/cc")
            
            if speed > 600:
                print("   ⚠️ HIGH SPEED STREAM - Expect volatility!")
            elif speed > 500:
                print("   🟡 Elevated solar wind")
            else:
                print("   🟢 Normal solar wind")
    except:
        pass
    
    # Cherokee Trading Analysis
    print()
    print("🔥 CHEROKEE TRADING COUNCIL INTERPRETATION:")
    print("=" * 70)
    
    try:
        if 'kp_value' in locals():
            if kp_value < 3:
                print("🟢 SOLAR BLESSING - The cosmos smiles upon risk")
                print("   • BTC/ETH likely to trend up")
                print("   • Good day for position building")
                print("   • Sacred Fire burns bright and steady")
            elif kp_value < 5:
                print("🟡 SOLAR NEUTRAL - Standard trading conditions")
                print("   • Follow normal strategies")
                print("   • Watch for afternoon volatility")
                print("   • Two Wolves in balance")
            elif kp_value < 7:
                print("🟠 SOLAR WARNING - Storm approaching")
                print("   • Reduce position sizes")
                print("   • Set tight stops")
                print("   • Prepare for sudden moves")
                print("   • Fear Wolf awakening")
            else:
                print("🔴 SOLAR STORM - Take defensive positions!")
                print("   • Consider going to cash")
                print("   • Avoid new positions")
                print("   • Wait for storm to pass")
                print("   • Sacred Fire needs protection")
            
            # The Force calculation
            force_strength = max(0, min(100, 100 - (kp_value * 10)))
            print()
            print(f"⚡ THE FORCE STRENGTH: {force_strength}/100")
            
            if force_strength > 70:
                print("   The Force is strong - favorable for trading")
            elif force_strength > 40:
                print("   The Force is balanced - trade carefully")
            else:
                print("   The Force is disturbed - defensive mode")
    except:
        pass
    
    print()
    print("🦅 Eagle Eye says: Solar weather affects human psychology")
    print("🐺 Coyote says: Use the chaos to our advantage")
    print("🐢 Turtle says: Seven generations thinking transcends solar storms")
    print()
    print("=" * 70)
    
    # Save to file for thermal memory
    try:
        solar_data = {
            'timestamp': datetime.now().isoformat(),
            'kp_index': kp_value if 'kp_value' in locals() else None,
            'force_strength': force_strength if 'force_strength' in locals() else None,
            'trading_stance': trading_impact if 'trading_impact' in locals() else 'UNKNOWN'
        }
        
        with open('/home/dereadi/scripts/claude/solar_forecast.json', 'w') as f:
            json.dump(solar_data, f, indent=2)
        
        print("✅ Solar forecast saved to thermal memory")
    except:
        pass

if __name__ == "__main__":
    get_solar_forecast()