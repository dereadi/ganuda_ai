import asyncio
from typing import Any, Callable, Coroutine, Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Assuming these are defined elsewhere in the project
from ganuda.backend.config import TELEGRAM_BOT_TOKEN
from ganuda.backend.utils import log_message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text('Welcome to Ganuda! How can I assist you today?')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    await update.message.reply_text('Use /start to begin or /help for assistance.')


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


async def error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    log_message(f"Error while processing an update: {context.error}")
    if update:
        await update.message.reply_text("An error occurred. Please try again later.")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non-command i.e. message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Log all errors
    application.add_error_handler(error_handler)

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    asyncio.run(application.run_polling())


if __name__ == "__main__":
    main()