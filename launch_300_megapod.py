#!/usr/bin/env python3
"""
🦀🔥 $300 COINBASE QUANTUM CRAWDAD MEGAPOD
==========================================
Adjusted for your $300 deposit
"""

print("🦀🔥 LAUNCHING $300 QUANTUM CRAWDAD MEGAPOD")
print("="*50)
print("💰 Capital: $300")
print("🦀 7 Crawdads: $42.86 each")
print("🎯 Target: $12/day (4% return)")
print("="*50)
print()

# Configuration for $300
config = {
    "capital": 300.0,
    "crawdads": 7,
    "per_crawdad": 300.0 / 7,  # $42.86 each
    "trade_sizes": {
        "micro": 3.00,   # 1% of capital
        "small": 6.00,   # 2% of capital  
        "medium": 15.00, # 5% of capital
        "large": 30.00,  # 10% of capital
        "mega": 45.00    # 15% of capital (Sacred Fire moments)
    },
    "daily_target": 12.00,  # $12/day (4%)
    "stop_loss": 6.00,      # $6 per trade
    "daily_limit": 15.00,   # $15 max daily loss
    "sacred_reserve": 180.00 # Keep $180 safe (60%)
}

print("📊 POSITION SIZING:")
for size, amount in config["trade_sizes"].items():
    print(f"  {size:6}: ${amount:.2f}")
print()

print("🛡️ RISK MANAGEMENT:")
print(f"  Stop loss: ${config['stop_loss']:.2f}/trade")
print(f"  Daily limit: ${config['daily_limit']:.2f}")
print(f"  Sacred reserve: ${config['sacred_reserve']:.2f}")
print()

print("🚀 Starting megapod with $300...")
print()

# Run the actual megapod
import os
os.system("source quantum_crawdad_env/bin/activate && python3 coinbase_quantum_megapod.py")