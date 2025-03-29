"""
Main bot setup and handler registration.
"""
import logging
from telegram.ext import (
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    Filters
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
    broadcast_command,
    redeem_code_command
)

logger = logging.getLogger(__name__)

def setup_bot(dispatcher):
    """
    Set up all command and message handlers for the bot.
    """
    # Basic commands
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("commands", commands_command))
    dispatcher.add_handler(CommandHandler("register", register_command))
    dispatcher.add_handler(CommandHandler("id", id_command))
    dispatcher.add_handler(CommandHandler("info", info_command))
    dispatcher.add_handler(CommandHandler("credits", credits_command))
    dispatcher.add_handler(CommandHandler("buy", buy_command))
    dispatcher.add_handler(CommandHandler("ping", ping_command))
    dispatcher.add_handler(CommandHandler("howcrd", howcrd_command))
    dispatcher.add_handler(CommandHandler("howpm", howpm_command))
    dispatcher.add_handler(CommandHandler("howgp", howgp_command))
    
    # Generator tools
    dispatcher.add_handler(CommandHandler("gen", gen_command))
    dispatcher.add_handler(CommandHandler("fakeus", fake_us_command))
    
    # Scraper tools
    dispatcher.add_handler(CommandHandler("scr", scr_command))
    dispatcher.add_handler(CommandHandler("scrbin", scrbin_command))
    dispatcher.add_handler(CommandHandler("scrsk", scrsk_command))
    
    # Redeem code handler
    dispatcher.add_handler(CommandHandler("redeem", redeem_code_command))
    
    # Admin commands
    dispatcher.add_handler(CommandHandler("addcredits", add_credits_command))
    dispatcher.add_handler(CommandHandler("gencode", generate_redeem_code_command))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # Support both / and . command prefixes
    for prefix in ["/", "."]:
        for gateway in ["stripe", "adyen", "braintree", "b3", "vbv", "paypal", 
                        "authnet", "shopify", "worldpay", "checkout", "cybersource"]:
            def gateway_handler(update, context, gateway_name=gateway):
                return command_handler(update, context, gateway_name)
            dispatcher.add_handler(CommandHandler(gateway, gateway_handler))
    
    # Callback query handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(start_handler, pattern="^start$"))
    dispatcher.add_handler(CallbackQueryHandler(register_handler, pattern="^register$"))
    dispatcher.add_handler(CallbackQueryHandler(lambda u, c: command_handler(u, c), pattern="^commands$"))
    
    # Auth category handlers
    dispatcher.add_handler(CallbackQueryHandler(lambda u, c: command_handler(u, c, "auth"), pattern="^AUTH/B3/VBV$"))
    
    # Charge category handler
    dispatcher.add_handler(CallbackQueryHandler(lambda u, c: command_handler(u, c, "charge"), pattern="^CHARGE$"))
    
    # Tools category handler
    dispatcher.add_handler(CallbackQueryHandler(lambda u, c: command_handler(u, c, "tools"), pattern="^TOOLS$"))
    
    # Helper category handler
    dispatcher.add_handler(CallbackQueryHandler(lambda u, c: command_handler(u, c, "helper"), pattern="^HELPER$"))
    
    # Gateway buttons (using the gateway names directly as patterns)
    for gateway in ["stripe", "adyen", "braintree_b3", "braintree_vbv", "paypal", 
                   "authnet", "shopify", "worldpay", "checkout", "cybersource"]:
        dispatcher.add_handler(CallbackQueryHandler(lambda u, c, gw=gateway: command_handler(u, c, gw), pattern=f"^{gateway}$"))
    
    # Back button handler
    dispatcher.add_handler(CallbackQueryHandler(lambda u, c: command_handler(u, c, "back"), pattern="^Back$"))
    
    # Close button handler
    dispatcher.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.message.delete(), pattern="^Close$"))
    
    # Error handler for better user experience
    dispatcher.add_error_handler(error_handler)
    
    # Message handler for text messages (CC checking) - should be last
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, command_handler))
    
    logger.info("Bot handlers have been set up successfully")

def error_handler(update, context):
    """Handle errors gracefully."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update.effective_message:
            update.effective_message.reply_text(
                "Sorry, something went wrong processing your request. Please try again later."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
    # We don't return anything because an exception occurred
