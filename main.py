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
    """Run the Telegram bot using polling or webhook based on configuration."""
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
        # Webhook configuration
        webhook_url = os.environ.get("WEBHOOK_URL")
        webhook_port = int(os.environ.get("WEBHOOK_PORT", "8443"))
        webhook_listen = os.environ.get("WEBHOOK_LISTEN", "0.0.0.0")
        webhook_cert = os.environ.get("WEBHOOK_CERT_PATH")
        webhook_key = os.environ.get("WEBHOOK_KEY_PATH")
        
        # Create the Application builder
        application_builder = Application.builder().token(token)
        
        # Create the Application instance
        application = application_builder.build()
        
        # Setup bot with all handlers
        setup_bot(application)
        
        # Determine whether to use webhook or polling
        use_webhook = webhook_url is not None
        
        if use_webhook:
            logger.info(f"Starting Telegram bot with webhook at {webhook_url}...")
            
            # Check if certificates are available for more secure webhook
            if webhook_cert and webhook_key:
                application.run_webhook(
                    listen=webhook_listen,
                    port=webhook_port,
                    url_path=token,
                    webhook_url=f"{webhook_url}/{token}",
                    cert=webhook_cert,
                    key=webhook_key,
                    allowed_updates=["message", "callback_query", "chat_member"]
                )
            else:
                # Run with webhook but without certificates (less secure)
                application.run_webhook(
                    listen=webhook_listen,
                    port=webhook_port,
                    url_path=token,
                    webhook_url=f"{webhook_url}/{token}",
                    allowed_updates=["message", "callback_query", "chat_member"]
                )
        else:
            # Fall back to polling method if webhook isn't configured
            logger.info("Starting Telegram bot with polling...")
            application.run_polling(
                allowed_updates=["message", "callback_query", "chat_member"]
            )
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
