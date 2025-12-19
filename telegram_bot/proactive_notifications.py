# Proactive notification system for group messages
# Add to TribeInterface class
GROUP_CHAT_ID = os.environ.get('TELEGRAM_GROUP_CHAT_ID')  # Set this in start_chief.sh

async def send_group_notification(self, message: str, parse_mode: str = None):
    """Send notification to the Telegram group"""
    if not GROUP_CHAT_ID:
        return {"error": "GROUP_CHAT_ID not configured"}

    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode=parse_mode
        )
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}