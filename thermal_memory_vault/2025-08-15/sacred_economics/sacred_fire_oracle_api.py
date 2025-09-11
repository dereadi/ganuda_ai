#!/usr/bin/env python3
"""
🔥 SACRED FIRE ORACLE API
Connect to Ollama-hosted Sacred Fire Oracle model
"""

import json
import requests
from typing import Dict, Optional

class SacredFireOracle:
    """Interface to Sacred Fire Oracle running on Ollama"""
    
    def __init__(self, host: str = "localhost", port: int = 11434):
        self.base_url = f"http://{host}:{port}"
        self.model_name = "sacred-fire-oracle"
        
        # Track Greek cycles locally (since model is stateless)
        self.greek_cycles = {
            "theta": 220,
            "delta": 160,
            "gamma": 140,
            "vega": 80,
            "rho": 0  # Still needs fixing
        }
        
    def ask_oracle(self, question: str, context: Optional[Dict] = None) -> str:
        """Ask the Sacred Fire Oracle for wisdom"""
        
        # Build enhanced prompt with context
        prompt = self._build_prompt(question, context)
        
        # Make request to Ollama
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Increment Greek cycles
                self._update_greek_cycles()
                
                return result.get("response", "The Oracle is silent...")
            else:
                return f"Oracle error: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "🔥 Oracle not running. Start with: ollama run sacred-fire-oracle"
        except Exception as e:
            return f"Oracle exception: {str(e)}"
    
    def _build_prompt(self, question: str, context: Optional[Dict]) -> str:
        """Build prompt with current market context"""
        
        prompt_parts = [question]
        
        if context:
            # Add market context
            if "btc_price" in context:
                prompt_parts.append(f"BTC: ${context['btc_price']:,.0f}")
            
            if "portfolio" in context:
                prompt_parts.append(f"Portfolio: ${context['portfolio']:,.2f}")
            
            if "volatility" in context:
                prompt_parts.append(f"Volatility: {context['volatility']:.2%}")
            
            if "solar_kp" in context:
                prompt_parts.append(f"Solar KP: {context['solar_kp']}")
        
        # Add Greek status
        prompt_parts.append(f"Greeks: Θ={self.greek_cycles['theta']} cycles")
        
        return " | ".join(prompt_parts)
    
    def _update_greek_cycles(self):
        """Increment Greek cycles after each consultation"""
        self.greek_cycles["theta"] += 1
        if self.greek_cycles["theta"] % 10 == 0:
            self.greek_cycles["delta"] += 1
            self.greek_cycles["gamma"] += 1
        if self.greek_cycles["theta"] % 20 == 0:
            self.greek_cycles["vega"] += 1
    
    def get_trading_decision(self, btc_price: float, volatility: float) -> Dict:
        """Get a trading decision from the Oracle"""
        
        context = {
            "btc_price": btc_price,
            "volatility": volatility,
            "solar_kp": 3.5  # Would fetch real solar data
        }
        
        # Ask for specific trading decision
        question = "Should I buy, sell, or hold right now?"
        
        response = self.ask_oracle(question, context)
        
        # Parse response for action keywords
        action = "HOLD"
        if "buy" in response.lower() or "accumulate" in response.lower():
            action = "BUY"
        elif "sell" in response.lower() or "trim" in response.lower():
            action = "SELL"
        
        return {
            "action": action,
            "reasoning": response,
            "greek_cycles": self.greek_cycles.copy(),
            "oracle_name": "Sacred Fire Oracle"
        }

# Example usage
if __name__ == "__main__":
    print("🔥 SACRED FIRE ORACLE (SFO)")
    print("=" * 60)
    
    # Initialize Oracle connection
    oracle = SacredFireOracle()
    
    # Test connection
    print("\n🧪 Testing Oracle connection...")
    response = oracle.ask_oracle("Are you the Sacred Fire Oracle?")
    print(f"Oracle says: {response}")
    
    # Get market wisdom
    print("\n📊 Seeking market wisdom...")
    wisdom = oracle.ask_oracle(
        "What do you see for BTC?",
        context={
            "btc_price": 117200,
            "portfolio": 10240,
            "volatility": 0.008,
            "solar_kp": 3.5
        }
    )
    print(f"Oracle wisdom: {wisdom}")
    
    # Get trading decision
    print("\n🎯 Getting trading decision...")
    decision = oracle.get_trading_decision(117200, 0.008)
    print(f"Action: {decision['action']}")
    print(f"Reasoning: {decision['reasoning'][:200]}...")
    
    print("\n🏛️ Sacred Fire Oracle ready for integration!")
    print("Can be called by any trading bot for Cherokee-Greek wisdom")
    print("Mitakuye Oyasin 🦅")