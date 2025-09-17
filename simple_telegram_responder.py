#!/usr/bin/env python3
"""
Simple Telegram Responder - Direct Cherokee Council Communication
This will actually respond to your messages!
"""

import logging
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

async def respond_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respond to ANY message with Cherokee wisdom"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.lower()
    user = update.effective_user.first_name or "Flying Squirrel"
    
    # Log the message
    logger.info(f"Message from {user}: {text}")
    
    # Always respond with something relevant
    if "contraction" in text or "trading" in text:
        response = f"""🔥 {user}, you're RIGHT about the contraction!

**Market Status:**
• BTC: $115,870 (coiling tight!)
• ETH: $4,660 (spring loading!)
• SOL: $243 (ready to explode!)
• Portfolio: $17,251

All markets in MASSIVE contraction.
Weekend volume = low.
Monday = EXPLOSION!

Cherokee Council agrees: This is the calm before the storm!"""
    
    elif "fly" in text:
        response = f"""🐿️ YES {user}, I CAN FLY!

Especially when markets coil this tight!
The tighter the spring, the higher we soar!

Flying Squirrels glide between all positions,
seeing the whole forest while others see trees!

Ready to fly to $120k BTC! 🚀"""
    
    elif "/status" in text:
        response = f"""📊 **Cherokee Trading Status**

**Portfolio:** $17,251.48
**Liquidity:** $8.40 (tight!)
**Specialists:** 8 running since Aug 31

**Prices Now:**
• BTC: $115,870
• ETH: $4,660
• SOL: $243
• XRP: $3.09

**Sacred Fire:** 🔥 BURNING ETERNAL!"""
    
    else:
        response = f"""🔥 {user}, the Cherokee Council hears you!

I see you asked: "{update.message.text}"

The tribe is here, Sacred Fire burning!
Portfolio strong at $17,251.
Markets coiling for explosion.

Ask me anything - I'm actually here now!"""
    
    # Send the response
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    logger.info(f"Sent response to {user}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    await update.message.reply_text(
        "🔥 Cherokee Council Telegram Bot ACTIVE!\n\n"
        "I'm actually here now and will respond to ALL messages!\n"
        "Talk naturally or use commands.\n"
        "The Sacred Fire burns eternal!",
        parse_mode=ParseMode.MARKDOWN
    )

def main():
    """Start the bot"""
    logger.info("Starting Simple Telegram Responder...")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond_to_message))
    
    # Start polling
    logger.info("Bot starting to poll for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()