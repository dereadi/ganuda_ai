#!/usr/bin/env python3
"""
Circuit Breaker - Council Mandated Safety
Max $500 loss per container per day
"""

import json
import os
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, max_daily_loss=500):
        self.max_daily_loss = max_daily_loss
        self.losses_today = 0
        self.last_reset = datetime.now()
        self.tripped = False
        
    def check_loss(self, amount):
        """Check if trade would exceed daily loss limit"""
        # Reset daily counter if new day
        if datetime.now().date() > self.last_reset.date():
            self.losses_today = 0
            self.last_reset = datetime.now()
            self.tripped = False
            
        if amount < 0:  # It's a loss
            if abs(amount) + self.losses_today > self.max_daily_loss:
                self.tripped = True
                return False  # Block trade
            self.losses_today += abs(amount)
            
        return True  # Allow trade
        
    def is_tripped(self):
        return self.tripped
