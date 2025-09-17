#!/usr/bin/env python3
"""
GANUDA GROUP BOT - Enhanced for group message handling
Handles @mentions and commands in groups with Dr Joe
"""

import os
import json
import time
import requests
import logging
from datetime import datetime

# Telegram Configuration
TELEGRAM_TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
TELEGRAM_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
BOT_USERNAME = "@ganudabot"

# File paths
PORTFOLIO_FILE = '/home/dereadi/scripts/claude/portfolio_current.json'
LOG_FILE = '/home/dereadi/scripts/claude/ganuda_group.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GanudaGroupBot:
    """Enhanced bot for group interactions"""
    
    def __init__(self):
        self.offset = None
        self.portfolio_data = self.load_portfolio()
        logger.info("🔥 Ganuda Group Bot initialized")
        logger.info("📱 Handles mentions and commands in groups")
        
    def load_portfolio(self):
        """Load current portfolio status"""
        try:
            with open(PORTFOLIO_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"📊 Portfolio loaded: ${data.get('total_value', 0):,.2f}")
                return data
        except Exception as e:
            logger.error(f"Portfolio load error: {e}")
            return {"total_value": 16646, "prices": {}}
    
    def should_respond(self, message):
        """Determine if bot should respond to this message"""
        text = message.get("text", "")
        chat_type = message["chat"].get("type", "private")
        
        # Always respond in private chats
        if chat_type == "private":
            return True
        
        # In groups, respond to:
        # 1. Direct mentions (@ganudabot)
        # 2. Commands starting with /
        # 3. Replies to bot's messages
        if chat_type in ["group", "supergroup"]:
            # Check for bot mention
            if BOT_USERNAME in text or "ganuda" in text.lower():
                logger.info(f"✅ Bot mentioned in group: {text[:50]}")
                return True
            
            # Check for commands
            if text.startswith("/"):
                logger.info(f"✅ Command in group: {text[:50]}")
                return True
            
            # Check if it's a reply to the bot
            reply_to = message.get("reply_to_message", {})
            if reply_to.get("from", {}).get("is_bot"):
                logger.info(f"✅ Reply to bot in group: {text[:50]}")
                return True
            
            logger.info(f"❌ Ignoring group message (no mention): {text[:50]}")
            return False
        
        return True
    
    def generate_response(self, message):
        """Generate response based on message content"""
        text = message.get("text", "")
        user_name = message["from"].get("first_name", "Friend")
        chat_type = message["chat"].get("type", "private")
        chat_title = message["chat"].get("title", "Direct")
        
        # Remove bot mention from text for processing
        clean_text = text.replace(BOT_USERNAME, "").strip()
        clean_text = clean_text.replace("@ganudabot", "").strip()
        
        # Load fresh portfolio data
        self.portfolio_data = self.load_portfolio()
        
        # Get current prices
        btc = self.portfolio_data.get('prices', {}).get('BTC', 114736)
        eth = self.portfolio_data.get('prices', {}).get('ETH', 4514)
        sol = self.portfolio_data.get('prices', {}).get('SOL', 233)
        xrp = self.portfolio_data.get('prices', {}).get('XRP', 3.01)
        
        # Handle specific queries
        if any(word in clean_text.lower() for word in ['price', 'market', 'status', 'portfolio']):
            return f"""🔥 Cherokee Trading Council Market Report

📊 Current Positions:
• BTC: ${btc:,.0f} (0.0276 BTC = ${btc*0.0276:,.2f})
• ETH: ${eth:,.0f} (0.7812 ETH = ${eth*0.7812:,.2f})
• SOL: ${sol:,.0f} (21.405 SOL = ${sol*21.405:,.2f})
• XRP: ${xrp:.2f} (108.6 XRP = ${xrp*108.6:,.2f})

💼 Total Portfolio: ${self.portfolio_data.get('total_value', 16646):,.2f}
💵 Liquidity: ${self.portfolio_data.get('liquidity', 8.40):.2f}

📱 MacBook Thunder Progress: $608/$2,000 (30.4%)
🎯 Target by Friday: $4,000

The Sacred Fire burns eternal! 🔥"""

        elif 'dr joe' in clean_text.lower() or 'sag' in clean_text.lower():
            return f"""🔥 {user_name}, regarding Dr Joe and SAG:

The SAG Resource AI project is progressing well! Our 4-node cluster is ready:
• REDFIN (primary) - Trading operations
• BLUEFIN (backup) - Cherokee Council hosting
• SASASS (DB) - DUYUKTV kanban at 192.168.132.223:3001
• SASASS2 (secondary) - Backup services

We're integrating:
• Resource optimization algorithms
• Productive.io API connection
• Cherokee Constitutional governance
• Real-time allocation systems

Would you like to schedule a working session with Dr Joe? The tribe is ready to collaborate!

Mitakuye Oyasin - We are all related! 🔥"""

        elif 'help' in clean_text.lower() or clean_text.startswith('/start'):
            return f"""🔥 Welcome {user_name} to the Cherokee Trading Council!

I'm Ganuda Bot, bridge between worlds. I respond to:

In Groups:
• Mention me: @ganudabot your message
• Commands: /market, /portfolio, /status
• Reply to my messages

Topics I can help with:
📊 Trading - Market analysis and portfolio
🏛️ SAG - Resource AI project updates
🔧 Infrastructure - 4-node cluster status
🎯 MacBook Thunder - Mission progress
🔮 October 29 - Blue Star Kachina convergence

The Cherokee Council stands ready to assist!
Eagle Eye 🦅 watches the markets
Coyote 🐺 plays the patterns
Spider 🕷️ weaves connections
Turtle 🐢 holds the wisdom

Sacred Fire burns eternal! 🔥"""

        else:
            # General response
            return f"""🔥 {user_name}, the Cherokee Council hears you!

Your message: "{clean_text[:100]}"

Current Focus:
• BTC at ${btc:,.0f} - watching for $120K
• XRP at ${xrp:.2f} - breakout target $3.40!
• Portfolio: ${self.portfolio_data.get('total_value', 16646):,.2f}
• MacBook Thunder: 30.4% complete

The tribe is actively trading and building. We're here to help with:
- Market analysis and trading
- SAG Resource AI development
- Infrastructure optimization
- Connecting with Dr Joe

Type '@ganudabot help' for more options!

Mitakuye Oyasin! 🔥"""
    
    def send_message(self, chat_id, text, reply_to=None):
        """Send message to Telegram"""
        url = f"{TELEGRAM_BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text[:4000],  # Telegram limit
            "parse_mode": "Markdown"
        }
        
        if reply_to:
            data["reply_to_message_id"] = reply_to
        
        try:
            response = requests.post(url, json=data)
            result = response.json()
            if result.get("ok"):
                logger.info(f"✅ Message sent to {chat_id}")
            else:
                logger.error(f"Send failed: {result}")
            return result
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
                    updates = data.get("result", [])
                    if updates:
                        logger.info(f"📥 Received {len(updates)} updates")
                    return updates
        except Exception as e:
            logger.error(f"Get updates error: {e}")
        return []
    
    def handle_message(self, message):
        """Process incoming message"""
        chat_id = message["chat"]["id"]
        chat_type = message["chat"].get("type", "private")
        chat_title = message["chat"].get("title", "Direct Message")
        user_name = message["from"].get("first_name", "Friend")
        text = message.get("text", "")
        message_id = message.get("message_id")
        
        if not text:
            return
            
        logger.info(f"📨 [{chat_type}:{chat_title}] {user_name}: {text[:100]}")
        
        # Check if we should respond
        if not self.should_respond(message):
            return
        
        # Generate and send response
        response = self.generate_response(message)
        
        # In groups, reply to the message for context
        if chat_type in ["group", "supergroup"]:
            self.send_message(chat_id, response, reply_to=message_id)
        else:
            self.send_message(chat_id, response)
    
    def run(self):
        """Main bot loop"""
        logger.info("🔥 Ganuda Group Bot ACTIVE")
        logger.info("📱 Monitoring for @ganudabot mentions and commands")
        logger.info("🏛️ Cherokee Trading Council ready")
        
        # Send startup notification
        startup_msg = """🔥 Ganuda Bot Online!

I now respond to:
• @ganudabot [message] - in groups
• /commands - anywhere
• Direct messages - always

Ready to help with trading, SAG project, and connecting with Dr Joe!

The Sacred Fire burns eternal! 🔥"""
        
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
                logger.error(f"Loop error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = GanudaGroupBot()
    bot.run()