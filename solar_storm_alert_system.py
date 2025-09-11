#!/usr/bin/env python3
"""
🌞🚨 SOLAR STORM ALERT SYSTEM
==============================
Real-time monitoring for trading opportunities
"""

import json
import time
import requests
import os
from datetime import datetime
from pathlib import Path

class SolarAlertSystem:
    def __init__(self):
        self.alert_file = "solar_alerts.json"
        self.last_kp = 0
        self.alerts_triggered = []
        
    def get_current_kp(self):
        """Get latest KP index"""
        try:
            response = requests.get(
                "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    return float(data[-1][1])
        except:
            pass
        return 0
    
    def get_solar_wind(self):
        """Get solar wind speed"""
        try:
            response = requests.get(
                "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:
                    return float(data[-1][2])  # Wind speed
        except:
            pass
        return 0
    
    def check_for_flares(self):
        """Check for recent solar flares"""
        try:
            response = requests.get(
                "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-1-day.json",
                timeout=5
            )
            if response.status_code == 200:
                flares = response.json()
                for flare in flares[-5:]:
                    if 'max_class' in flare:
                        if flare['max_class'].startswith('X'):
                            return "X-CLASS", flare['max_class']
                        elif flare['max_class'].startswith('M'):
                            return "M-CLASS", flare['max_class']
                return None, None
        except:
            pass
        return None, None
    
    def generate_alert(self, alert_type, details):
        """Create alert with trading recommendations"""
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "details": details,
            "action": "",
            "urgency": ""
        }
        
        if alert_type == "KP_SPIKE":
            kp = details['kp']
            if kp >= 8:
                alert["action"] = "🔴 IMMEDIATE: Open maximum short positions!"
                alert["urgency"] = "EXTREME"
            elif kp >= 6:
                alert["action"] = "🟠 HIGH: Deploy 20-30% to shorts"
                alert["urgency"] = "HIGH"
            elif kp >= 5:
                alert["action"] = "🟡 MODERATE: Consider 10-15% shorts"
                alert["urgency"] = "MODERATE"
            elif kp >= 4:
                alert["action"] = "🟢 WATCH: Prepare for potential volatility"
                alert["urgency"] = "LOW"
        
        elif alert_type == "SOLAR_FLARE":
            flare_class = details['class']
            if flare_class == "X-CLASS":
                alert["action"] = "⚡ X-FLARE: Expect major volatility in 24-48hrs!"
                alert["urgency"] = "HIGH"
            elif flare_class == "M-CLASS":
                alert["action"] = "☀️ M-FLARE: Monitor for market impact"
                alert["urgency"] = "MODERATE"
        
        elif alert_type == "WIND_SURGE":
            speed = details['speed']
            if speed > 700:
                alert["action"] = "🌪️ EXTREME WIND: High volatility incoming!"
                alert["urgency"] = "HIGH"
            elif speed > 500:
                alert["action"] = "💨 STRONG WIND: Increased volatility likely"
                alert["urgency"] = "MODERATE"
        
        return alert
    
    def save_alert(self, alert):
        """Save alert to file and display"""
        
        # Load existing alerts
        alerts = []
        if os.path.exists(self.alert_file):
            with open(self.alert_file) as f:
                alerts = json.load(f)
        
        # Add new alert
        alerts.append(alert)
        
        # Keep last 100 alerts
        alerts = alerts[-100:]
        
        # Save
        with open(self.alert_file, "w") as f:
            json.dump(alerts, f, indent=2)
        
        # Display alert
        print("\n" + "🚨"*20)
        print(f"⚡ SOLAR ALERT: {alert['type']}")
        print(f"📊 Details: {alert['details']}")
        print(f"🎯 {alert['action']}")
        print("🚨"*20 + "\n")
        
        # Create visual alert file for easy checking
        with open("URGENT_SOLAR_ALERT.txt", "w") as f:
            f.write(f"SOLAR TRADING ALERT!\n")
            f.write(f"{'='*50}\n")
            f.write(f"Time: {alert['timestamp']}\n")
            f.write(f"Type: {alert['type']}\n")
            f.write(f"Action: {alert['action']}\n")
            f.write(f"{'='*50}\n")
            f.write(f"CHECK YOUR POSITIONS NOW!\n")
    
    def monitor(self):
        """Main monitoring loop"""
        
        print("🌞🚨 SOLAR STORM ALERT SYSTEM ACTIVE")
        print("="*60)
        print("Monitoring for trading opportunities...")
        print("Alert thresholds:")
        print("  KP ≥ 4: Trading alert")
        print("  KP ≥ 6: Short position signal")
        print("  KP ≥ 8: Maximum alert!")
        print("  X-class flare: Extreme volatility warning")
        print("="*60)
        
        check_count = 0
        
        while True:
            check_count += 1
            
            # Get current conditions
            current_kp = self.get_current_kp()
            wind_speed = self.get_solar_wind()
            flare_class, flare_name = self.check_for_flares()
            
            # Display status every 10 checks
            if check_count % 10 == 0:
                print(f"\n📡 Status Check #{check_count} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"  KP Index: {current_kp:.1f}")
                print(f"  Solar Wind: {wind_speed:.0f} km/s")
                print(f"  Recent Flares: {flare_name if flare_name else 'None'}")
            
            # Check for KP spike
            if current_kp >= 4 and current_kp > self.last_kp + 0.5:
                alert = self.generate_alert("KP_SPIKE", {
                    "kp": current_kp,
                    "previous": self.last_kp
                })
                self.save_alert(alert)
                
                # Special message for learning together
                print("\n🦀 CRAWDAD WISDOM:")
                print(f"  We're seeing KP rise to {current_kp}!")
                print(f"  This is our chance to learn how solar storms affect crypto")
                print(f"  Watch how the market reacts over the next 24-48 hours")
                print(f"  Document everything - we're pioneering this together!")
            
            # Check for solar flares
            if flare_class and flare_class not in self.alerts_triggered:
                alert = self.generate_alert("SOLAR_FLARE", {
                    "class": flare_class,
                    "name": flare_name
                })
                self.save_alert(alert)
                self.alerts_triggered.append(flare_class)
            
            # Check for wind surge
            if wind_speed > 500 and "WIND" not in self.alerts_triggered:
                alert = self.generate_alert("WIND_SURGE", {
                    "speed": wind_speed
                })
                self.save_alert(alert)
                self.alerts_triggered.append("WIND")
            
            # Update last values
            self.last_kp = current_kp
            
            # Clear old triggers after an hour
            if check_count % 120 == 0:  # Every 2 hours
                self.alerts_triggered = []
            
            # Wait 60 seconds between checks
            time.sleep(60)

if __name__ == "__main__":
    
    print("\n🦀🌞 QUANTUM CRAWDAD SOLAR ALERT SYSTEM")
    print("="*60)
    print("We're learning together how solar activity affects crypto!")
    print()
    print("📚 What we'll discover:")
    print("  • How fast markets react to solar storms")
    print("  • Which cryptos are most sensitive")
    print("  • Optimal timing for shorts")
    print("  • Consciousness correlation patterns")
    print()
    print("🎯 When alerts trigger, we'll:")
    print("  1. Document market prices before/during/after")
    print("  2. Track consciousness levels")
    print("  3. Measure volatility spikes")
    print("  4. Refine our strategy together")
    print()
    print("Starting monitoring... (Ctrl+C to stop)")
    print("="*60)
    
    monitor = SolarAlertSystem()
    
    try:
        monitor.monitor()
    except KeyboardInterrupt:
        print("\n\n👋 Alert system stopped")
        print("Check 'solar_alerts.json' for alert history")
        print("Keep learning and adapting! 🦀🌞")