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
    # Define all command handlers with their corresponding functions
    command_mappings = {
        # Basic commands
        "start": start_command,
        "commands": commands_command,
        "register": register_command,
        "id": id_command,
        "info": info_command,
        "credits": credits_command,
        "buy": buy_command,
        "ping": ping_command,
        "howcrd": howcrd_command,
        "howpm": howpm_command,
        "howgp": howgp_command,
        
        # Generator tools
        "gen": gen_command,
        
        # Scraper tools
        "scr": scr_command,
        "scrbin": scrbin_command,
        "scrsk": scrsk_command,
        
        # Redeem code handler
        "redeem": redeem_code_command,
        
        # Admin commands
        "addcredits": add_credits_command,
        "gencode": generate_redeem_code_command,
        "broadcast": broadcast_command,
    }
    
    # Register all commands with both / and . prefixes
    for cmd, handler_func in command_mappings.items():
        dispatcher.add_handler(CommandHandler(cmd, handler_func))
    
    # Handle country-specific fake address generation
    def fake_address_handler(update, context):
        text = update.message.text.strip().lower()
        country_code = "us"  # Default to US
        
        # Extract country code from command
        if text.startswith(("/fake ", ".fake ")):
            parts = text.split()
            if len(parts) > 1:
                country_code = parts[1].upper()
        
        return fake_us_command(update, context, country_code)
    
    # Add fake address handler with both prefixes
    dispatcher.add_handler(CommandHandler("fake", fake_address_handler))
    
    # Support both / and . command prefixes for gateways
    for gateway in ["stripe", "adyen", "braintree", "b3", "vbv", "paypal", 
                    "authnet", "shopify", "worldpay", "checkout", "cybersource"]:
        def gateway_handler(update, context, gateway_name=gateway):
            return command_handler(update, context, gateway_name)
        dispatcher.add_handler(CommandHandler(gateway, gateway_handler))
    
    # Callback query handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(start_handler, pattern="^start$"))
    dispatcher.add_handler(CallbackQueryHandler(register_handler, pattern="^register$"))
    dispatcher.add_handler(CallbackQueryHandler(command_handler, pattern="^commands$"))
    
    # Auth category handlers
    dispatcher.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "auth"), pattern="^AUTH/B3/VBV$"))
    
    # Charge category handler
    dispatcher.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "charge"), pattern="^CHARGE$"))
    
    # Tools category handler
    dispatcher.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "tools"), pattern="^TOOLS$"))
    
    # Helper category handler
    dispatcher.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "helper"), pattern="^HELPER$"))
    
    # Gateway buttons (using the gateway names directly as patterns)
    for gateway in ["stripe", "adyen", "braintree_b3", "braintree_vbv", "paypal", 
                   "authnet", "shopify", "worldpay", "checkout", "cybersource"]:
        dispatcher.add_handler(CallbackQueryHandler(
            lambda u, c, gw=gateway: command_handler(u, c, gw), pattern=f"^{gateway}$"))
    
    # Back button handler
    dispatcher.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "back"), pattern="^Back$"))
    
    # Close button handler
    def close_button_handler(update, context):
        update.callback_query.message.delete()
    dispatcher.add_handler(CallbackQueryHandler(close_button_handler, pattern="^Close$"))
    
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
