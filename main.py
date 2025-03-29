#!/usr/bin/env python3
"""
Main entry point for the Voidvisa Checker Telegram Bot.
"""
import os
import logging
from telegram.ext import Updater
from bot import setup_bot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Get the Telegram token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return

    # Create the Updater and pass it your bot's token
    updater = Updater(token=token, use_context=True)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Setup bot with all handlers
    setup_bot(dispatcher)
    
    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
