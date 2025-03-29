#!/usr/bin/env python3
"""
Main entry point for the HUMBL3 CH3CK4R Telegram Bot.
"""
import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot import setup_bot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Start the bot."""
    # Get the Telegram token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return

    # Create the Application and pass it your bot's token
    application = Application.builder().token(token).build()
    
    # Setup bot with all handlers
    await setup_bot(application)
    
    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
