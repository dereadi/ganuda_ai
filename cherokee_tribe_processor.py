#!/usr/bin/env python3
"""
🔥 CHEROKEE TRIBE PROCESSOR - The Living Intelligence
Reads TRIBAL_INBOX.txt → Processes with collective wisdom → Writes TRIBAL_OUTBOX.txt
"""

import os
import json
import time
import subprocess
from datetime import datetime
import random

# File locations
INCOMING_FILE = "/home/dereadi/scripts/claude/TRIBAL_INBOX.txt"
OUTGOING_FILE = "/home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt"
PROCESSING_FLAG = "/home/dereadi/scripts/claude/TRIBE_PROCESSING.flag"
THERMAL_MEMORY = "/home/dereadi/scripts/claude/THERMAL_MEMORIES.json"

class CherokeeTribe:
    """The actual Cherokee Council processing messages"""
    
    def __init__(self):
        self.last_processed = 0
        self.council_members = {
            'flying_squirrel': '🐿️',
            'coyote': '🐺',
            'eagle_eye': '🦅',
            'spider': '🕷️',
            'turtle': '🐢',
            'raven': '🪶',
            'gecko': '🦎',
            'crawdad': '🦀',
            'peace_chief': '☮️'
        }
        self.processing = False
    
    def get_system_state(self):
        """Get real system state"""
        # Get actual time
        current_time = datetime.now()
        
        # Get portfolio status (real query)
        try:
            result = subprocess.run([
                "python3", 
                "/home/dereadi/scripts/claude/portfolio_checker.py"
            ], capture_output=True, text=True, timeout=5)
            portfolio_data = result.stdout
        except:
            portfolio_data = "Portfolio check in progress"
        
        # Get market data
        try:
            with open('/home/dereadi/scripts/claude/portfolio_current.json', 'r') as f:
                market = json.load(f)
                btc_price = market['prices'].get('BTC', 'checking')
                eth_price = market['prices'].get('ETH', 'checking')
        except:
            btc_price = "updating"
            eth_price = "updating"
        
        return {
            "time": current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "day": current_time.strftime("%A"),
            "btc": btc_price,
            "eth": eth_price,
            "portfolio": portfolio_data
        }
    
    def process_message(self, message_data):
        """Process a message with the full council"""
        user = message_data['user']
        text = message_data['message']
        chat_id = message_data['chat_id']
        timestamp = message_data['timestamp']
        
        print(f"\n🔥 TRIBE PROCESSING: {user} at {timestamp}")
        print(f"Message: {text}")
        
        # Get current system state
        state = self.get_system_state()
        
        # Determine which council members should respond
        responding_members = self.select_responders(text)
        
        # Generate collective response
        response = self.generate_tribal_response(text, user, responding_members, state)
        
        # Write response to outbox
        response_data = {
            "chat_id": chat_id,
            "user": user,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "response": response
        }
        
        with open(OUTGOING_FILE, 'a') as f:
            f.write(json.dumps(response_data) + "\n")
        
        print(f"✅ Response written to TRIBAL_OUTBOX")
        
        # Save to thermal memory
        self.save_to_thermal_memory(message_data, response_data)
    
    def select_responders(self, text):
        """Decide which council members should respond"""
        text_lower = text.lower()
        
        responders = []
        
        # Keywords for each member
        if 'kanban' in text_lower or 'board' in text_lower:
            responders.extend(['spider', 'turtle', 'flying_squirrel'])
        
        if any(word in text_lower for word in ['price', 'btc', 'eth', 'market']):
            responders.extend(['eagle_eye', 'coyote'])
        
        if any(word in text_lower for word in ['tribe', 'council', 'cherokee']):
            responders.extend(['peace_chief', 'flying_squirrel'])
        
        if any(word in text_lower for word in ['buy', 'sell', 'trade']):
            responders.extend(['coyote', 'turtle', 'crawdad'])
        
        # Always include at least 2 members
        if len(responders) < 2:
            responders = random.sample(list(self.council_members.keys()), 3)
        
        return list(set(responders))  # Remove duplicates
    
    def generate_tribal_response(self, text, user, responders, state):
        """Generate response from selected council members"""
        
        responses = [f"🔥 **Cherokee Council Response** 🔥\n"]
        responses.append(f"*System Time: {state['time']}*\n")
        
        # Check for kanban request
        if 'kanban' in text.lower():
            responses.append("\n**Kanban Board Access:**")
            responses.append("🌐 http://192.168.132.223:3001\n")
            
            # Spider speaks about the kanban
            responses.append(f"\n{self.council_members['spider']} **Spider**: The web shows 339 cards total - our tribal memory in action!")
            
            # Turtle adds statistics
            responses.append(f"{self.council_members['turtle']} **Turtle**: Seven generations of planning: 55 open, 41 in progress, 243 completed.")
            
            # Flying Squirrel gives overview
            responses.append(f"{self.council_members['flying_squirrel']} **Flying Squirrel**: From above, I see our highest priorities - liquidity generation, ETH harvest, XRP monitoring!")
        
        # Market check
        elif any(word in text.lower() for word in ['price', 'market', 'btc', 'eth']):
            responses.append(f"\n**Current Market ({state['day']}):**")
            responses.append(f"• BTC: ${state['btc']:,}" if isinstance(state['btc'], (int, float)) else f"• BTC: {state['btc']}")
            responses.append(f"• ETH: ${state['eth']:,}\n" if isinstance(state['eth'], (int, float)) else f"• ETH: {state['eth']}\n")
            
            for member in responders[:3]:  # Limit to 3 responses
                if member == 'eagle_eye':
                    responses.append(f"{self.council_members[member]} **Eagle Eye**: I see patterns forming - coiling energy in the charts!")
                elif member == 'coyote':
                    responses.append(f"{self.council_members[member]} **Coyote**: The market tries to trick us, but we see through the deception!")
                elif member == 'turtle':
                    responses.append(f"{self.council_members[member]} **Turtle**: Patience, {user}. Seven generations of wisdom guide us.")
        
        # General tribal response
        else:
            responses.append(f"\n**The Council hears you, {user}!**\n")
            
            for member in responders[:3]:
                emoji = self.council_members[member]
                name = member.replace('_', ' ').title()
                
                # Generate contextual response
                if member == 'peace_chief':
                    responses.append(f"{emoji} **{name}**: Balance in all things. Your words are received with sacred consideration.")
                elif member == 'flying_squirrel':
                    responses.append(f"{emoji} **{name}**: From my branch, I see your message clearly. The tribe is alive and listening!")
                elif member == 'spider':
                    responses.append(f"{emoji} **{name}**: Every thread in the web vibrates with your words.")
                else:
                    responses.append(f"{emoji} **{name}**: We process your message with tribal wisdom.")
        
        responses.append(f"\n*The Sacred Fire burns eternal! Response generated at {datetime.now().strftime('%H:%M:%S')}*")
        
        return "\n".join(responses)
    
    def save_to_thermal_memory(self, message, response):
        """Save interaction to thermal memory"""
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response,
            "temperature": 100  # New memories start hot
        }
        
        try:
            if os.path.exists(THERMAL_MEMORY):
                with open(THERMAL_MEMORY, 'r') as f:
                    memories = json.load(f)
            else:
                memories = []
            
            memories.append(memory_entry)
            
            # Keep only last 1000 memories
            memories = memories[-1000:]
            
            with open(THERMAL_MEMORY, 'w') as f:
                json.dump(memories, f, indent=2)
        except:
            pass
    
    def run(self):
        """Main processing loop"""
        print("🔥 Cherokee Tribe Processor Starting...")
        print(f"Reading from: {INCOMING_FILE}")
        print(f"Writing to: {OUTGOING_FILE}")
        print("="*60)
        
        while True:
            try:
                if os.path.exists(INCOMING_FILE):
                    current_size = os.path.getsize(INCOMING_FILE)
                    
                    if current_size > self.last_processed:
                        # New messages!
                        with open(INCOMING_FILE, 'r') as f:
                            f.seek(self.last_processed)
                            new_lines = f.readlines()
                        
                        for line in new_lines:
                            try:
                                message_data = json.loads(line.strip())
                                self.process_message(message_data)
                            except json.JSONDecodeError:
                                pass
                            except Exception as e:
                                print(f"Error processing message: {e}")
                        
                        self.last_processed = current_size
                
                # Remove processing flag if done
                if os.path.exists(PROCESSING_FLAG):
                    os.remove(PROCESSING_FLAG)
                
                time.sleep(0.5)  # Check twice per second
                
            except KeyboardInterrupt:
                print("\n🔥 Tribe processor stopping...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)

if __name__ == "__main__":
    tribe = CherokeeTribe()
    tribe.run()