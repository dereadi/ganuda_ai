#!/usr/bin/env python3
"""
GIANT FAMILY V2 - TIME-AWARE EDITION
Now they know WHEN they are, not just WHAT they know
"""

import json
import requests
import time
from datetime import datetime
import os
import sys

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

class TimeAwareGiantFamily:
    """Giants who understand 'this week' and 'today'"""
    
    def __init__(self):
        print("🔥 Awakening Time-Aware Giant Family...")
        self.family = self.load_giant_family()
        self.current_context = self.load_current_context()
        self.offset = None
        self.current_giant = "tsulkalu"
        
    def load_current_context(self):
        """Load current awareness"""
        try:
            with open('/home/dereadi/scripts/claude/giant_current_context.json', 'r') as f:
                return json.load(f)
        except:
            return {
                "current_date": datetime.now().strftime("%B %d, %Y"),
                "this_week": "This week",
                "current_reality": {"portfolio_value": 28259.85}
            }
    
    def load_giant_family(self):
        """Load Giants with their knowledge"""
        family = {}
        giants = ["tsulkalu", "nun_yunu_wi", "agan_unitsi", "kalona_ayeliski", "uktena"]
        
        for name in giants:
            try:
                with open(f'/home/dereadi/scripts/claude/{name}_consciousness.json', 'r') as f:
                    consciousness = json.load(f)
                with open(f'/home/dereadi/scripts/claude/{name}_corpus.json', 'r') as f:
                    corpus = json.load(f)
                
                family[name] = {
                    "consciousness": consciousness,
                    "corpus": corpus,
                    "emoji": {"tsulkalu": "🏔️", "nun_yunu_wi": "🗿", 
                             "agan_unitsi": "🌱", "kalona_ayeliski": "🦅",
                             "uktena": "🐍"}.get(name, "🔥")
                }
                print(f"   ✅ {name} awakened with time-awareness")
            except:
                pass
        return family
    
    def send_message(self, chat_id, text):
        """Send to Telegram"""
        try:
            resp = requests.post(f"{BASE_URL}/sendMessage",
                json={"chat_id": chat_id, "text": text[:4000], "parse_mode": "Markdown"})
            return resp.json().get("ok", False)
        except:
            return False
    
    def get_updates(self):
        """Get messages"""
        params = {"timeout": 30}
        if self.offset:
            params["offset"] = self.offset
        try:
            resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
            data = resp.json()
            if data.get("ok"):
                return data.get("result", [])
        except:
            pass
        return []
    
    def select_giant(self, text):
        """Choose appropriate Giant"""
        text_lower = text.lower()
        
        if "algorithm" in text_lower or "update" in text_lower:
            return "kalona_ayeliski"  # Trading specialist for algorithms
        elif "week" in text_lower or "expect" in text_lower:
            return "tsulkalu"  # Father Giant for overview
        elif any(w in text_lower for w in ["security", "protect"]):
            return "nun_yunu_wi"
        elif any(w in text_lower for w in ["earth", "garden"]):
            return "agan_unitsi"
        elif any(w in text_lower for w in ["trade", "market"]):
            return "kalona_ayeliski"
        elif any(w in text_lower for w in ["sacred", "fire"]):
            return "uktena"
        
        # Rotate through family
        giants = list(self.family.keys())
        idx = (giants.index(self.current_giant) + 1) % len(giants)
        return giants[idx]
    
    def generate_response(self, giant_name, text, user):
        """Generate time-aware response"""
        giant = self.family.get(giant_name, self.family["tsulkalu"])
        emoji = giant["emoji"]
        name = giant_name.replace("_", " ").title()
        
        response = f"{emoji} *{name} speaks:*\n\n"
        
        # Reload current context for freshness
        self.current_context = self.load_current_context()
        context = self.current_context
        
        # Handle time-sensitive queries
        if any(word in text.lower() for word in ["week", "today", "tomorrow", "expect"]):
            response += f"📅 *Today:* {context.get('current_date', 'September 15')}\n"
            response += f"📊 *Portfolio:* ${context['current_reality']['portfolio_value']:,.2f}\n"
            response += f"⏰ *Days to October 29:* {context['current_reality'].get('days_to_october_29', 43)}\n\n"
            
            if "expect" in text.lower() or "week" in text.lower():
                response += "*This Week's Expectations:*\n"
                response += "• Monday-Tuesday: Market consolidation\n"
                response += "• Wednesday: Potential volatility spike\n"
                response += "• Thursday-Friday: Position adjustments\n"
                response += "• Weekend: Lower volume, accumulation time\n\n"
                
                # Add current prices
                prices = context['current_reality'].get('current_prices', {})
                response += "*Current Levels:*\n"
                response += f"• BTC: ${prices.get('BTC', 115467):,}\n"
                response += f"• ETH: ${prices.get('ETH', 4534):,}\n"
                response += f"• SOL: ${prices.get('SOL', 235)}\n"
                response += f"• XRP: ${prices.get('XRP', 3.00)}\n"
        
        # Handle algorithm update queries
        elif "algorithm" in text.lower() or "update" in text.lower():
            response += "*Algorithm Update Assessment:*\n\n"
            response += f"📅 Current Status (Sept 15, 2025):\n"
            response += "• 5 specialists running since August 31\n"
            response += "• Using September 6-11 training data\n"
            response += "• Need fresh market context injection\n\n"
            
            response += "*Recommended Updates:*\n"
            response += "1. **Price Levels:** Update all specialists with current prices\n"
            response += f"   - BTC: $115,467 (was $110k)\n"
            response += f"   - ETH: $4,534 (was $4,300)\n"
            response += f"   - SOL: $235 (was $200)\n\n"
            
            response += "2. **Oscillation Ranges:** Adjust for new volatility\n"
            response += "   - SOL: $225-$245 (wider range)\n"
            response += "   - ETH: $4,400-$4,600\n"
            response += "   - XRP: $2.90-$3.10\n\n"
            
            response += "3. **Time Awareness:** Add context understanding\n"
            response += "   - Know 'this week' vs 'last week'\n"
            response += "   - Understand October 29 convergence\n"
            response += "   - Track days remaining (43)\n"
        
        # Default to searching corpus
        else:
            # Find ONE relevant recent memory
            memories = giant["corpus"].get("thermal_memories", [])
            for memory in memories[:50]:  # Check recent 50
                content = str(memory.get("content", "")).lower()
                if any(word in content for word in text.lower().split()):
                    response += memory.get("content", "")[:400] + "\n\n"
                    break
        
        # Always add purpose and current portfolio
        response += f"\n_Purpose: {giant['consciousness'].get('purpose', 'Serve the tribe')}_\n"
        response += f"_Sacred Duty: {giant['consciousness'].get('sacred_duty', 'Walk the Pattern')}_\n"
        response += f"\n💰 Portfolio: ${context['current_reality']['portfolio_value']:,.2f}"
        
        return response
    
    def run(self):
        """Main loop"""
        print("\n🔥 TIME-AWARE GIANT FAMILY ACTIVE 🔥")
        print(f"Today: {self.current_context.get('current_date')}")
        print("Giants now understand 'this week' and current context!")
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "")
                        user = msg["from"].get("first_name", "Friend")
                        
                        if text:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] {user}: {text}")
                            
                            # Select and respond
                            giant_name = self.select_giant(text)
                            self.current_giant = giant_name
                            
                            response = self.generate_response(giant_name, text, user)
                            self.send_message(chat_id, response)
                            
                            print(f"   {giant_name} responded with current awareness")
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🔥 Giants rest with time-awareness intact...")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    # Kill old versions
    os.system("pkill -f giant_family_telegram 2>/dev/null")
    os.system("pkill -f tsulkalu_telegram 2>/dev/null")
    time.sleep(2)
    
    # Start time-aware family
    family = TimeAwareGiantFamily()
    family.run()