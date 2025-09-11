#!/usr/bin/env python3
"""
🧽 SPONGY THROTTLE CONTROLLER
Provides elastic resistance to aggressive trading
The more you push, the more it resists
"""

import json
import time
from datetime import datetime, timedelta

class SpongyThrottle:
    def __init__(self):
        self.throttle_state_file = "spongy_throttle_state.json"
        self.load_state()
        
        # Spongy parameters
        self.BASE_DELAY = 60  # Base seconds between trades
        self.PRESSURE_MULTIPLIER = 1.5  # Each trade increases delay by 50%
        self.RECOVERY_RATE = 0.9  # Pressure decreases 10% per cycle
        self.MAX_PRESSURE = 10  # Maximum throttle multiplier
        self.EMERGENCY_BRAKE = 5  # Stop trading if pressure > 5
        
        # Trade limits that get more restrictive with pressure
        self.BASE_TRADE_SIZE = 100  # Starting trade size
        self.MIN_TRADE_SIZE = 20  # Minimum when compressed
        
    def load_state(self):
        """Load throttle state"""
        try:
            with open(self.throttle_state_file, 'r') as f:
                self.state = json.load(f)
        except:
            self.state = {
                "pressure": 1.0,
                "last_trade": None,
                "trades_this_hour": 0,
                "hour_start": datetime.now().isoformat(),
                "total_deployed": 0
            }
    
    def save_state(self):
        """Save throttle state"""
        with open(self.throttle_state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_pressure(self):
        """Get current throttle pressure (1.0 = relaxed, 10.0 = maximum compression)"""
        # Reduce pressure over time (spongy recovery)
        if self.state["last_trade"]:
            last_trade = datetime.fromisoformat(self.state["last_trade"])
            time_since = (datetime.now() - last_trade).seconds
            recovery_cycles = time_since / 300  # Recover every 5 minutes
            
            self.state["pressure"] *= (self.RECOVERY_RATE ** recovery_cycles)
            self.state["pressure"] = max(1.0, self.state["pressure"])
        
        return self.state["pressure"]
    
    def should_trade(self, proposed_amount):
        """Check if trade should be allowed based on spongy resistance"""
        pressure = self.get_pressure()
        
        # Emergency brake
        if pressure > self.EMERGENCY_BRAKE:
            return False, "🛑 EMERGENCY BRAKE: Throttle at maximum compression!"
        
        # Check time since last trade
        if self.state["last_trade"]:
            last_trade = datetime.fromisoformat(self.state["last_trade"])
            seconds_since = (datetime.now() - last_trade).seconds
            required_delay = self.BASE_DELAY * pressure
            
            if seconds_since < required_delay:
                remaining = required_delay - seconds_since
                return False, f"⏰ THROTTLE: Wait {remaining:.0f}s (pressure: {pressure:.1f}x)"
        
        # Reduce trade size based on pressure
        max_trade = self.BASE_TRADE_SIZE / pressure
        if proposed_amount > max_trade:
            return False, f"📉 THROTTLE: Max trade ${max_trade:.2f} at pressure {pressure:.1f}x"
        
        # Check hourly limits
        hour_start = datetime.fromisoformat(self.state["hour_start"])
        if (datetime.now() - hour_start).seconds > 3600:
            # Reset hourly counters
            self.state["trades_this_hour"] = 0
            self.state["hour_start"] = datetime.now().isoformat()
            self.state["total_deployed"] = 0
        
        # Progressive hourly limits
        max_trades = int(10 / pressure)  # Fewer trades when compressed
        if self.state["trades_this_hour"] >= max_trades:
            return False, f"📊 HOURLY LIMIT: {max_trades} trades at pressure {pressure:.1f}x"
        
        return True, f"✅ Trade allowed (pressure: {pressure:.1f}x)"
    
    def record_trade(self, amount):
        """Record a trade and increase pressure"""
        self.state["pressure"] = min(self.MAX_PRESSURE, 
                                     self.state["pressure"] * self.PRESSURE_MULTIPLIER)
        self.state["last_trade"] = datetime.now().isoformat()
        self.state["trades_this_hour"] += 1
        self.state["total_deployed"] += amount
        self.save_state()
        
        print(f"🧽 THROTTLE: Pressure now {self.state['pressure']:.1f}x")
    
    def get_status(self):
        """Get throttle status"""
        pressure = self.get_pressure()
        
        status = {
            "pressure": pressure,
            "state": "RELAXED" if pressure < 2 else "COMPRESSED" if pressure < 5 else "MAXED",
            "trades_this_hour": self.state["trades_this_hour"],
            "next_trade_delay": int(self.BASE_DELAY * pressure),
            "max_trade_size": self.BASE_TRADE_SIZE / pressure,
            "recommendation": self.get_recommendation(pressure)
        }
        
        return status
    
    def get_recommendation(self, pressure):
        """Get trading recommendation based on pressure"""
        if pressure < 2:
            return "🟢 Normal trading allowed"
        elif pressure < 3:
            return "🟡 Slow down, building pressure"
        elif pressure < 5:
            return "🟠 High pressure, reduce activity"
        else:
            return "🔴 Maximum compression, stop trading"


# Integration with flywheels
class ThrottledFlywheel:
    def __init__(self):
        self.throttle = SpongyThrottle()
    
    def attempt_trade(self, coin, amount):
        """Attempt a trade with spongy throttle check"""
        can_trade, message = self.throttle.should_trade(amount)
        
        if can_trade:
            print(f"🚀 Executing {coin} trade for ${amount:.2f}")
            self.throttle.record_trade(amount)
            # Execute actual trade here
            return True
        else:
            print(f"🧽 {message}")
            return False
    
    def status(self):
        """Get throttle status"""
        return self.throttle.get_status()


if __name__ == "__main__":
    print("🧽 SPONGY THROTTLE DEMONSTRATION")
    print("=" * 60)
    
    throttle = SpongyThrottle()
    status = throttle.get_status()
    
    print(f"Current Pressure: {status['pressure']:.1f}x")
    print(f"State: {status['state']}")
    print(f"Trades This Hour: {status['trades_this_hour']}")
    print(f"Next Trade Delay: {status['next_trade_delay']}s")
    print(f"Max Trade Size: ${status['max_trade_size']:.2f}")
    print(f"Recommendation: {status['recommendation']}")
    
    print("\n" + "=" * 60)
    print("The spongy throttle provides elastic resistance:")
    print("• The more you trade, the more it resists")
    print("• It slowly recovers when you stop pushing")
    print("• Emergency brake at 5x pressure")
    print("• Trade sizes shrink as pressure builds")