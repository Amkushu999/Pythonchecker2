#!/usr/bin/env python3
"""
Main entry point for the HUMBL3 CH3CK4R Telegram Bot.
"""
import os
import logging
import threading
import sys
from app import app

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_flask_app():
    """Run the Flask web app."""
    logger.info("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_telegram_bot():
    """Run the Telegram bot."""
    try:
        import asyncio
        from telegram.ext import Application
        from bot import setup_bot
    except ImportError as e:
        logger.error(f"Failed to import Telegram modules: {e}")
        logger.error("Make sure python-telegram-bot is installed")
        return

    # Get the Telegram token from environment variables
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        logger.error("Please set the TELEGRAM_BOT_TOKEN environment variable")
        return

    try:
        # Create the Application instance
        application = Application.builder().token(token).build()
        
        # Setup bot with all handlers
        setup_bot(application)
        
        # Run the bot until the user presses Ctrl-C
        logger.info("Starting Telegram bot...")
        application.run_polling(allowed_updates=["message", "callback_query", "chat_member"])
    except Exception as e:
        logger.error(f"Error starting Telegram bot: {e}")
        sys.exit(1)

def main():
    """Start both the bot and web app in separate threads."""
    # Create threads for Flask and the Telegram bot
    flask_thread = threading.Thread(target=run_flask_app)
    bot_thread = threading.Thread(target=run_telegram_bot)
    
    # Set threads as daemons so they automatically terminate when the main process ends
    flask_thread.daemon = True
    bot_thread.daemon = True
    
    # Start threads
    flask_thread.start()
    logger.info("Flask thread started")
    
    # Run the bot in the main thread for proper signal handling
    run_telegram_bot()
    
    # Join threads (will not reach here normally due to updater.idle())
    flask_thread.join()

# When running directly
if __name__ == '__main__':
    main()
