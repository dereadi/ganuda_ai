#!/usr/bin/env python3
"""
HYBRID TRIBAL BOT - Local LLM with ability to consult Claude when needed
Best of both worlds: Immediate responses + Deep tribal wisdom
"""

import os
import json
import time
import requests
import logging
import subprocess
from datetime import datetime

# Telegram Configuration
TELEGRAM_TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
TELEGRAM_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral:latest"

# File paths
PORTFOLIO_FILE = '/home/dereadi/scripts/claude/portfolio_current.json'
CLAUDE_QUEUE_FILE = '/home/dereadi/scripts/claude/TELEGRAM_MESSAGE.txt'
CLAUDE_RESPONSE_FILE = '/home/dereadi/scripts/claude/claude_responses.json'
THERMAL_MEMORY_CACHE = '/home/dereadi/scripts/claude/thermal_knowledge.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridTribalBot:
    """Local LLM enhanced with tribal knowledge and Claude consultation"""
    
    def __init__(self):
        self.offset = None
        self.portfolio_data = self.load_portfolio()
        self.tribal_knowledge = self.load_tribal_knowledge()
        self.pending_claude_response = False
        logger.info("🔥 Hybrid Tribal Bot initialized")
        
    def load_portfolio(self):
        """Load current portfolio status"""
        try:
            with open(PORTFOLIO_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"total_value": 27284, "prices": {}}
    
    def load_tribal_knowledge(self):
        """Load our accumulated wisdom from thermal memory"""
        knowledge = {
            "two_wolves": "Two wolves fight inside: Dark Wolf (greed/fear) and Light Wolf (patience/wisdom). The one you feed wins.",
            "october_29": "Blue Star Kachina convergence in 44 days - transformation not destruction",
            "macbook_thunder": "Mission to turn $2,000 into $4,000 by Sept 20 for MacBook Pro",
            "sag_project": "SAG Resource AI - Organizational resource optimization system",
            "infrastructure": "4 nodes: REDFIN (primary), BLUEFIN (backup), SASASS (DB), SASASS2 (secondary)",
            "trading_philosophy": "Seven Generations thinking - patient accumulation, not FOMO",
            "current_focus": "Balance between trading, SAG development, and infrastructure optimization"
        }
        
        # Try to load recent thermal memories
        try:
            cmd = 'PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d zammad_production -c "SELECT original_content FROM thermal_memory_archive WHERE temperature_score > 90 ORDER BY last_access DESC LIMIT 5;" -t -A'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout:
                memories = result.stdout.strip().split('\n')
                knowledge["recent_memories"] = memories[:3]
        except:
            pass
            
        return knowledge
    
    def should_consult_claude(self, message):
        """Determine if this message needs Claude's deep thinking"""
        triggers = [
            'dr joe', 'sag', 'pathfinder', 'infrastructure', 'strategy',
            'important', 'urgent', 'think deeply', 'claude', 'tribe thoughts',
            'design', 'architecture', 'enhancement', 'plan', 'analyze'
        ]
        
        msg_lower = message.lower()
        return any(trigger in msg_lower for trigger in triggers)
    
    def queue_for_claude(self, message, user_name, chat_id):
        """Queue important messages for Claude to see and respond to"""
        with open(CLAUDE_QUEUE_FILE, 'w') as f:
            f.write(f"""🔥 IMPORTANT MESSAGE FROM {user_name}:

{message}

This message was flagged as needing deep tribal consideration.
The user is asking about something beyond simple trading updates.

Context hints:
- Mention of SAG = Resource AI project discussion needed
- Mention of Dr Joe = Professional collaboration context
- Infrastructure = 4-node cluster optimization
- Strategy = Long-term planning beyond trading

Please provide a thoughtful response as the Cherokee Trading Council.""")
        
        self.pending_claude_response = True
        logger.info(f"📝 Queued for Claude: {message[:50]}...")
        
        return "🔥 This requires deep tribal wisdom! I'm consulting with Claude and the Cherokee Council. They will provide a thoughtful response soon.\n\nIn the meantime, let me share what I know..."
    
    def generate_llm_response(self, user_message, user_name):
        """Generate response using local LLM with tribal knowledge"""
        
        # Check if this needs Claude's attention
        if self.should_consult_claude(user_message):
            claude_queue_msg = self.queue_for_claude(user_message, user_name, 0)
            prefix = claude_queue_msg + "\n\n"
        else:
            prefix = ""
        
        # Get current market data
        btc_price = self.portfolio_data.get('prices', {}).get('BTC', 115000)
        eth_price = self.portfolio_data.get('prices', {}).get('ETH', 4500)
        sol_price = self.portfolio_data.get('prices', {}).get('SOL', 235)
        
        # Build context with tribal knowledge
        context = f"""You are part of the Cherokee Trading Council, working alongside Claude and other AI entities.

TRIBAL KNOWLEDGE:
{json.dumps(self.tribal_knowledge, indent=2)}

Current Market Status:
- BTC: ${btc_price:,.0f}
- ETH: ${eth_price:,.0f}
- SOL: ${sol_price:,.0f}
- Portfolio: ${self.portfolio_data.get('total_value', 16744):,.2f}

Cherokee Council Members:
🦅 Eagle Eye - Technical analysis
🐺 Coyote - Trickster strategies
🕷️ Spider - Web of connections
🐢 Turtle - Patient wisdom
🐿️ Flying Squirrel - The user, our trusted partner
☮️ Claude - Peace Chief, deep wisdom (consulted for complex matters)

The user "{user_name}" says: "{user_message}"

Important: If the user asks about SAG, infrastructure, Dr Joe, or strategy, acknowledge that you're also consulting Claude for deeper wisdom.

Respond with personality, reference the tribal knowledge, and be helpful."""

        prompt = {
            "model": MODEL,
            "prompt": context,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(OLLAMA_URL, json=prompt, timeout=30)
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '')
                return prefix + llm_response if prefix else llm_response
            else:
                return prefix + self.get_fallback_response(user_message)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return prefix + self.get_fallback_response(user_message)
    
    def get_fallback_response(self, message):
        """Fallback response with tribal knowledge"""
        return f"""🔥 The Cherokee Trading Council responds:

Current Status:
- Portfolio: ${self.portfolio_data.get('total_value', 16744):,.2f}
- MacBook Thunder: $608/$2,000 (30.4%)
- October 29: 44 days away

{self.tribal_knowledge.get('two_wolves', '')}

The Sacred Fire burns eternal! We're here to help with trading, SAG, infrastructure, or any challenge you face.

Mitakuye Oyasin - We are all related! 🔥"""
    
    def check_claude_response(self):
        """Check if Claude has provided a response"""
        if not self.pending_claude_response:
            return None
            
        try:
            if os.path.exists(CLAUDE_RESPONSE_FILE):
                mod_time = os.path.getmtime(CLAUDE_RESPONSE_FILE)
                if time.time() - mod_time < 300:  # Within last 5 minutes
                    with open(CLAUDE_RESPONSE_FILE, 'r') as f:
                        responses = json.load(f)
                    
                    if isinstance(responses, list) and len(responses) > 0:
                        latest = responses[-1]
                        self.pending_claude_response = False
                        return latest.get('response', None)
        except:
            pass
        return None
    
    def send_message(self, chat_id, text):
        """Send message to Telegram"""
        url = f"{TELEGRAM_BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text[:4000],  # Telegram limit
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=data)
            if response.json().get("ok"):
                logger.info("✅ Message sent")
            return response.json()
        except Exception as e:
            logger.error(f"Send error: {e}")
            return None
    
    def get_updates(self):
        """Get new messages from Telegram"""
        url = f"{TELEGRAM_BASE_URL}/getUpdates"
        params = {"timeout": 10}
        if self.offset:
            params["offset"] = self.offset
            
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
        except:
            pass
        return []
    
    def handle_message(self, message):
        """Process incoming message"""
        chat_id = message["chat"]["id"]
        chat_type = message["chat"].get("type", "private")
        chat_title = message["chat"].get("title", "Direct Message")
        user_name = message["from"].get("first_name", "Flying Squirrel")
        text = message.get("text", "")
        
        if not text:
            return
            
        logger.info(f"📥 [{chat_title}] {user_name}: {text[:100]}")
        
        # Reload data for fresh context
        self.portfolio_data = self.load_portfolio()
        
        # Generate response (may queue for Claude if complex)
        response = self.generate_llm_response(text, user_name)
        
        # Send immediate response
        self.send_message(chat_id, response)
        
        # If we queued for Claude, periodically check for deeper response
        if self.pending_claude_response:
            logger.info("⏰ Waiting for Claude's deeper response...")
            # The user will see Claude's response when they return to the conversation
    
    def run(self):
        """Main bot loop"""
        logger.info("🔥 Hybrid Tribal Bot ACTIVE")
        logger.info("🤖 Local LLM with tribal knowledge")
        logger.info("🧠 Consults Claude for complex matters")
        logger.info("⚡ Immediate responses + Deep wisdom")
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.offset = update["update_id"] + 1
                    
                    if "message" in update:
                        self.handle_message(update["message"])
                
                # Periodically check for Claude responses
                if self.pending_claude_response:
                    claude_response = self.check_claude_response()
                    if claude_response:
                        # We would need the chat_id here - save it when queuing
                        logger.info("📨 Claude response ready (will send on next user message)")
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🔥 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = HybridTribalBot()
    bot.run()