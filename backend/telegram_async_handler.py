import asyncio
from typing import Callable, Any, Dict, Optional
from telegram import Update, Bot
from telegram.ext import CallbackContext, Dispatcher, MessageHandler, Filters

class TelegramAsyncHandler:
    def __init__(self, bot_token: str, dispatcher: Dispatcher):
        self.bot = Bot(token=bot_token)
        self.dispatcher = dispatcher
        self.message_handlers: Dict[str, Callable[[Update, CallbackContext], None]] = {}

    async def start(self) -> None:
        """Starts the Telegram bot and adds message handlers."""
        for command, handler in self.message_handlers.items():
            self.dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), handler))
        await self.bot.set_webhook(url='https://your-webhook-url.com')

    async def stop(self) -> None:
        """Stops the Telegram bot and removes webhook."""
        await self.bot.delete_webhook()

    def add_message_handler(self, command: str, handler: Callable[[Update, CallbackContext], None]) -> None:
        """Adds a message handler for a specific command."""
        self.message_handlers[command] = handler

    async def process_update(self, update: Update, context: CallbackContext) -> None:
        """Processes incoming updates asynchronously."""
        if update.message and update.message.text:
            text = update.message.text
            for command, handler in self.message_handlers.items():
                if text.startswith(command):
                    await handler(update, context)
                    break

# Example usage
async def echo(update: Update, context: CallbackContext) -> None:
    """Echoes the received message back to the user."""
    await update.message.reply_text(update.message.text)

if __name__ == "__main__":
    bot_token = 'YOUR_BOT_TOKEN'
    dispatcher = Dispatcher(bot=Bot(token=bot_token), update_queue=None, workers=0)
    handler = TelegramAsyncHandler(bot_token, dispatcher)
    handler.add_message_handler('/echo', echo)
    await handler.start()
    # Keep the bot running
    while True:
        await asyncio.sleep(1000)