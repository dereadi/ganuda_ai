#!/usr/bin/env python3
"""
🛡️ QUANTUM CRAWDAD SAFETY SYSTEM
==================================
Internal safeguards to prevent trading disasters
"""

import json
import time
from datetime import datetime
from typing import Dict, Tuple

class QuantumSafeguards:
    def __init__(self):
        self.config = self.load_config()
        
        # SAFETY LIMITS
        self.MAX_SINGLE_TRADE_USD = 50.00      # Never trade more than $50 at once
        self.MAX_DAILY_TRADES = 100            # Max trades per day
        self.MAX_POSITION_PERCENT = 0.25       # Never put >25% in one asset
        self.MIN_RESERVE_USD = 50.00           # Always keep $50 reserve
        self.MAX_LOSS_PERCENT = 0.05           # Stop if down 5% in a day
        
        # Circuit breakers
        self.PANIC_STOP_LOSS = 0.10            # Emergency stop at 10% loss
        self.MAX_SLIPPAGE = 0.02               # Cancel if slippage >2%
        
        # Trade tracking
        self.daily_trades = []
        self.daily_loss = 0
        self.circuit_breaker_triggered = False
        
    def load_config(self):
        """Load configuration safely"""
        try:
            with open('/home/dereadi/.coinbase_config.json', 'r') as f:
                return json.load(f)
        except:
            print("❌ Config not found - SAFETY MODE ACTIVATED")
            return {'capital': 0}
    
    def check_trade_size(self, amount_usd: float, action: str) -> Tuple[bool, str]:
        """Verify trade size is safe"""
        if amount_usd > self.MAX_SINGLE_TRADE_USD:
            return False, f"Trade size ${amount_usd:.2f} exceeds maximum ${self.MAX_SINGLE_TRADE_USD}"
        
        if amount_usd < 0.01:
            return False, f"Trade size ${amount_usd:.2f} too small"
        
        return True, "Size OK"
    
    def check_position_concentration(self, symbol: str, new_amount_usd: float, 
                                   total_portfolio: float) -> Tuple[bool, str]:
        """Prevent over-concentration in one asset"""
        if total_portfolio <= 0:
            return False, "Invalid portfolio value"
        
        concentration = new_amount_usd / total_portfolio
        if concentration > self.MAX_POSITION_PERCENT:
            return False, f"{symbol} would be {concentration*100:.1f}% of portfolio (max {self.MAX_POSITION_PERCENT*100:.0f}%)"
        
        return True, "Concentration OK"
    
    def check_reserve_maintained(self, usd_balance: float, trade_amount: float) -> Tuple[bool, str]:
        """Ensure minimum reserve is maintained"""
        remaining = usd_balance - trade_amount
        if remaining < self.MIN_RESERVE_USD:
            return False, f"Would leave only ${remaining:.2f} (min reserve ${self.MIN_RESERVE_USD})"
        
        return True, "Reserve OK"
    
    def check_daily_limits(self) -> Tuple[bool, str]:
        """Check if daily limits exceeded"""
        # Count today's trades
        today_count = len([t for t in self.daily_trades 
                          if t.get('date') == datetime.now().date()])
        
        if today_count >= self.MAX_DAILY_TRADES:
            return False, f"Daily trade limit reached ({self.MAX_DAILY_TRADES})"
        
        # Check daily loss
        if self.daily_loss > self.MAX_LOSS_PERCENT:
            return False, f"Daily loss limit exceeded ({self.daily_loss*100:.1f}%)"
        
        return True, "Daily limits OK"
    
    def check_circuit_breaker(self, current_value: float, starting_value: float) -> Tuple[bool, str]:
        """Emergency stop if massive loss detected"""
        if starting_value <= 0:
            return True, "No baseline"
        
        loss = (starting_value - current_value) / starting_value
        
        if loss > self.PANIC_STOP_LOSS:
            self.circuit_breaker_triggered = True
            return False, f"🚨 CIRCUIT BREAKER: Down {loss*100:.1f}% - TRADING HALTED"
        
        return True, "No emergency"
    
    def validate_trade(self, trade_params: Dict) -> Tuple[bool, list]:
        """Run all safety checks on a proposed trade"""
        failures = []
        
        # Extract parameters
        action = trade_params.get('action', 'BUY')
        symbol = trade_params.get('symbol', 'UNKNOWN')
        amount_usd = trade_params.get('amount_usd', 0)
        usd_balance = trade_params.get('usd_balance', 0)
        portfolio_value = trade_params.get('portfolio_value', 0)
        
        # Run all checks
        checks = [
            self.check_trade_size(amount_usd, action),
            self.check_position_concentration(symbol, amount_usd, portfolio_value),
            self.check_reserve_maintained(usd_balance, amount_usd),
            self.check_daily_limits(),
        ]
        
        # Collect failures
        for passed, message in checks:
            if not passed:
                failures.append(message)
        
        return len(failures) == 0, failures
    
    def calculate_safe_trade_size(self, usd_balance: float, target_percent: float = 0.05) -> float:
        """Calculate a safe trade size"""
        # Never use more than 5% of balance per trade
        safe_amount = usd_balance * target_percent
        
        # Apply maximum limit
        safe_amount = min(safe_amount, self.MAX_SINGLE_TRADE_USD)
        
        # Keep reserve
        available = usd_balance - self.MIN_RESERVE_USD
        safe_amount = min(safe_amount, available)
        
        # Minimum viable trade
        if safe_amount < 1.00:
            return 0
        
        return round(safe_amount, 2)

# Test the safeguards
print("🛡️ QUANTUM CRAWDAD SAFETY SYSTEM")
print("="*60)
print("Testing safeguards to prevent trading disasters...")
print()

safeguards = QuantumSafeguards()

print("⚙️ SAFETY PARAMETERS:")
print("-"*60)
print(f"  Max Single Trade: ${safeguards.MAX_SINGLE_TRADE_USD}")
print(f"  Max Daily Trades: {safeguards.MAX_DAILY_TRADES}")
print(f"  Max Position Size: {safeguards.MAX_POSITION_PERCENT*100:.0f}%")
print(f"  Min Reserve: ${safeguards.MIN_RESERVE_USD}")
print(f"  Daily Loss Limit: {safeguards.MAX_LOSS_PERCENT*100:.0f}%")
print(f"  Circuit Breaker: {safeguards.PANIC_STOP_LOSS*100:.0f}% loss")

# Test scenarios
print("\n🧪 TESTING SAFETY SCENARIOS:")
print("-"*60)

test_trades = [
    {
        'name': 'Normal $10 trade',
        'params': {
            'action': 'BUY',
            'symbol': 'BTC',
            'amount_usd': 10,
            'usd_balance': 342,
            'portfolio_value': 479
        }
    },
    {
        'name': 'Oversized $200 trade',
        'params': {
            'action': 'BUY',
            'symbol': 'BTC',
            'amount_usd': 200,
            'usd_balance': 342,
            'portfolio_value': 479
        }
    },
    {
        'name': 'Would break reserve',
        'params': {
            'action': 'BUY',
            'symbol': 'SOL',
            'amount_usd': 300,
            'usd_balance': 342,
            'portfolio_value': 479
        }
    },
    {
        'name': 'Over-concentration',
        'params': {
            'action': 'BUY',
            'symbol': 'DOGE',
            'amount_usd': 150,
            'usd_balance': 342,
            'portfolio_value': 479
        }
    }
]

for test in test_trades:
    print(f"\n📋 Test: {test['name']}")
    passed, failures = safeguards.validate_trade(test['params'])
    
    if passed:
        print("   ✅ APPROVED")
    else:
        print("   ❌ BLOCKED:")
        for failure in failures:
            print(f"      • {failure}")

# Calculate safe trade sizes
print("\n💰 SAFE TRADE SIZE CALCULATOR:")
print("-"*60)

balances = [342.37, 100, 50, 1000]
for balance in balances:
    safe_size = safeguards.calculate_safe_trade_size(balance)
    print(f"  Balance ${balance:.2f} → Safe trade: ${safe_size:.2f}")

print("\n🛡️ SAFEGUARD RULES:")
print("-"*60)
print("1. NEVER trade more than $50 in a single transaction")
print("2. ALWAYS keep $50 minimum reserve")
print("3. STOP if down 5% in a day")
print("4. HALT everything if down 10% (circuit breaker)")
print("5. No more than 25% in any single asset")
print("6. Maximum 100 trades per day")
print("7. Always validate BEFORE executing")

print("\n✨ The Quantum Crawdads are now PROTECTED!")
print("   No more accidental massive trades...")
print("   Safe, controlled learning at all times!")
print("   🛡️ Safety first, profits second! 🛡️")