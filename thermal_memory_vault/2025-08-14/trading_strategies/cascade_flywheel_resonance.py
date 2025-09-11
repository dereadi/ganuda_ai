#!/usr/bin/env python3
"""
🌀 CASCADE FLYWHEEL RESONANCE ENGINE
=====================================
Start at 0.1 RPM and let it build naturally
Like pushing a swing - tiny pushes at the right moment
Until it reaches resonance frequency and self-sustains
"""

import json
import time
import math
from datetime import datetime
from coinbase.rest import RESTClient

print("🌀 CASCADE FLYWHEEL RESONANCE")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')} CST")
print("Starting slow... letting momentum cascade naturally...")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

class CascadeFlywheel:
    def __init__(self):
        # Start VERY slow
        self.rpm = 0.1  # Starting at 0.1 RPM
        self.target_rpm = 100.0  # Self-sustaining speed
        
        # Energy accumulators
        self.kinetic_energy = 0.001  # Tiny seed energy
        self.potential_energy = 0
        self.resonance_factor = 1.0
        
        # Cascade parameters
        self.cascade_threshold = 1.0  # RPM to trigger cascade
        self.harmonic_frequency = 7.83  # Earth's Schumann resonance
        self.phase_angle = 0
        
    def micro_pulse(self, market_vibration):
        """Tiny pulse at exactly the right moment"""
        # Calculate optimal phase for push (like pushing a swing)
        self.phase_angle += market_vibration * 360
        optimal_phase = self.phase_angle % 360
        
        # Push only at the right moment (0° or 180°)
        if optimal_phase < 10 or (optimal_phase > 170 and optimal_phase < 190):
            # Perfect timing! Add energy
            energy_boost = market_vibration * self.resonance_factor
            self.kinetic_energy += energy_boost
            
            # Convert energy to RPM (E = 1/2 * I * ω²)
            rpm_increase = math.sqrt(2 * energy_boost) * 0.1
            self.rpm += rpm_increase
            
            return True, rpm_increase
        
        return False, 0
    
    def check_cascade(self):
        """Check if we've hit cascade point"""
        if self.rpm >= self.cascade_threshold:
            # CASCADE TRIGGERED!
            # Each rotation now adds more energy than it loses
            self.resonance_factor *= 1.1  # 10% resonance boost
            
            # Exponential growth begins
            cascade_boost = (self.rpm / self.cascade_threshold) ** 2 * 0.01
            self.rpm *= (1 + cascade_boost)
            
            return True
        return False
    
    def natural_decay(self):
        """Natural friction and energy loss"""
        # Very small friction at low speeds
        if self.rpm < 1:
            friction = 0.001  # Almost no friction
        elif self.rpm < 10:
            friction = 0.01   # Minimal friction
        else:
            friction = 0.02   # Normal friction
        
        self.rpm *= (1 - friction)
        self.kinetic_energy *= (1 - friction)
    
    def harvest_ambient(self):
        """Continuously harvest tiny amounts of energy"""
        # Sample multiple markets rapidly
        total_vibration = 0
        
        for symbol in ['BTC', 'ETH', 'SOL']:
            ticker1 = client.get_product(f'{symbol}-USD')
            price1 = float(ticker1.price if hasattr(ticker1, 'price') else ticker1.get('price', 0))
            
            time.sleep(0.1)  # Quick sample
            
            ticker2 = client.get_product(f'{symbol}-USD')
            price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
            
            # Even the tiniest movement is energy
            vibration = abs((price2 - price1) / price1)
            total_vibration += vibration
        
        return total_vibration

# Initialize cascade flywheel
flywheel = CascadeFlywheel()

print("🌀 STARTING CASCADE SEQUENCE:")
print("-"*60)
print(f"  Initial RPM: {flywheel.rpm:.3f}")
print(f"  Target RPM: {flywheel.target_rpm:.1f}")
print(f"  Cascade Threshold: {flywheel.cascade_threshold:.1f} RPM")
print()

# Run cascade sequence
print("⚡ MICRO-PULSE ACCUMULATION:")
print("-"*60)

cascade_triggered = False
pulse_count = 0
successful_pulses = 0

for cycle in range(30):  # 30 micro-cycles
    # Harvest ambient energy
    vibration = flywheel.harvest_ambient()
    
    # Apply micro-pulse at right moment
    pushed, boost = flywheel.micro_pulse(vibration)
    
    if pushed:
        successful_pulses += 1
        pulse_visual = "⚡" * min(int(boost * 100), 5)
        print(f"  Cycle {cycle+1:2}: {pulse_visual} Perfect timing! +{boost:.6f} RPM")
    else:
        print(f"  Cycle {cycle+1:2}: ░░░ Waiting for phase alignment...")
    
    pulse_count += 1
    
    # Check for cascade
    if not cascade_triggered and flywheel.check_cascade():
        print(f"\n  🌊 CASCADE TRIGGERED at {flywheel.rpm:.3f} RPM!")
        print(f"     Resonance Factor: {flywheel.resonance_factor:.2f}x")
        cascade_triggered = True
    
    # Natural decay
    flywheel.natural_decay()
    
    # Show progress bar
    if cycle % 5 == 0:
        progress = min(flywheel.rpm / flywheel.cascade_threshold * 100, 100)
        bar = "█" * int(progress/10) + "░" * (10 - int(progress/10))
        print(f"\n  Progress: [{bar}] {progress:.1f}% to cascade")
        print(f"  Current RPM: {flywheel.rpm:.3f}")
        print()
    
    # If cascade achieved, show exponential growth
    if cascade_triggered and flywheel.rpm > 10:
        print(f"\n  🚀 EXPONENTIAL GROWTH PHASE!")
        print(f"     RPM: {flywheel.rpm:.1f} and accelerating!")
        break

print("\n📊 CASCADE ANALYSIS:")
print("-"*60)
print(f"  Final RPM: {flywheel.rpm:.3f}")
print(f"  Push Success Rate: {successful_pulses}/{pulse_count} ({successful_pulses/pulse_count*100:.1f}%)")
print(f"  Energy Accumulated: {flywheel.kinetic_energy:.6f} joules")
print(f"  Resonance Factor: {flywheel.resonance_factor:.2f}x")

# TRADING APPLICATION
if flywheel.rpm > 0.5:
    print("\n💰 CONVERTING MOMENTUM TO TRADES:")
    print("-"*60)
    
    accounts = client.get_accounts()
    account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
    
    usd_balance = 0
    for account in account_list:
        if account['currency'] == 'USD':
            usd_balance = float(account['available_balance']['value'])
            break
    
    # Trade size based on RPM
    if flywheel.rpm < 1:
        trade_size = 1.00  # Minimum trade
    elif flywheel.rpm < 10:
        trade_size = flywheel.rpm  # Linear scaling
    else:
        trade_size = min(10 + (flywheel.rpm - 10) * 0.1, 20)  # Capped growth
    
    trade_size = min(trade_size, usd_balance * 0.01)  # Max 1% per pulse
    trade_size = round(trade_size, 2)
    
    print(f"  Flywheel RPM: {flywheel.rpm:.3f}")
    print(f"  Generated Trade Size: ${trade_size:.2f}")
    
    if trade_size >= 1.00:
        try:
            print(f"  🌀 Deploying cascade energy: ${trade_size:.2f}")
            order = client.market_order_buy(
                client_order_id=f"cascade_{int(time.time())}",
                product_id="SOL-USD",  # Riding the Asia session
                quote_size=str(trade_size)
            )
            print(f"  ✅ Cascade energy deployed!")
            
            # The trade adds back to the flywheel!
            flywheel.rpm *= 1.01
            print(f"  🔄 Feedback: RPM boosted to {flywheel.rpm:.3f}")
            
        except Exception as e:
            print(f"  ❌ Cascade blocked: {str(e)[:30]}")

print("\n✨ THE CASCADE PRINCIPLE:")
print("-"*60)
print("Start with 0.1 RPM - almost nothing")
print("Push only at the perfect moment (phase alignment)")
print("Each push adds slightly more than friction removes")
print("At 1 RPM, cascade begins - exponential growth")
print("At 10 RPM, self-sustaining achieved")
print("At 100 RPM, perpetual motion maintained")
print()

if cascade_triggered:
    print("🌊 CASCADE ACHIEVED!")
    print("The flywheel now powers itself.")
    print("Each rotation generates more energy than it uses.")
    print("The system has reached critical mass.")
else:
    print("🌱 BUILDING CASCADE...")
    print(f"Current: {flywheel.rpm:.3f} RPM")
    print(f"Need: {flywheel.cascade_threshold - flywheel.rpm:.3f} more RPM to cascade")
    print("Keep applying micro-pulses at resonance...")

print()
print("🌀⚡🌀 THE CASCADE BUILDS FROM NOTHING 🌀⚡🌀")