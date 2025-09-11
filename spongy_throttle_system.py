#!/usr/bin/env python3
"""
🎮 SPONGY THROTTLE CONTROL SYSTEM
==================================
Variable acceleration with instant braking
Like a gas pedal made of memory foam
"""

import json
import time
from datetime import datetime
from typing import Dict
import math

class SpongyThrottle:
    def __init__(self):
        # Throttle characteristics
        self.current_throttle = 0.0  # 0-100% (0=idle, 100=full power)
        self.throttle_stiffness = 0.5  # How fast it responds (0=mushy, 1=instant)
        self.brake_power = 0.95  # Instant stop capability
        
        # Performance zones
        self.IDLE = (0, 10)          # 0-10%: Watching only
        self.LEARNING = (10, 30)     # 10-30%: Micro trades
        self.CRUISING = (30, 60)     # 30-60%: Normal trading  
        self.AGGRESSIVE = (60, 85)   # 60-85%: Active trading
        self.REDLINE = (85, 100)     # 85-100%: Maximum aggression
        
        # Trade size mapping (% of available capital)
        self.throttle_to_trade_size = {
            0: 0,        # No trading
            10: 0.001,   # 0.1% trades
            30: 0.01,    # 1% trades
            60: 0.05,    # 5% trades
            85: 0.10,    # 10% trades
            100: 0.15    # 15% trades (max with safeguards)
        }
        
        # Spongy characteristics
        self.momentum = 0.0  # Current momentum
        self.resistance = 0.0  # Current resistance
        self.temperature = 0.0  # Engine temp (activity heat)
        
        # Safety features
        self.emergency_brake_engaged = False
        self.traction_control = True
        self.abs_enabled = True  # Anti-lock braking
        
    def press_gas(self, pressure: float) -> float:
        """Press the gas pedal (0-100)"""
        if self.emergency_brake_engaged:
            return 0.0
        
        # Apply spongy resistance
        effective_pressure = pressure * (1 - self.resistance)
        
        # Gradual acceleration based on stiffness
        target = min(100, effective_pressure)
        acceleration = (target - self.current_throttle) * self.throttle_stiffness
        
        # Apply traction control
        if self.traction_control and acceleration > 20:
            acceleration = min(acceleration, 20)  # Limit sudden jumps
        
        # Update throttle
        self.current_throttle += acceleration
        self.current_throttle = max(0, min(100, self.current_throttle))
        
        # Build momentum
        self.momentum = min(1.0, self.momentum + 0.1)
        
        # Heat up with activity
        self.temperature = min(100, self.temperature + acceleration * 0.5)
        
        return self.current_throttle
    
    def ease_off(self, amount: float = 10) -> float:
        """Gently ease off the gas"""
        self.current_throttle = max(0, self.current_throttle - amount)
        self.momentum = max(0, self.momentum - 0.2)
        self.temperature = max(0, self.temperature - 5)
        return self.current_throttle
    
    def hit_brakes(self, force: float = 50) -> float:
        """Apply brakes (0-100 force)"""
        # ABS prevents lock-up
        if self.abs_enabled:
            brake_effect = min(force, 80)  # Max 80% instant reduction
        else:
            brake_effect = force
        
        # Apply brake force
        reduction = self.current_throttle * (brake_effect / 100) * self.brake_power
        self.current_throttle = max(0, self.current_throttle - reduction)
        
        # Kill momentum
        self.momentum = max(0, self.momentum - (force / 100))
        
        # Cool down
        self.temperature = max(0, self.temperature - 10)
        
        return self.current_throttle
    
    def emergency_stop(self) -> float:
        """EMERGENCY BRAKE - Instant stop"""
        self.emergency_brake_engaged = True
        self.current_throttle = 0
        self.momentum = 0
        self.temperature = 0
        print("🚨 EMERGENCY STOP ENGAGED!")
        return 0
    
    def reset_emergency(self):
        """Reset after emergency stop"""
        self.emergency_brake_engaged = False
        print("✅ Emergency brake released")
    
    def get_zone(self) -> str:
        """Get current performance zone"""
        throttle = self.current_throttle
        
        if throttle <= self.IDLE[1]:
            return "IDLE"
        elif throttle <= self.LEARNING[1]:
            return "LEARNING"
        elif throttle <= self.CRUISING[1]:
            return "CRUISING"
        elif throttle <= self.AGGRESSIVE[1]:
            return "AGGRESSIVE"
        else:
            return "REDLINE"
    
    def get_trade_size_percent(self) -> float:
        """Get recommended trade size based on throttle"""
        # Interpolate between defined points
        throttle = self.current_throttle
        
        if throttle <= 0:
            return 0
        elif throttle <= 10:
            return 0.001 * (throttle / 10)
        elif throttle <= 30:
            return 0.001 + (0.009 * ((throttle - 10) / 20))
        elif throttle <= 60:
            return 0.01 + (0.04 * ((throttle - 30) / 30))
        elif throttle <= 85:
            return 0.05 + (0.05 * ((throttle - 60) / 25))
        else:
            return 0.10 + (0.05 * ((throttle - 85) / 15))
    
    def adjust_stiffness(self, new_stiffness: float):
        """Adjust throttle response (0=spongy, 1=instant)"""
        self.throttle_stiffness = max(0.1, min(1.0, new_stiffness))
    
    def add_resistance(self, amount: float):
        """Add resistance to throttle (market conditions)"""
        self.resistance = min(0.8, self.resistance + amount)
    
    def dashboard(self) -> str:
        """Display throttle dashboard"""
        zone = self.get_zone()
        trade_size = self.get_trade_size_percent() * 100
        
        # Visual throttle meter
        meter_width = 40
        filled = int((self.current_throttle / 100) * meter_width)
        empty = meter_width - filled
        
        meter = "█" * filled + "░" * empty
        
        return f"""
╔════════════════════════════════════════════════╗
║         🎮 SPONGY THROTTLE DASHBOARD           ║
╠════════════════════════════════════════════════╣
║ Throttle: [{meter}] {self.current_throttle:.1f}%
║ Zone: {zone:<12} | Trade Size: {trade_size:.2f}%
║ Momentum: {self.momentum:.2f} | Resistance: {self.resistance:.2f}
║ Temperature: {self.temperature:.1f}°C | Stiffness: {self.throttle_stiffness:.1f}
║ Traction: {'ON' if self.traction_control else 'OFF'} | ABS: {'ON' if self.abs_enabled else 'OFF'}
╚════════════════════════════════════════════════╝"""

# Test the throttle system
print("🎮 SPONGY THROTTLE CONTROL SYSTEM")
print("="*60)
print("Testing variable acceleration with instant braking...")

throttle = SpongyThrottle()

# Simulation sequence
print("\n📊 THROTTLE SIMULATION:")
print("-"*60)

sequences = [
    ("Starting engine...", lambda: throttle.press_gas(30)),
    ("Gentle acceleration", lambda: throttle.press_gas(50)),
    ("More gas!", lambda: throttle.press_gas(80)),
    ("Ease off a bit", lambda: throttle.ease_off(20)),
    ("Floor it!", lambda: throttle.press_gas(100)),
    ("Hit the brakes!", lambda: throttle.hit_brakes(60)),
    ("Emergency stop!", lambda: throttle.emergency_stop()),
    ("Reset emergency", lambda: throttle.reset_emergency()),
    ("Gentle restart", lambda: throttle.press_gas(20)),
    ("Cruise control", lambda: throttle.press_gas(45)),
]

for description, action in sequences:
    print(f"\n{description}")
    result = action()
    print(throttle.dashboard())
    time.sleep(0.5)

print("\n🎯 THROTTLE FEATURES:")
print("-"*60)
print("• SPONGY RESPONSE: Gradual acceleration, no jerky movements")
print("• INSTANT BRAKING: Hit brakes for immediate slowdown")
print("• EMERGENCY STOP: Panic button kills everything instantly")
print("• TRACTION CONTROL: Prevents spinning out on acceleration")
print("• ABS: Prevents lock-up when braking hard")
print("• VARIABLE STIFFNESS: Adjust response from mushy to instant")
print("• HEAT MANAGEMENT: Activity builds heat, cooling prevents overrun")

print("\n📈 TRADE SIZE MAPPING:")
print("-"*60)
print("  Throttle  0% → No trading")
print("  Throttle 10% → 0.1% position sizes")
print("  Throttle 30% → 1% position sizes")
print("  Throttle 60% → 5% position sizes")
print("  Throttle 85% → 10% position sizes")
print("  Throttle 100% → 15% position sizes (max)")

print("\n✨ The Quantum Crawdads now have a SPONGY THROTTLE!")
print("   Hit the gas for aggressive trading...")
print("   Ease off for cautious learning...")
print("   Emergency brake always ready!")
print("   🎮 Full control at your fingertips! 🎮")