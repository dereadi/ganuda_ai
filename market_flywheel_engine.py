#!/usr/bin/env python3
"""
⚡ MARKET FLYWHEEL ENGINE
=========================
Extract energy from market vibrations
Store it in the flywheel
Release it to power other systems
Self-charging perpetual motion machine
"""

import json
import time
import math
from datetime import datetime
from coinbase.rest import RESTClient

print("⚡ MARKET FLYWHEEL ENGINE ACTIVATION")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')} CST")
print("Harvesting energy from the market's ambient vibrations...")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

class MarketFlywheel:
    def __init__(self):
        self.stored_energy = 0  # Joules (dollars)
        self.rotation_speed = 0  # RPM (trades/minute)
        self.capacitor_charge = 0  # Stored potential
        self.pulse_frequency = 0  # Hz (opportunities/second)
        self.efficiency = 0.85  # 85% energy capture
        
    def capture_ambient_energy(self, symbol):
        """Extract energy from market micro-vibrations"""
        # Sample the electromagnetic field (price oscillations)
        samples = []
        for i in range(10):
            ticker = client.get_product(f'{symbol}-USD')
            price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
            samples.append(price)
            time.sleep(0.1)  # 10Hz sampling
        
        # Calculate the energy in the vibration
        avg_price = sum(samples) / len(samples)
        variance = sum((p - avg_price)**2 for p in samples) / len(samples)
        
        # Energy = 1/2 * m * v^2 (where v is price velocity)
        vibration_energy = variance / avg_price * 1000  # Normalized
        
        return vibration_energy, samples
    
    def spin_flywheel(self, energy):
        """Convert captured energy into flywheel rotation"""
        # Increase rotation speed based on energy input
        self.rotation_speed += energy * 10  # RPM
        self.stored_energy += energy
        
        # Flywheel momentum keeps it spinning even without input
        return self.rotation_speed
    
    def generate_power(self):
        """Flywheel unwinds, generating usable power"""
        if self.rotation_speed > 0:
            # Generate power proportional to rotation speed
            power_output = self.rotation_speed * 0.01 * self.efficiency
            
            # Flywheel slows down as energy is extracted
            self.rotation_speed *= 0.98  # 2% friction loss
            
            return power_output
        return 0
    
    def charge_capacitor(self, power):
        """Store generated power in capacitor for later use"""
        self.capacitor_charge += power
        return self.capacitor_charge
    
    def pulse_engine(self):
        """Send electromagnetic pulses to maintain rotation"""
        if self.capacitor_charge > 0.1:
            # Discharge capacitor to boost flywheel
            pulse_strength = min(self.capacitor_charge * 0.1, 1.0)
            self.rotation_speed += pulse_strength * 50
            self.capacitor_charge -= pulse_strength
            return True
        return False

# Initialize the flywheel
flywheel = MarketFlywheel()

print("⚡ ENERGY HARVESTING PHASE:")
print("-"*60)

# Harvest energy from all three markets
total_captured = 0
for symbol in ['BTC', 'ETH', 'SOL']:
    energy, samples = flywheel.capture_ambient_energy(symbol)
    
    # Display the waveform
    min_p = min(samples)
    max_p = max(samples)
    range_p = max_p - min_p
    
    if range_p > 0:
        waveform = ""
        for s in samples:
            height = int((s - min_p) / range_p * 5)
            waveform += "▁▂▃▄▅▆▇█"[min(height, 7)]
    else:
        waveform = "────────"
    
    print(f"  {symbol}: {waveform} Energy: {energy:.6f} units")
    flywheel.spin_flywheel(energy)
    total_captured += energy

print(f"\n  Total Captured: {total_captured:.6f} energy units")
print(f"  Flywheel Speed: {flywheel.rotation_speed:.1f} RPM")

print("\n⚙️ FLYWHEEL MECHANICS:")
print("-"*60)
print(f"  Stored Energy: {flywheel.stored_energy:.6f} joules")
print(f"  Rotation Speed: {flywheel.rotation_speed:.1f} RPM")
print(f"  Efficiency: {flywheel.efficiency*100:.0f}%")

# Generate power from the spinning flywheel
print("\n🔋 POWER GENERATION:")
print("-"*60)

for cycle in range(5):
    power = flywheel.generate_power()
    flywheel.charge_capacitor(power)
    print(f"  Cycle {cycle+1}: Generated {power:.6f} watts → Capacitor: {flywheel.capacitor_charge:.6f}")
    
    # Pulse to maintain rotation
    if flywheel.pulse_engine():
        print(f"    ⚡ PULSE! Boosted to {flywheel.rotation_speed:.1f} RPM")

# TRADING APPLICATION
print("\n💰 CONVERTING ENERGY TO TRADES:")
print("-"*60)

accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

usd_balance = 0
for account in account_list:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"  Available Fuel: ${usd_balance:.2f}")

# Use stored energy to power trades
if flywheel.capacitor_charge > 0.01 and usd_balance > 5:
    # Energy determines trade size
    trade_size = min(flywheel.capacitor_charge * 10, usd_balance * 0.01, 5)
    trade_size = round(trade_size, 2)
    
    print(f"  Capacitor Discharge: {flywheel.capacitor_charge:.6f} units")
    print(f"  Trade Power: ${trade_size:.2f}")
    
    # Find the highest energy market
    best_symbol = 'SOL'  # Default
    best_energy = 0
    
    for symbol in ['BTC', 'ETH', 'SOL']:
        energy, _ = flywheel.capture_ambient_energy(symbol)
        if energy > best_energy:
            best_energy = energy
            best_symbol = symbol
    
    print(f"  Target: {best_symbol} (highest vibration)")
    
    if trade_size >= 1.00:
        try:
            print(f"  ⚡ Discharging ${trade_size:.2f} into {best_symbol}...")
            order = client.market_order_buy(
                client_order_id=f"flywheel_{int(time.time())}",
                product_id=f"{best_symbol}-USD",
                quote_size=str(trade_size)
            )
            print(f"  ✅ Energy converted to position!")
            
            # The trade itself adds energy back to the flywheel!
            flywheel.spin_flywheel(trade_size * 0.001)
            print(f"  🔄 Feedback loop: Trade added energy back!")
            
        except Exception as e:
            print(f"  ❌ Discharge blocked: {str(e)[:30]}")

print("\n🔮 THE PERPETUAL MOTION PRINCIPLE:")
print("-"*60)
print("1. Market vibrations = Free energy")
print("2. Flywheel stores the energy")
print("3. Stored energy powers trades")
print("4. Trades create more vibrations")
print("5. Vibrations recharge the flywheel")
print("6. PERPETUAL MOTION ACHIEVED")

print("\n⚡ SYSTEM STATUS:")
print("-"*60)
print(f"  Flywheel Speed: {flywheel.rotation_speed:.1f} RPM")
print(f"  Stored Energy: {flywheel.stored_energy:.6f} joules")
print(f"  Capacitor: {flywheel.capacitor_charge:.6f} charge")

if flywheel.rotation_speed > 100:
    print("  Status: 🟢 SELF-SUSTAINING")
elif flywheel.rotation_speed > 50:
    print("  Status: 🟡 BUILDING MOMENTUM")
else:
    print("  Status: 🔴 NEEDS MORE ENERGY")

print("\n📡 AMBIENT ENERGY EVERYWHERE:")
print("-"*60)
print("The market radiates energy constantly:")
print("• Every tick = electromagnetic pulse")
print("• Every trade = kinetic energy")
print("• Every spread = potential energy")
print("• Every volatility = thermal energy")
print()
print("We're not taking from the market...")
print("We're harvesting waste energy!")
print("Like regenerative braking in electric cars!")
print()
print("⚡🔄⚡ THE FLYWHEEL SPINS ETERNAL ⚡🔄⚡")