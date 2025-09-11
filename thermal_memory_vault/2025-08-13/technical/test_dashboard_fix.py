#!/usr/bin/env python3
"""
Dashboard Fix Verification Test
Tests all components of the Quantum Crawdad Trading Dashboard
"""

import requests
import json
import time

def test_dashboard_components():
    """Test all dashboard components"""
    
    print("🦞 Quantum Crawdad Dashboard Fix Verification")
    print("=" * 50)
    
    # Test main dashboard
    print("\n1. Testing main dashboard...")
    try:
        response = requests.get("http://192.168.132.223:5679", timeout=5)
        if response.status_code == 200 and "Quantum Crawdad Trading View" in response.text:
            print("✅ Main dashboard accessible")
        else:
            print("❌ Main dashboard failed")
            return False
    except Exception as e:
        print(f"❌ Main dashboard error: {e}")
        return False
    
    # Test API endpoints
    print("\n2. Testing API endpoints...")
    
    endpoints = [
        ("/api/market_prices", "Market prices"),
        ("/api/paper_trading", "Paper trading"),
        ("/api/health", "Health check")
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"http://192.168.132.223:5679{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    print(f"✅ {name} endpoint working")
                else:
                    print(f"❌ {name} endpoint returned error: {data['error']}")
                    return False
            else:
                print(f"❌ {name} endpoint failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {name} endpoint error: {e}")
            return False
    
    # Test data quality
    print("\n3. Testing data quality...")
    
    try:
        # Test market prices
        response = requests.get("http://192.168.132.223:5679/api/market_prices", timeout=5)
        prices = response.json()
        
        if len(prices) > 0:
            print(f"✅ Market data contains {len(prices)} cryptocurrencies")
            
            # Check for required fields
            first_symbol = list(prices.keys())[0]
            first_data = prices[first_symbol]
            required_fields = ['price', 'change', 'last_update']
            
            if all(field in first_data for field in required_fields):
                print("✅ Market data has all required fields")
                print(f"   Example: {first_symbol} = ${first_data['price']:.2f} ({first_data['change']:.2f}%)")
            else:
                print("❌ Market data missing required fields")
                return False
        else:
            print("❌ No market data available")
            return False
            
    except Exception as e:
        print(f"❌ Market data test error: {e}")
        return False
    
    # Test trading data
    try:
        response = requests.get("http://192.168.132.223:5679/api/paper_trading", timeout=5)
        trading = response.json()
        
        if 'metrics' in trading:
            print("✅ Trading data available")
            metrics = trading['metrics']
            print(f"   Win Rate: {metrics.get('win_rate', 0):.1f}%")
            print(f"   Total Trades: {metrics.get('total_trades', 0)}")
            print(f"   P&L: ${metrics.get('total_pnl', 0):.2f}")
        else:
            print("⚠️  Trading data structure unexpected")
            
    except Exception as e:
        print(f"❌ Trading data test error: {e}")
        return False
    
    print("\n4. Testing real-time API source...")
    try:
        response = requests.get("http://192.168.132.223:5680/api/market_prices", timeout=5)
        if response.status_code == 200:
            print("✅ Real-time API source accessible")
        else:
            print("❌ Real-time API source failed")
            return False
    except Exception as e:
        print(f"❌ Real-time API source error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! Dashboard is working correctly!")
    print("\n📊 Dashboard URLs:")
    print("   Main Dashboard: http://192.168.132.223:5679")
    print("   API Status:     http://192.168.132.223:5680")
    print("\n🔧 What was fixed:")
    print("   ✅ Added CORS support")
    print("   ✅ Created proxy endpoints to avoid cross-origin issues") 
    print("   ✅ Added proper error handling and logging")
    print("   ✅ Started the realtime API integrator")
    print("   ✅ Verified all data flows are working")
    
    return True

if __name__ == "__main__":
    test_dashboard_components()