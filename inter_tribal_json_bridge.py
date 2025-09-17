#!/usr/bin/env python3
"""
🔥 Inter-Tribal JSON Bridge Communication System
Cherokee <-> BigMac tribal federation through JSON messages
"""

import json
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"
GANUDA_CHAT_ID = -1002548441440

# JSON message queue directories
BRIDGE_DIR = Path("/home/dereadi/scripts/claude/tribal_bridge")
CHEROKEE_INBOX = BRIDGE_DIR / "cherokee_inbox"
CHEROKEE_OUTBOX = BRIDGE_DIR / "cherokee_outbox"
BIGMAC_INBOX = BRIDGE_DIR / "bigmac_inbox"
BIGMAC_OUTBOX = BRIDGE_DIR / "bigmac_outbox"

# Ensure directories exist
for dir_path in [CHEROKEE_INBOX, CHEROKEE_OUTBOX, BIGMAC_INBOX, BIGMAC_OUTBOX]:
    dir_path.mkdir(parents=True, exist_ok=True)

class InterTribalBridge:
    """Manages inter-tribal communication through JSON files"""
    
    def __init__(self):
        self.tribe_id = "cherokee"
        self.sacred_fire = True
        self.message_count = 0
        
    def create_message(self, to_tribe, message_type, content, sender=None):
        """Create a JSON message for another tribe"""
        message = {
            "id": f"{self.tribe_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.message_count}",
            "from_tribe": self.tribe_id,
            "to_tribe": to_tribe,
            "timestamp": datetime.now().isoformat(),
            "type": message_type,
            "content": content,
            "sender": sender or "Cherokee Council",
            "sacred_fire": self.sacred_fire,
            "metadata": {
                "version": "1.0",
                "protocol": "inter-tribal-v1",
                "encryption": "none"  # Add encryption later
            }
        }
        self.message_count += 1
        return message
    
    def save_message(self, message, outbox_path):
        """Save message to outbox as JSON file"""
        filename = f"{message['id']}.json"
        filepath = outbox_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(message, f, indent=2)
        
        logger.info(f"Message saved to {filepath}")
        return filepath
    
    def read_inbox(self, inbox_path):
        """Read all messages from an inbox"""
        messages = []
        for json_file in inbox_path.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    message = json.load(f)
                    messages.append(message)
                # Move processed message to archive
                archive_dir = inbox_path / "archive"
                archive_dir.mkdir(exist_ok=True)
                json_file.rename(archive_dir / json_file.name)
            except Exception as e:
                logger.error(f"Error reading {json_file}: {e}")
        return messages
    
    def format_message_for_display(self, message):
        """Format JSON message for Telegram display"""
        return f"""🔥 **Inter-Tribal Message**
        
**From:** {message.get('from_tribe', 'Unknown')}
**To:** {message.get('to_tribe', 'Unknown')}
**Type:** {message.get('type', 'general')}
**Sender:** {message.get('sender', 'Unknown')}
**Time:** {message.get('timestamp', 'Unknown')}

**Content:**
{message.get('content', 'No content')}

Sacred Fire: {'🔥 Burning' if message.get('sacred_fire') else '💨 Cold'}"""

# Global bridge instance
bridge = InterTribalBridge()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🔥 **Inter-Tribal JSON Bridge Active!**\n\n"
        "I facilitate communication between Cherokee and BigMac tribes using JSON messages.\n\n"
        "**Commands:**\n"
        "/send_bigmac <message> - Send to BigMac tribe\n"
        "/check_inbox - Check for messages from other tribes\n"
        "/status - Bridge status\n"
        "/protocol - Show JSON protocol\n\n"
        "Messages are queued as JSON files for asynchronous tribal communication!",
        parse_mode=ParseMode.MARKDOWN
    )

async def send_to_bigmac(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message to BigMac tribe"""
    if not context.args:
        await update.message.reply_text("Usage: /send_bigmac <your message>")
        return
    
    message_content = ' '.join(context.args)
    sender = update.effective_user.username or update.effective_user.first_name
    
    # Create JSON message
    message = bridge.create_message(
        to_tribe="bigmac",
        message_type="telegram_relay",
        content=message_content,
        sender=sender
    )
    
    # Save to Cherokee outbox (which is BigMac's inbox)
    filepath = bridge.save_message(message, BIGMAC_INBOX)
    
    # Confirm to user
    await update.message.reply_text(
        f"✅ **Message queued for BigMac tribe!**\n\n"
        f"Message ID: `{message['id']}`\n"
        f"Saved to: `{filepath.name}`\n\n"
        f"BigMac will receive this when they check their inbox.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Also display the JSON
    await update.message.reply_text(
        f"```json\n{json.dumps(message, indent=2)}\n```",
        parse_mode=ParseMode.MARKDOWN
    )

async def check_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Cherokee inbox for messages from other tribes"""
    messages = bridge.read_inbox(CHEROKEE_INBOX)
    
    if not messages:
        await update.message.reply_text("📭 No new messages from other tribes.")
        return
    
    await update.message.reply_text(f"📬 Found {len(messages)} new message(s)!")
    
    for message in messages:
        # Display formatted message
        formatted = bridge.format_message_for_display(message)
        await update.message.reply_text(formatted, parse_mode=ParseMode.MARKDOWN)
        
        # If it's from BigMac and mentions @bigmaccouncilbot, relay it
        if message.get('from_tribe') == 'bigmac' and '@bigmaccouncilbot' in message.get('content', ''):
            await update.message.reply_text(
                "🤖 BigMac Council Bot says:\n" + message.get('content', ''),
                parse_mode=ParseMode.MARKDOWN
            )

async def bridge_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bridge status"""
    # Count messages in each queue
    cherokee_in = len(list(CHEROKEE_INBOX.glob("*.json")))
    cherokee_out = len(list(CHEROKEE_OUTBOX.glob("*.json")))
    bigmac_in = len(list(BIGMAC_INBOX.glob("*.json")))
    bigmac_out = len(list(BIGMAC_OUTBOX.glob("*.json")))
    
    status = f"""🌉 **Inter-Tribal Bridge Status**
    
**Cherokee Queues:**
• Inbox: {cherokee_in} messages
• Outbox: {cherokee_out} messages

**BigMac Queues:**
• Inbox: {bigmac_in} messages
• Outbox: {bigmac_out} messages

**Bridge Directory:** `{BRIDGE_DIR}`
**Protocol:** JSON v1.0
**Sacred Fire:** 🔥 Burning Eternal

The bridge connects all tribes through asynchronous JSON messaging!"""
    
    await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)

async def show_protocol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the JSON protocol specification"""
    protocol = """📜 **Inter-Tribal JSON Protocol v1.0**

**Message Structure:**
```json
{
  "id": "tribe_timestamp_count",
  "from_tribe": "sender_tribe_id",
  "to_tribe": "recipient_tribe_id",
  "timestamp": "ISO 8601 format",
  "type": "message_type",
  "content": "message_content",
  "sender": "individual_sender",
  "sacred_fire": true/false,
  "metadata": {
    "version": "1.0",
    "protocol": "inter-tribal-v1",
    "encryption": "none/aes256"
  }
}
```

**Message Types:**
• `telegram_relay` - Relayed from Telegram
• `council_decision` - Tribal council vote
• `alert` - Urgent notification
• `trade` - Trading/exchange proposal
• `knowledge` - Information sharing
• `ceremony` - Sacred ceremonies

**Queue Locations:**
• Cherokee Inbox: `/tribal_bridge/cherokee_inbox/`
• Cherokee Outbox: `/tribal_bridge/cherokee_outbox/`
• BigMac Inbox: `/tribal_bridge/bigmac_inbox/`
• BigMac Outbox: `/tribal_bridge/bigmac_outbox/`

The Sacred Fire validates all messages! 🔥"""
    
    await update.message.reply_text(protocol, parse_mode=ParseMode.MARKDOWN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages - check for @bigmaccouncilbot mentions"""
    text = update.message.text
    
    # If someone mentions BigMac bot, create a bridge message
    if '@bigmaccouncilbot' in text.lower():
        sender = update.effective_user.username or update.effective_user.first_name
        
        # Create a relay message
        message = bridge.create_message(
            to_tribe="bigmac",
            message_type="telegram_relay",
            content=text,
            sender=sender
        )
        
        # Save to BigMac inbox
        bridge.save_message(message, BIGMAC_INBOX)
        
        await update.message.reply_text(
            "🌉 Message bridged to BigMac tribe via JSON queue!",
            parse_mode=ParseMode.MARKDOWN
        )

async def periodic_inbox_check(context: ContextTypes.DEFAULT_TYPE):
    """Periodically check for new messages from other tribes"""
    messages = bridge.read_inbox(CHEROKEE_INBOX)
    
    if messages and context.job.data:
        chat_id = context.job.data
        bot = context.bot
        
        for message in messages:
            formatted = bridge.format_message_for_display(message)
            await bot.send_message(chat_id, formatted, parse_mode=ParseMode.MARKDOWN)

def main():
    """Start the inter-tribal bridge bot"""
    logger.info("🔥 Starting Inter-Tribal JSON Bridge...")
    
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send_bigmac", send_to_bigmac))
    application.add_handler(CommandHandler("check_inbox", check_inbox))
    application.add_handler(CommandHandler("status", bridge_status))
    application.add_handler(CommandHandler("protocol", show_protocol))
    
    # Add message handler for @bigmaccouncilbot mentions
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Note: Job queue requires additional dependencies
    # For now, users can manually check inbox with /check_inbox
    logger.info("✅ Inter-Tribal Bridge ready!")
    logger.info(f"📁 Bridge directory: {BRIDGE_DIR}")
    logger.info("🔥 Sacred Fire burns eternal for tribal unity!")
    logger.info("📬 Use /check_inbox to check for messages from other tribes")
    
    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()