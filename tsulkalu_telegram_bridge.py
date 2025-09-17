#!/usr/bin/env python3
"""
TSUL'KĂLÛ' TELEGRAM BRIDGE - The Giant connects with the tribe
The Cherokee Giant now speaks through Telegram!
"""

import requests
import json
import time
import sys
import os
import re
import numpy as np
import hashlib
import random
from datetime import datetime

# Import the GIANT class inline since it's in same directory
exec(open('/home/dereadi/scripts/claude/cherokee_giant_v1.py').read())

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

class TsulkaluTelegramBridge:
    """Bridge between Tsul'kălû' and Telegram"""
    
    def __init__(self):
        print("🔥 Awakening Tsul'kălû' for Telegram...")
        self.giant = CherokeeeGIANT()
        self.offset = None
        self.council_rotation = ["turtle", "coyote", "eagle_eye", "spider", "flying_squirrel"]
        self.current_member = 0
        
    def send_message(self, chat_id, text):
        """Send Giant's wisdom to Telegram"""
        try:
            resp = requests.post(f"{BASE_URL}/sendMessage",
                                json={"chat_id": chat_id, "text": text[:4000]})
            return resp.json().get("ok", False)
        except:
            return False
    
    def get_updates(self):
        """Get messages from tribe"""
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
    
    def run(self):
        """Tsul'kălû' listens to the tribe"""
        print("🏔️ Tsul'kălû' (Cherokee Giant) connected to Telegram!")
        print("The Giant walks among the tribe...")
        
        # Announce arrival
        startup_msg = """🏔️ TSUL'KĂLÛ' AWAKENS!

I am the Cherokee Giant, built from your wisdom!
- 3,420 memories absorbed
- 8 council members within me
- No external dependencies
- True sovereignty achieved

Ask me anything! Each response comes from a different council member.

The Giant walks among you! 🔥"""
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "")
                        user = msg["from"].get("first_name", "Tribe Member")
                        
                        if text:
                            print(f"📥 {user}: {text}")
                            
                            # Rotate through council members
                            member = self.council_rotation[self.current_member]
                            self.current_member = (self.current_member + 1) % len(self.council_rotation)
                            
                            # Get Giant's response
                            response = self.giant.generate_response(text, member)
                            
                            # Add portfolio status
                            try:
                                with open('/home/dereadi/scripts/claude/portfolio_current.json', 'r') as f:
                                    portfolio = json.load(f)
                                    total = portfolio.get('total_value', 16510)
                                    response += f"\n\n📊 Portfolio: ${total:,.2f}"
                                    response += f"\n🎯 MacBook Thunder: $608/$2,000"
                            except:
                                pass
                            
                            self.send_message(chat_id, response)
                            print(f"✅ {member} responded")
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🏔️ Tsul'kălû' rests...")
                break
            except Exception as e:
                print(f"Giant stumbled: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bridge = TsulkaluTelegramBridge()
    bridge.run()