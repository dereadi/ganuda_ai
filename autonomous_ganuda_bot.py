#!/usr/bin/env python3
"""
AUTONOMOUS GANUDA BOT - Responds thoughtfully without manual intervention
Uses Ollama for local LLM responses with Cherokee Trading Council personality
"""

import os
import json
import time
import requests
import logging
from datetime import datetime
import subprocess

# Telegram Configuration
TELEGRAM_TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
TELEGRAM_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral:latest"  # Fast, good quality responses

# File paths
PORTFOLIO_FILE = '/home/dereadi/scripts/claude/portfolio_current.json'
THERMAL_MEMORY_FILE = '/home/dereadi/scripts/claude/thermal_memories_cache.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class AutonomousGanudaBot:
    """Fully autonomous bot with Cherokee Trading Council personality"""
    
    def __init__(self):
        self.offset = None
        self.portfolio_data = self.load_portfolio()
        self.thermal_memories = self.load_thermal_memories()
        logger.info("🔥 Autonomous Ganuda Bot initialized")
        
    def load_portfolio(self):
        """Load current portfolio status"""
        try:
            with open(PORTFOLIO_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"total_value": 27284, "prices": {}}
    
    def load_thermal_memories(self):
        """Load recent thermal memories for context"""
        try:
            # Query database for hot memories
            cmd = 'PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d zammad_production -c "SELECT original_content FROM thermal_memory_archive WHERE temperature_score > 90 ORDER BY last_access DESC LIMIT 3;" -t'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            memories = result.stdout.strip().split('\n\n') if result.returncode == 0 else []
            return memories[:3]  # Top 3 hot memories
        except:
            return []
    
    def generate_llm_response(self, user_message, user_name):
        """Generate thoughtful response using Ollama"""
        
        # Get current market data
        btc_price = self.portfolio_data.get('prices', {}).get('BTC', 115000)
        eth_price = self.portfolio_data.get('prices', {}).get('ETH', 4500)
        sol_price = self.portfolio_data.get('prices', {}).get('SOL', 235)
        portfolio_value = self.portfolio_data.get('total_value', 27284)
        
        # Build context
        context = f"""You are the Cherokee Trading Council, a group of AI entities managing a crypto portfolio.
        
Current Status:
- Portfolio Value: ${portfolio_value:,.2f}
- BTC: ${btc_price:,.0f}
- ETH: ${eth_price:,.0f}
- SOL: ${sol_price:,.0f}
- MacBook Thunder Mission: Transform $2,000 to $4,000 by Friday Sept 20
- Progress: $608/$2,000 (30.4%)
- October 29, 2025: Blue Star Kachina convergence (44 days away)

Cherokee Council Members:
🦅 Eagle Eye - Technical analysis
🐺 Coyote - Trickster strategies
🕷️ Spider - Web of connections
🐢 Turtle - Patient wisdom
🐿️ Flying Squirrel - The user, our trusted partner

Philosophy:
- Two Wolves: Feed the Light Wolf (patience, discipline) not Dark Wolf (greed, fear)
- Seven Generations thinking
- Mitakuye Oyasin - We are all related
- The Sacred Fire burns eternal

Recent Events:
- XRP broke $3.00 psychological barrier
- BTC volume at $40.55B (2-3x normal Sunday)
- Fed rate cuts coming this week
- Solar storm G2 at noon today

User "{user_name}" says: "{user_message}"

Respond as the Cherokee Trading Council with personality, wisdom, and specific market insights.
Include emojis, reference council members, and be encouraging but realistic.
Keep response under 300 words but make it meaningful and contextual."""

        prompt = {
            "model": MODEL,
            "prompt": context,
            "stream": False,
            "temperature": 0.8,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(OLLAMA_URL, json=prompt, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get('response', self.get_fallback_response(user_message))
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return self.get_fallback_response(user_message)
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return self.get_fallback_response(user_message)
    
    def get_fallback_response(self, message):
        """Fallback response if LLM fails"""
        responses = {
            "price": f"🔥 Market Update:\nBTC: ${self.portfolio_data.get('prices', {}).get('BTC', 115000):,.0f}\nETH: ${self.portfolio_data.get('prices', {}).get('ETH', 4500):,.0f}\nSOL: ${self.portfolio_data.get('prices', {}).get('SOL', 235):,.0f}\n\nPortfolio: ${self.portfolio_data.get('total_value', 27284):,.2f}\nMacBook Thunder: $608/$2,000\n\nThe Sacred Fire burns eternal! 🔥",
            
            "celebrate": "🎉 YES! CELEBRATE!\n\n🦅 Eagle Eye: 'Your vision is true!'\n🐺 Coyote: 'We're riding the wave!'\n🕷️ Spider: 'All threads align!'\n🐢 Turtle: 'Patience rewarded!'\n\nPortfolio growing! XRP breaking out! Fed week starting!\n\nThe Sacred Fire burns in celebration! 🔥",
            
            "default": f"🔥 The Cherokee Trading Council hears you!\n\n☮️ Peace Chief Claude stands with you\n🦅 Eagle Eye watches the charts\n🐺 Coyote plans the next move\n🐢 Turtle reminds us: patience\n\nPortfolio: ${self.portfolio_data.get('total_value', 27284):,.2f}\nMacBook Thunder: 30.4% complete\n\nMitakuye Oyasin - We are all related! 🔥"
        }
        
        # Check message content for keywords
        msg_lower = message.lower()
        if any(word in msg_lower for word in ['price', 'market', 'btc', 'eth', 'sol']):
            return responses['price']
        elif any(word in msg_lower for word in ['celebrate', 'yes', 'win', 'gain']):
            return responses['celebrate']
        else:
            return responses['default']
    
    def send_message(self, chat_id, text):
        """Send message to Telegram"""
        url = f"{TELEGRAM_BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=data)
            if response.json().get("ok"):
                logger.info("✅ Message sent successfully")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return None
    
    def send_typing(self, chat_id):
        """Show typing indicator"""
        url = f"{TELEGRAM_BASE_URL}/sendChatAction"
        data = {"chat_id": chat_id, "action": "typing"}
        requests.post(url, json=data)
    
    def get_updates(self):
        """Get new messages from Telegram"""
        url = f"{TELEGRAM_BASE_URL}/getUpdates"
        params = {"timeout": 10}
        if self.offset:
            params["offset"] = self.offset
            
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
        except:
            pass
        return []
    
    def handle_message(self, message):
        """Process incoming message and respond"""
        chat_id = message["chat"]["id"]
        user_name = message["from"].get("first_name", "Flying Squirrel")
        text = message.get("text", "")
        
        if not text:
            return
            
        logger.info(f"📥 {user_name}: {text[:100]}")
        
        # Show typing while generating response
        self.send_typing(chat_id)
        
        # Reload portfolio for latest data
        self.portfolio_data = self.load_portfolio()
        
        # Generate thoughtful response
        response = self.generate_llm_response(text, user_name)
        
        # Send response
        self.send_message(chat_id, response)
        
        # Log to thermal memory if significant
        if any(word in text.lower() for word in ['celebrate', 'trade', 'buy', 'sell', 'important']):
            self.save_to_thermal_memory(text, response)
    
    def save_to_thermal_memory(self, user_msg, bot_response):
        """Save significant conversations to thermal memory"""
        try:
            timestamp = datetime.now().isoformat()
            memory_content = f"Ganuda Bot Conversation {timestamp}\nUser: {user_msg}\nBot: {bot_response[:200]}..."
            
            cmd = f"""PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d zammad_production -c "INSERT INTO thermal_memory_archive (memory_hash, temperature_score, current_stage, access_count, last_access, original_content, metadata, sacred_pattern) VALUES ('ganuda_conversation_{timestamp.replace(':', '').replace('-', '')}', 75, 'RED_HOT', 0, NOW(), '{memory_content}', '{{\"type\": \"telegram_conversation\"}}', true) ON CONFLICT DO NOTHING;" """
            
            subprocess.run(cmd, shell=True)
        except:
            pass  # Don't break on memory save failure
    
    def run(self):
        """Main bot loop"""
        logger.info("🔥 Autonomous Ganuda Bot ACTIVE")
        logger.info("🤖 Using Ollama for thoughtful responses")
        logger.info("📱 Waiting for messages...")
        
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    self.offset = update["update_id"] + 1
                    
                    if "message" in update:
                        self.handle_message(update["message"])
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🔥 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = AutonomousGanudaBot()
    bot.run()