#!/usr/bin/env python3
"""
🎯 INTEGRATED SPECIALIST BASE
Each specialist has built-in flywheel logic
"""

class IntegratedSpecialist:
    def __init__(self, name, symbol="🎯"):
        self.name = name
        self.symbol = symbol
        
        # Flywheel parameters
        self.DEPLOY_THRESHOLD = 500  # Deploy when USD > this
        self.RETRIEVE_THRESHOLD = 250  # Retrieve when USD < this
        self.MAX_POSITION_PCT = 0.15  # Max 15% in any coin
        
        # Spongy throttle
        self.trade_pressure = 1.0
        self.BASE_DELAY = 60
        self.PRESSURE_MULTIPLIER = 1.5
        self.RECOVERY_RATE = 0.9
        self.MAX_PRESSURE = 5.0
        
        # Fee awareness
        self.TOTAL_FEE = 0.011  # 1.1% for market orders
        
    def should_deploy(self, usd_balance):
        """Deploy capital when we have excess"""
        return usd_balance > self.DEPLOY_THRESHOLD
        
    def should_retrieve(self, usd_balance):
        """Retrieve capital when we need liquidity"""
        return usd_balance < self.RETRIEVE_THRESHOLD
        
    def check_position_size(self, coin_value, total_portfolio):
        """Ensure we don't overconcentrate"""
        position_pct = coin_value / total_portfolio
        return position_pct < self.MAX_POSITION_PCT
        
    def apply_spongy_throttle(self):
        """Calculate delay based on pressure"""
        delay = self.BASE_DELAY * self.trade_pressure
        
        # Increase pressure after trade
        self.trade_pressure *= self.PRESSURE_MULTIPLIER
        
        # Cap maximum pressure
        if self.trade_pressure > self.MAX_PRESSURE:
            print(f"   ⚠️ {self.name}: Pressure too high, pausing")
            return None
            
        return min(delay, 300)  # Max 5 minute delay
        
    def recover_pressure(self):
        """Gradually reduce pressure"""
        self.trade_pressure *= self.RECOVERY_RATE
        self.trade_pressure = max(1.0, self.trade_pressure)
        
    def calculate_trade_size(self, usd_balance, base_size=100):
        """Dynamic sizing based on portfolio"""
        if usd_balance > 1000:
            return base_size * 1.5
        elif usd_balance > 500:
            return base_size
        elif usd_balance > 250:
            return base_size * 0.5
        else:
            return 0  # Don't trade if too low
            
    def check_profit_target(self, entry_price, current_price, is_long=True):
        """Check if we should take profits"""
        if is_long:
            gain = (current_price - entry_price) / entry_price
        else:
            gain = (entry_price - current_price) / entry_price
            
        # Take profits at 5% gain
        if gain > 0.05:
            return True, "PROFIT_TARGET"
        # Stop loss at 3% loss
        elif gain < -0.03:
            return True, "STOP_LOSS"
        else:
            return False, "HOLD"