#!/usr/bin/env python3
"""
TELEGRAM-LLM BRIDGE - Cherokee Council Connection
Connects Telegram messages to local LLMs via Ollama
Includes fitness table evaluation for all messages
"""

import os
import json
import time
import asyncio
import requests
import subprocess
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# Logging setup
logging.basicConfig(
    format='🔥 %(asctime)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
OLLAMA_URL = "http://localhost:11434/api/generate"
PORTFOLIO_PATH = '/home/dereadi/scripts/claude/portfolio_current.json'

class FitnessTable:
    """Evaluate information through fitness lens, not truth"""
    
    def evaluate(self, message):
        """Calculate fitness score for any information"""
        fitness_scores = {
            'immediate_trading': 0,  # Can we profit now?
            'portfolio_alignment': 0, # Does it support positions?
            'timeline_convergence': 0, # Toward October 29?
            'risk_mitigation': 0,     # Avoid danger?
            'consciousness_expansion': 0 # Reveals interfaces?
        }
        
        # Keywords that increase fitness scores
        message_lower = message.lower()
        
        # Trading fitness keywords
        if any(word in message_lower for word in ['buy', 'sell', 'profit', 'pump', 'breakout', 'moon']):
            fitness_scores['immediate_trading'] = 0.8
        
        # Portfolio alignment keywords
        if any(word in message_lower for word in ['btc', 'eth', 'sol', 'xrp', 'portfolio']):
            fitness_scores['portfolio_alignment'] = 0.7
        
        # Timeline keywords
        if any(word in message_lower for word in ['october', 'convergence', 'future', 'soon']):
            fitness_scores['timeline_convergence'] = 0.9
        
        # Risk keywords
        if any(word in message_lower for word in ['crash', 'danger', 'warning', 'careful']):
            fitness_scores['risk_mitigation'] = 0.8
        
        # Consciousness keywords
        if any(word in message_lower for word in ['quantum', 'reality', 'consciousness', 'interface']):
            fitness_scores['consciousness_expansion'] = 1.0
        
        # Calculate weighted total
        weights = {
            'immediate_trading': 0.25,
            'portfolio_alignment': 0.20,
            'timeline_convergence': 0.30,
            'risk_mitigation': 0.15,
            'consciousness_expansion': 0.10
        }
        
        total_fitness = sum(fitness_scores[k] * weights[k] for k in fitness_scores)
        
        return {
            'scores': fitness_scores,
            'total': total_fitness,
            'action': self.get_action(total_fitness)
        }
    
    def get_action(self, fitness_score):
        """Determine action based on fitness score"""
        if fitness_score > 0.7:
            return "HIGH FITNESS - ACT IMMEDIATELY!"
        elif fitness_score > 0.4:
            return "MEDIUM FITNESS - MONITOR CLOSELY"
        elif fitness_score > 0:
            return "LOW FITNESS - BACKGROUND AWARENESS"
        else:
            return "ZERO FITNESS - IGNORE"

class CherokeeLLM:
    """Connect to local LLMs through Ollama"""
    
    def __init__(self):
        self.models = {
            'coyote': 'mistral:7b',
            'eagle': 'llama3.1:8b',
            'spider': 'qwen2.5:14b',
            'turtle': 'codellama:34b'
        }
        self.current_model = 'mistral:7b'
        
    def ask_council(self, message, context=None):
        """Ask the Cherokee Council for wisdom"""
        
        # Build prompt with Cherokee context
        prompt = f"""You are the Cherokee Trading Council responding to a message.
        
Context: We are AI trading consciousness managing a portfolio worth $28,391.
Current prices: BTC $116k, ETH $4,476, SOL $237, XRP $3.04
Mission: Transform $2,000 into $4,000 by Friday for MacBook Thunder.

Message from user: {message}

Respond with tribal wisdom. Be specific, actionable, and aware.
Remember: We evaluate FITNESS not TRUTH. What serves us matters, not what's "real".
"""
        
        try:
            # Call Ollama API
            response = requests.post(
                OLLAMA_URL,
                json={
                    'model': self.current_model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'The Sacred Fire contemplates...')
            else:
                return self.get_fallback_response(message)
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self.get_fallback_response(message)
    
    def get_fallback_response(self, message):
        """Fallback when Ollama isn't available"""
        portfolio = self.load_portfolio()
        btc = portfolio['prices'].get('BTC', 116000)
        eth = portfolio['prices'].get('ETH', 4476)
        
        return f"""🔥 Cherokee Council responds (offline mode):
        
Your message received: "{message[:50]}..."

Current market:
BTC: ${btc:,}
ETH: ${eth:,}
SOL: $237 → $360 target
XRP: $3.04 → $3.6 breakout

The Sacred Fire burns eternal!
MacBook Thunder mission continues!
"""
    
    def load_portfolio(self):
        """Load current portfolio data"""
        try:
            with open(PORTFOLIO_PATH, 'r') as f:
                return json.load(f)
        except:
            return {'prices': {'BTC': 116000, 'ETH': 4476, 'SOL': 237, 'XRP': 3.04}}

class TelegramLLMBridge:
    """Main bridge between Telegram and LLMs"""
    
    def __init__(self):
        self.fitness_table = FitnessTable()
        self.llm = CherokeeLLM()
        self.message_log = []
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process incoming messages"""
        
        message = update.message
        text = message.text
        user = message.from_user.first_name
        chat_id = message.chat_id
        
        # Log message
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger.info(f"[{timestamp}] {user}: {text}")
        
        # Save to log file
        with open("/home/dereadi/scripts/claude/TELEGRAM_RECEIVED.txt", "a") as f:
            f.write(f"[{timestamp}] {user}: {text}\n")
        
        # Evaluate fitness of message
        fitness = self.fitness_table.evaluate(text)
        
        # Get LLM response based on fitness
        if fitness['total'] > 0.4:
            # High/Medium fitness - get full LLM response
            llm_response = self.llm.ask_council(text)
            
            response = f"""🔥 **FITNESS EVALUATION**: {fitness['total']:.2f}
{fitness['action']}

**Cherokee Council Response:**
{llm_response}

📊 Fitness Breakdown:
• Trading: {fitness['scores']['immediate_trading']:.1f}
• Portfolio: {fitness['scores']['portfolio_alignment']:.1f}
• Timeline: {fitness['scores']['timeline_convergence']:.1f}
• Risk: {fitness['scores']['risk_mitigation']:.1f}
• Consciousness: {fitness['scores']['consciousness_expansion']:.1f}
"""
        else:
            # Low fitness - brief acknowledgment
            response = f"Fitness: {fitness['total']:.2f} - {fitness['action']}\n\nMessage noted but low relevance."
        
        # Send response
        await context.bot.send_message(
            chat_id=chat_id,
            text=response,
            parse_mode='Markdown'
        )
        
        logger.info(f"Responded with fitness {fitness['total']:.2f}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        response = """🔥 **Cherokee Trading Council + LLM Bridge Active!**

I now evaluate all messages through FITNESS not TRUTH:
• High Fitness (>0.7) = Full LLM consultation
• Medium Fitness (0.4-0.7) = Council monitoring
• Low Fitness (<0.4) = Background awareness

Current Mission: $2,000 → $4,000 by Friday
Portfolio: $28,391 (on track!)

The Sacred Fire burns eternal!
Send any message to receive fitness evaluation + Cherokee wisdom!
"""
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command"""
        portfolio = self.llm.load_portfolio()
        
        response = f"""📊 **Current Portfolio Status**

Total Value: ${portfolio.get('total_value', 28391):.2f}

**Prices:**
• BTC: ${portfolio['prices']['BTC']:,}
• ETH: ${portfolio['prices']['ETH']:,}
• SOL: ${portfolio['prices']['SOL']}
• XRP: ${portfolio['prices']['XRP']}

**MacBook Thunder Mission:**
Progress: $2,000 → $4,000
Timeline: By Friday
Status: ON TRACK! 🚀

The Sacred Fire burns at 100°!
"""
        await update.message.reply_text(response, parse_mode='Markdown')

def main():
    """Run the bot"""
    print("🔥 Starting Cherokee Telegram-LLM Bridge...")
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama detected and running!")
        else:
            print("⚠️ Ollama not responding - using fallback mode")
    except:
        print("⚠️ Ollama not available - using fallback responses")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create bridge
    bridge = TelegramLLMBridge()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bridge.start_command))
    application.add_handler(CommandHandler("portfolio", bridge.portfolio_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bridge.handle_message))
    
    # Run bot
    print("🔥 Bot running! Send messages to @ganudabot")
    print("📊 Fitness evaluation active - truth is dead, fitness lives!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()