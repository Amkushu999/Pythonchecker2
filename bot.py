"""
Main bot setup and handler registration.
"""
import logging
from telegram.ext import (
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters
)
from handlers import (
    start_handler,
    command_handler,
    register_handler,
    start_command,
    commands_command,
    register_command,
    id_command,
    info_command,
    credits_command,
    buy_command,
    ping_command,
    gen_command,
    fake_us_command,
    scr_command,
    scrbin_command,
    scrsk_command,
    howcrd_command,
    howpm_command,
    howgp_command
)
from handlers.admin import (
    admin_handler,
    add_credits_command,
    generate_redeem_code_command,
    broadcast_command
)

logger = logging.getLogger(__name__)

def setup_bot(application):
    """
    Set up all command and message handlers for the bot.
    """
    # Basic commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("commands", commands_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("credits", credits_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("howcrd", howcrd_command))
    application.add_handler(CommandHandler("howpm", howpm_command))
    application.add_handler(CommandHandler("howgp", howgp_command))
    
    # Generator tools
    application.add_handler(CommandHandler("gen", gen_command))
    application.add_handler(CommandHandler("fakeus", fake_us_command))
    
    # Scraper tools
    application.add_handler(CommandHandler("scr", scr_command))
    application.add_handler(CommandHandler("scrbin", scrbin_command))
    application.add_handler(CommandHandler("scrsk", scrsk_command))
    
    # Redeem code handler
    application.add_handler(CommandHandler("redeem", lambda update, context: 
        admin_handler(update, context, "redeem")))
    
    # Admin commands
    application.add_handler(CommandHandler("addcredits", add_credits_command))
    application.add_handler(CommandHandler("gencode", generate_redeem_code_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # Auth gateway commands
    for gateway in ["stripe", "adyen", "braintree", "b3", "vbv", "paypal"]:
        application.add_handler(CommandHandler(gateway, lambda update, context, gw=gateway: 
            command_handler(update, context, gw)))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(start_handler, pattern="^start$"))
    application.add_handler(CallbackQueryHandler(register_handler, pattern="^register$"))
    application.add_handler(CallbackQueryHandler(command_handler, pattern="^commands$"))
    
    # Auth category handlers
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "auth"), pattern="^AUTH/B3/VBV$"))
    
    # Charge category handler
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "charge"), pattern="^CHARGE$"))
    
    # Tools category handler
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "tools"), pattern="^TOOLS$"))
    
    # Helper category handler
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "helper"), pattern="^HELPER$"))
    
    # Individual auth gateways
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "stripe"), pattern="^Stripe Auth$"))
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "adyen"), pattern="^Adyen Auth$"))
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "braintree_b3"), pattern="^Braintree B3$"))
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "braintree_vbv"), pattern="^Braintree VBV$"))
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "otp"), pattern="^OTP Lookup$"))
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "paypal"), pattern="^Paypal Auth$"))
    
    # Back button handler
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        command_handler(update, context, "back"), pattern="^Back$"))
    
    # Close button handler
    application.add_handler(CallbackQueryHandler(lambda update, context: 
        update.callback_query.message.delete(), pattern="^Close$"))
    
    # Message handler for text messages (CC checking)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, command_handler))
    
    logger.info("Bot handlers have been set up successfully")
    
    return application
