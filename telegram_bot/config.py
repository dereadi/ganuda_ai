"""Bot configuration"""
import os

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
AUTHORIZED_ADMIN_IDS = []  # Add Telegram user IDs here