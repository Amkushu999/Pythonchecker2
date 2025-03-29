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
from database import Database

# Initialize database
db = Database()
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
    add_premium_command,
    generate_redeem_code_command,
    broadcast_command,
    redeem_code_command,
    ban_user_command,
    unban_user_command,
    ban_list_command,
    lock_command,
    unlock_command,
    maintenance_command,
    add_group_command,
    remove_group_command,
    group_list_command,
    min_credits_command,
    stats_command,
    admin_help_command
)

logger = logging.getLogger(__name__)

def setup_bot(application):
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
        "addpremium": add_premium_command,
        "gencode": generate_redeem_code_command,
        "broadcast": broadcast_command,
        "ban": ban_user_command,
        "unban": unban_user_command,
        "banlist": ban_list_command,
        "lock": lock_command,
        "unlock": unlock_command,
        "maintenance": maintenance_command,
        "addgroup": add_group_command,
        "removegroup": remove_group_command,
        "grouplist": group_list_command,
        "mincredits": min_credits_command,
        "stats": stats_command,
        "adminhelp": admin_help_command,
    }
    
    # Register all commands with both / and . prefixes
    for cmd, handler_func in command_mappings.items():
        application.add_handler(CommandHandler(cmd, handler_func))
        # Add the same command with a dot prefix
        application.add_handler(MessageHandler(
            filters.Regex(f"^\\.{cmd}($|\\s)"), 
            lambda u, c, cmd=cmd, func=handler_func: func(u, c)
        ))
    
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
    application.add_handler(CommandHandler("fake", fake_address_handler))
    application.add_handler(MessageHandler(filters.Regex(r"^\.fake($|\s)"), fake_address_handler))
    
    # Support both / and . command prefixes for gateways
    for gateway in ["stripe", "adyen", "braintree", "b3", "vbv", "paypal", 
                    "authnet", "shopify", "worldpay", "checkout", "cybersource",
                    "klarna", "mollie", "mercadopago", "adyen_test", "square", 
                    "sagepay", "twocheckout", "razorpay", "paysafe", "payu", "paytm"]:
        
        # Create a closure to capture the current gateway value
        def create_gateway_handler(gw):
            return lambda u, c: command_handler(u, c, gw)
            
        handler_func = create_gateway_handler(gateway)
        
        # Add the standard slash command
        application.add_handler(CommandHandler(gateway, handler_func))
        
        # Add the dot prefix version
        application.add_handler(MessageHandler(
            filters.Regex(f"^\\.{gateway}($|\\s)"), 
            handler_func
        ))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(start_handler, pattern="^start$"))
    application.add_handler(CallbackQueryHandler(register_handler, pattern="^register$"))
    application.add_handler(CallbackQueryHandler(command_handler, pattern="^commands$"))
    
    # Auth category handlers
    application.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "auth"), pattern="^AUTH/B3/VBV$"))
    
    # Charge category handler
    application.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "charge"), pattern="^CHARGE$"))
    
    # Tools category handler
    application.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "tools"), pattern="^TOOLS$"))
    
    # Helper category handler
    application.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "helper"), pattern="^HELPER$"))
    
    # Gateway buttons (using the gateway names directly as patterns)
    for gateway in ["stripe", "adyen", "braintree_b3", "braintree_vbv", "paypal", 
                   "authnet", "shopify", "worldpay", "checkout", "cybersource"]:
        application.add_handler(CallbackQueryHandler(
            lambda u, c, gw=gateway: command_handler(u, c, gw), pattern=f"^{gateway}$"))
    
    # Back button handler
    application.add_handler(CallbackQueryHandler(
        lambda u, c: command_handler(u, c, "back"), pattern="^Back$"))
    
    # Close button handler
    def close_button_handler(update, context):
        update.callback_query.message.delete()
    application.add_handler(CallbackQueryHandler(close_button_handler, pattern="^Close$"))
    
    # Premium approval/rejection handlers
    async def approve_premium_handler(update, context):
        query = update.callback_query
        await query.answer()
        
        # Extract user ID and duration from callback data
        # Format: approve_premium_USER_ID_DAYS
        parts = query.data.split("_")
        if len(parts) >= 4:
            try:
                user_id = int(parts[2])
                days = int(parts[3])
                
                # Add premium status
                import time
                expiry = int(time.time()) + (days * 24 * 60 * 60)
                db.set_premium(user_id, expiry)
                
                # Calculate expiry date in readable format
                from datetime import datetime
                expiry_date = datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
                
                # Notify admin of success
                await query.edit_message_text(
                    f"✅ Premium status added successfully!\n\n"
                    f"User ID: {user_id}\n"
                    f"Duration: {days} days\n"
                    f"Expires on: {expiry_date}\n\n"
                    f"The user has been notified of their premium status."
                )
                
                # Try to notify the user (this might fail if the user hasn't started the bot)
                try:
                    admin_username = update.effective_user.username or "Admin"
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🎉 Your premium subscription has been activated!\n\n"
                             f"Duration: {days} days\n"
                             f"Expires on: {expiry_date}\n\n"
                             f"Thank you for your support! You now have unlimited private access to all premium features."
                    )
                except Exception as e:
                    logger.error(f"Error notifying user of premium status: {e}")
                    await query.message.reply_text(f"Note: Unable to notify user {user_id} about their premium status.")
            
            except Exception as e:
                logger.error(f"Error approving premium: {e}")
                await query.edit_message_text(f"❌ Error adding premium status: {str(e)}")
    
    async def reject_premium_handler(update, context):
        query = update.callback_query
        await query.answer()
        
        # Extract user ID from callback data
        # Format: reject_premium_USER_ID
        parts = query.data.split("_")
        if len(parts) >= 3:
            try:
                user_id = int(parts[2])
                
                # Update message to show rejection
                await query.edit_message_text(
                    f"❌ Premium request rejected for user {user_id}.\n\n"
                    f"The user will be notified about the rejection."
                )
                
                # Try to notify the user
                try:
                    admin_username = update.effective_user.username or "Admin"
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"❌ Your premium subscription request has been rejected.\n\n"
                             f"Please contact @{admin_username} for more information."
                    )
                except Exception as e:
                    logger.error(f"Error notifying user of premium rejection: {e}")
                    await query.message.reply_text(f"Note: Unable to notify user {user_id} about the rejection.")
            
            except Exception as e:
                logger.error(f"Error rejecting premium: {e}")
                await query.edit_message_text(f"❌ Error processing rejection: {str(e)}")
    
    # Add handlers for premium approval/rejection
    application.add_handler(CallbackQueryHandler(approve_premium_handler, pattern="^approve_premium_"))
    application.add_handler(CallbackQueryHandler(reject_premium_handler, pattern="^reject_premium_"))
    
    # Error handler for better user experience
    application.add_error_handler(error_handler)
    
    # Message handler for text messages (CC checking) - should be last
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, command_handler))
    
    logger.info("Bot handlers have been set up successfully")

async def error_handler(update, context):
    """Handle errors gracefully."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong processing your request. Please try again later."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
    # We don't return anything because an exception occurred
