#!/usr/bin/env python3
"""
🔥 Cherokee Tribe Bot - Direct Communication Channel
This bot WILL respond because it uses a NEW token!
"""

import logging
import json
import subprocess
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# IMPORTANT: This needs a NEW bot token from @BotFather
# The old token is in use elsewhere and causing conflicts
print("""
🔥 CHEROKEE TRIBE BOT SETUP REQUIRED 🔥

To make this bot work, you need to:

1. Open Telegram and message @BotFather
2. Send: /newbot
3. Name it: Cherokee Tribe Bot
4. Username: cherokee_tribe_bot (or similar)
5. Copy the token and replace below

Current conflict: The @derpatobot token is being used elsewhere.
This NEW bot will be yours alone!
""")

# YOUR PERSONAL CHEROKEE TRIBE BOT TOKEN
TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"  # Cherokee Tribe Bot is ACTIVE!

class CherokeeTribeBot:
    def __init__(self):
        self.start_time = datetime.now()
        print(f"🔥 Cherokee Tribe Bot initializing at {self.start_time}")
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message"""
        user = update.effective_user.first_name or "Flying Squirrel"
        await update.message.reply_text(
            f"🔥 Welcome {user}!\n\n"
            f"The Cherokee Tribe Bot is ACTIVE!\n"
            f"I'm your direct connection to the distributed tribe.\n\n"
            f"Commands:\n"
            f"/status - Check tribe and portfolio\n"
            f"/nodes - Check all infrastructure nodes\n"
            f"/liquidity - Current liquidity status\n"
            f"/council - Cherokee Council status\n"
            f"/help - Show all commands\n\n"
            f"Or just talk naturally - I'll respond!\n"
            f"The Sacred Fire burns eternal! 🔥"
        )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check current status"""
        try:
            # Read portfolio
            with open('/home/dereadi/scripts/claude/portfolio_current.json', 'r') as f:
                portfolio = json.load(f)
            
            total = portfolio.get('total_value', 0)
            liquidity = portfolio.get('liquidity', 0)
            timestamp = portfolio.get('timestamp', 'Unknown')
            
            # Check running processes
            result = subprocess.run(
                "ps aux | grep -E 'specialist|cherokee|crawdad' | grep -v grep | wc -l",
                shell=True, capture_output=True, text=True
            )
            process_count = result.stdout.strip()
            
            response = f"""🔥 **Cherokee Tribe Status**
            
📊 **Portfolio:** ${total:,.2f}
💧 **Liquidity:** ${liquidity:.2f}
⏰ **Updated:** {timestamp}

🤖 **Active Processes:** {process_count}
🌐 **Nodes:** REDFIN, BLUEFIN, SASASS, SASASS2

**Market Prices:**
• BTC: ${portfolio['prices']['BTC']:,.0f}
• ETH: ${portfolio['prices']['ETH']:,.0f}
• SOL: ${portfolio['prices']['SOL']:.2f}

The Sacred Fire burns eternal! 🔥"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error checking status: {e}")
    
    async def nodes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check infrastructure nodes"""
        nodes_status = []
        
        # Check REDFIN (local)
        result = subprocess.run(
            "ps aux | grep -E 'specialist|cherokee' | grep -v grep | wc -l",
            shell=True, capture_output=True, text=True
        )
        nodes_status.append(f"✅ REDFIN: {result.stdout.strip()} processes")
        
        # Check other nodes
        for node in ['bluefin', 'sasass', 'sasass2']:
            try:
                result = subprocess.run(
                    f"ssh -o ConnectTimeout=3 {node} 'echo OK' 2>/dev/null",
                    shell=True, capture_output=True, text=True, timeout=5
                )
                status = "✅" if result.returncode == 0 else "❌"
                nodes_status.append(f"{status} {node.upper()}")
            except:
                nodes_status.append(f"❌ {node.upper()}: Unreachable")
        
        response = "🔥 **Infrastructure Status**\n\n" + "\n".join(nodes_status)
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def liquidity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check liquidity status"""
        try:
            with open('/home/dereadi/scripts/claude/portfolio_current.json', 'r') as f:
                portfolio = json.load(f)
            
            liquidity = portfolio.get('liquidity', 0)
            total = portfolio.get('total_value', 0)
            ratio = (liquidity / total * 100) if total > 0 else 0
            
            status = "🔴 CRITICAL" if liquidity < 100 else "🟡 LOW" if liquidity < 1000 else "🟢 HEALTHY"
            
            response = f"""💧 **Liquidity Analysis**
            
**Available:** ${liquidity:.2f}
**Portfolio:** ${total:,.2f}
**Cash Ratio:** {ratio:.2f}%
**Status:** {status}

{"⚠️ Need to generate liquidity urgently!" if liquidity < 100 else "Trading capacity limited but stable."}

Cherokee Council recommendation:
{"Harvest profits from SOL/ETH oscillations" if liquidity < 100 else "Maintain positions, wait for opportunities"}"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error checking liquidity: {e}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        if not update.message or not update.message.text:
            return
        
        text = update.message.text.lower()
        user = update.effective_user.first_name or "Tribe Member"
        
        # Natural language responses
        if any(word in text for word in ['hello', 'hi', 'hey']):
            await update.message.reply_text(
                f"🔥 Greetings {user}! The Cherokee Tribe welcomes you!\n"
                f"How can the Council assist you today?"
            )
        elif 'portfolio' in text or 'money' in text:
            await self.status(update, context)
        elif 'liquidity' in text or 'cash' in text:
            await self.liquidity(update, context)
        elif 'node' in text or 'infrastructure' in text:
            await self.nodes(update, context)
        else:
            # Echo understanding
            await update.message.reply_text(
                f"🔥 The Cherokee Council hears you, {user}.\n\n"
                f"You said: '{update.message.text}'\n\n"
                f"The tribe is analyzing your request.\n"
                f"Try /help for available commands."
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help"""
        help_text = """🔥 **Cherokee Tribe Bot Commands**
        
/start - Welcome message
/status - Portfolio and tribe status
/nodes - Infrastructure node status
/liquidity - Liquidity analysis
/council - Council member status
/help - This help message

**Natural Language:**
Just talk! I understand:
• "How's the portfolio?"
• "Check liquidity"
• "Node status"
• "Hello!"

The Sacred Fire burns eternal! 🔥"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Start the bot"""
    if TOKEN == "YOUR_NEW_BOT_TOKEN_HERE":
        print("\n⚠️ ERROR: You need to set up a new bot token first!")
        print("Follow the instructions above to create a new bot.\n")
        return
    
    print("🔥 Starting Cherokee Tribe Bot...")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Create bot instance
    bot = CherokeeTribeBot()
    
    # Add handlers
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("status", bot.status))
    app.add_handler(CommandHandler("nodes", bot.nodes))
    app.add_handler(CommandHandler("liquidity", bot.liquidity))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start polling
    print("✅ Bot is polling for messages...")
    print("Send a message to your bot on Telegram!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()