#!/usr/bin/env python3
"""
ULTIMATE ECHO BOT - The simplest bot that WILL work!
"""
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

async def echo_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo every single message"""
    text = update.message.text
    user = update.message.from_user.first_name
    
    logger.info(f"Message from {user}: {text}")
    
    response = f"""🔥 {user}! The tribe responds!

You said: "{text}"

MacBook Thunder Status: ACTIVE
Target: $2,000 → $4,000 by Friday
SOL: Breaking to $360!
XRP: Breaking to $3.6!

The Sacred Fire burns eternal! 🔥"""
    
    await update.message.reply_text(response)
    logger.info("Response sent!")

def main():
    """Run the bot"""
    logger.info("Starting ultimate echo bot...")
    
    # Create app
    app = Application.builder().token(TOKEN).build()
    
    # Handle ALL messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_everything))
    
    logger.info("Bot ready! Send a message to @ganudabot NOW!")
    
    # Run with clean slate
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()