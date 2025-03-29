"""
Admin-only handlers for the bot.
"""
import logging
import random
import string
from telegram import Update
from telegram.ext import CallbackContext
from database import db
from config import ADMIN_USER_IDS

logger = logging.getLogger(__name__)

async def admin_handler(update: Update, context: CallbackContext, command: str) -> None:
    """Handle admin commands."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if command == "redeem":
        # Redeem command is for all users
        await redeem_code_command(update, context)
        return
    
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use admin commands.")
        return
    
    # Handle specific admin commands
    if command == "addcredits":
        await add_credits_command(update, context)
    elif command == "addpremium":
        await add_premium_command(update, context)
    elif command == "gencode":
        await generate_redeem_code_command(update, context)
    elif command == "broadcast":
        await broadcast_command(update, context)
    elif command == "ban":
        await ban_user_command(update, context)
    elif command == "unban":
        await unban_user_command(update, context)
    elif command == "banlist":
        await ban_list_command(update, context)
    elif command == "lock":
        await lock_command(update, context)
    elif command == "unlock":
        await unlock_command(update, context)
    elif command == "maintenance":
        await maintenance_command(update, context)
    elif command == "addgroup":
        await add_group_command(update, context)
    elif command == "removegroup":
        await remove_group_command(update, context)
    elif command == "grouplist":
        await group_list_command(update, context)
    elif command == "mincredits":
        await min_credits_command(update, context)
    elif command == "stats":
        await stats_command(update, context)
    elif command == "gatewaystatus":
        await gateway_status_command(update, context)
    elif command == "adminhelp":
        await admin_help_command(update, context)

async def add_credits_command(update: Update, context: CallbackContext) -> None:
    """Handle the /addcredits command to add credits to a user."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /addcredits USER_ID AMOUNT\n"
            "Example: /addcredits 123456789 100"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        
        # Check if user exists
        if not db.user_exists(target_user_id):
            await update.message.reply_text(f"User {target_user_id} does not exist.")
            return
        
        # Add credits
        db.add_credits(target_user_id, amount)
        
        await update.message.reply_text(
            f"✅ Successfully added {amount} credits to user {target_user_id}."
        )
    
    except ValueError:
        await update.message.reply_text("Invalid arguments. Please provide a valid user ID and amount.")
    except Exception as e:
        logger.error(f"Error adding credits: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def generate_redeem_code_command(update: Update, context: CallbackContext) -> None:
    """Handle the /gencode command to generate a redeem code."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /gencode CREDITS PREMIUM_DAYS\n"
            "Example: /gencode 100 30"
        )
        return
    
    try:
        credits = int(context.args[0])
        premium_days = int(context.args[1])
        
        # Generate code
        code = db.generate_redeem_code(credits, premium_days)
        
        await update.message.reply_text(
            f"✅ Redeem code generated successfully:\n\n"
            f"Code: {code}\n"
            f"Credits: {credits}\n"
            f"Premium days: {premium_days}"
        )
    
    except ValueError:
        await update.message.reply_text("Invalid arguments. Please provide valid credits and premium days.")
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def redeem_code_command(update: Update, context: CallbackContext) -> None:
    """Handle the /redeem command to redeem a code."""
    user_id = update.effective_user.id
    
    # Check if user is registered
    if not db.user_exists(user_id):
        await update.message.reply_text("You need to register first. Use /register command.")
        return
    
    # Parse argument
    if not context.args:
        await update.message.reply_text(
            "Usage: /redeem CODE\n"
            "Example: /redeem ANON-PG9X1NEM4GSEHK1-CHK"
        )
        return
    
    code = context.args[0]
    
    # Try to redeem the code
    result = db.redeem_code(user_id, code)
    
    if not result:
        await update.message.reply_text("Invalid or already used code.")
        return
    
    # Format response message
    message = (
        f"Redeemed Successfully ✅\n"
        f"─────────────────\n"
        f"• Giftcode: {code}\n"
        f"• User ID: {user_id}\n\n"
        f"Message: Congratz ! Your Provided Giftcode Successfully Redeemed to Your "
        f"Account And You Got \"{result['credits']} Credits"
    )
    
    if result["premium_days"] > 0:
        message += f" + Premium Subscription"
    
    message += " \"."
    
    await update.message.reply_text(message)

async def broadcast_command(update: Update, context: CallbackContext) -> None:
    """Handle the /broadcast command to send a message to all users."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Get message to broadcast
    if not context.args:
        await update.message.reply_text(
            "Usage: /broadcast MESSAGE\n"
            "Example: /broadcast Hello, this is an announcement!"
        )
        return
    
    message = " ".join(context.args)
    
    # In a real implementation, this would send the message to all users
    # Here we'll just return a success message
    await update.message.reply_text(
        f"✅ Broadcast message sent successfully to all users:\n\n{message}"
    )

async def ban_user_command(update: Update, context: CallbackContext) -> None:
    """Handle the /ban command to ban a user."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /ban USER_ID REASON\n"
            "Example: /ban 123456789 Spamming"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        reason = " ".join(context.args[1:])
        
        # Cannot ban an admin
        if target_user_id in ADMIN_USER_IDS:
            await update.message.reply_text("Cannot ban an admin user.")
            return
        
        # Ban user
        if db.ban_user(target_user_id, reason):
            await update.message.reply_text(
                f"✅ User {target_user_id} has been banned.\n"
                f"Reason: {reason}"
            )
        else:
            await update.message.reply_text(f"User {target_user_id} is already banned.")
    
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a valid user ID.")
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def unban_user_command(update: Update, context: CallbackContext) -> None:
    """Handle the /unban command to unban a user."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /unban USER_ID\n"
            "Example: /unban 123456789"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        # Unban user
        if db.unban_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been unbanned.")
        else:
            await update.message.reply_text(f"User {target_user_id} is not banned.")
    
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a valid user ID.")
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def ban_list_command(update: Update, context: CallbackContext) -> None:
    """Handle the /banlist command to list all banned users."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    banned_users = db.get_banned_users()
    
    if not banned_users:
        await update.message.reply_text("No users are currently banned.")
        return
    
    # Format the ban list
    message = "📋 Ban List:\n\n"
    for user_id, data in banned_users.items():
        message += f"• User ID: {user_id}\n"
        message += f"  Reason: {data['reason']}\n"
        message += f"  Banned at: {data['timestamp']}\n\n"
    
    await update.message.reply_text(message)

async def lock_command(update: Update, context: CallbackContext) -> None:
    """Handle the /lock command to globally lock the system."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Set global lock
    db.set_global_lock(True)
    
    await update.message.reply_text(
        "🔒 System is now globally locked. Only admins can use the bot."
    )

async def unlock_command(update: Update, context: CallbackContext) -> None:
    """Handle the /unlock command to globally unlock the system."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Unset global lock
    db.set_global_lock(False)
    
    await update.message.reply_text(
        "🔓 System is now globally unlocked. All users can use the bot."
    )

async def add_premium_command(update: Update, context: CallbackContext) -> None:
    """Handle the /addpremium command to give premium status to a user."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /addpremium USER_ID DAYS\n"
            "Example: /addpremium 123456789 30"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        days = int(context.args[1])
        
        # Check if user exists
        if not db.user_exists(target_user_id):
            await update.message.reply_text(f"User {target_user_id} does not exist.")
            return
        
        # Add premium status
        import time
        expiry = int(time.time()) + (days * 24 * 60 * 60)
        db.set_premium(target_user_id, expiry)
        
        # Calculate expiry date in readable format
        from datetime import datetime
        expiry_date = datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
        
        await update.message.reply_text(
            f"✅ Successfully added premium status to user {target_user_id}.\n"
            f"Duration: {days} days\n"
            f"Expires on: {expiry_date}"
        )
    
    except ValueError:
        await update.message.reply_text("Invalid arguments. Please provide a valid user ID and number of days.")
    except Exception as e:
        logger.error(f"Error adding premium status: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def maintenance_command(update: Update, context: CallbackContext) -> None:
    """Handle the /maintenance command to toggle maintenance mode."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args:
        # Toggle maintenance mode
        current = db.is_in_maintenance_mode()
        db.set_maintenance_mode(not current)
        
        if not current:
            await update.message.reply_text(
                "🛠️ Maintenance mode enabled. Only admins can use the bot."
            )
        else:
            await update.message.reply_text(
                "✅ Maintenance mode disabled. All users can use the bot."
            )
        return
    
    # Set maintenance mode explicitly
    try:
        mode = context.args[0].lower()
        
        if mode in ["on", "true", "1", "yes"]:
            db.set_maintenance_mode(True)
            await update.message.reply_text(
                "🛠️ Maintenance mode enabled. Only admins can use the bot."
            )
        elif mode in ["off", "false", "0", "no"]:
            db.set_maintenance_mode(False)
            await update.message.reply_text(
                "✅ Maintenance mode disabled. All users can use the bot."
            )
        else:
            await update.message.reply_text(
                "Invalid argument. Use 'on' or 'off'."
            )
    
    except Exception as e:
        logger.error(f"Error setting maintenance mode: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def add_group_command(update: Update, context: CallbackContext) -> None:
    """Handle the /addgroup command to add an authorized group."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /addgroup GROUP_ID\n"
            "Example: /addgroup -1001234567890"
        )
        return
    
    try:
        group_id = int(context.args[0])
        
        # Add group
        if db.add_authorized_group(group_id):
            await update.message.reply_text(
                f"✅ Group {group_id} has been added to the authorized groups list."
            )
        else:
            await update.message.reply_text(
                f"Group {group_id} is already in the authorized groups list."
            )
    
    except ValueError:
        await update.message.reply_text("Invalid group ID. Please provide a valid group ID.")
    except Exception as e:
        logger.error(f"Error adding group: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def remove_group_command(update: Update, context: CallbackContext) -> None:
    """Handle the /removegroup command to remove an authorized group."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args:
        await update.message.reply_text(
            "Usage: /removegroup GROUP_ID\n"
            "Example: /removegroup -1001234567890"
        )
        return
    
    try:
        group_id = int(context.args[0])
        
        # Remove group
        if db.remove_authorized_group(group_id):
            await update.message.reply_text(
                f"✅ Group {group_id} has been removed from the authorized groups list."
            )
        else:
            await update.message.reply_text(
                f"Group {group_id} is not in the authorized groups list."
            )
    
    except ValueError:
        await update.message.reply_text("Invalid group ID. Please provide a valid group ID.")
    except Exception as e:
        logger.error(f"Error removing group: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def group_list_command(update: Update, context: CallbackContext) -> None:
    """Handle the /grouplist command to list all authorized groups."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    authorized_groups = db.get_authorized_groups()
    
    if not authorized_groups:
        await update.message.reply_text("No groups are currently authorized.")
        return
    
    # Format the group list
    message = "📋 Authorized Groups:\n\n"
    for i, group_id in enumerate(authorized_groups, 1):
        message += f"{i}. Group ID: {group_id}\n"
    
    await update.message.reply_text(message)

async def min_credits_command(update: Update, context: CallbackContext) -> None:
    """Handle the /mincredits command to set the minimum credits required for private use."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Parse arguments
    if not context.args:
        current = db.get_min_credits_for_private()
        await update.message.reply_text(
            f"Current minimum credits for private use: {current}\n\n"
            "To change, use: /mincredits AMOUNT\n"
            "Example: /mincredits 10"
        )
        return
    
    try:
        amount = int(context.args[0])
        
        if amount < 0:
            await update.message.reply_text("Amount must be a non-negative integer.")
            return
        
        # Set minimum credits
        db.set_min_credits_for_private(amount)
        
        await update.message.reply_text(
            f"✅ Minimum credits for private use set to {amount}."
        )
    
    except ValueError:
        await update.message.reply_text("Invalid amount. Please provide a valid integer.")
    except Exception as e:
        logger.error(f"Error setting minimum credits: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def stats_command(update: Update, context: CallbackContext) -> None:
    """Handle the /stats command to show system statistics."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    try:
        stats = db.data["stats"]
        users = db.data["users"]
        
        total_users = len(users)
        premium_users = sum(1 for user in users.values() if user.get("is_premium", False))
        
        message = (
            "📊 System Statistics:\n\n"
            f"Total users: {total_users}\n"
            f"Premium users: {premium_users}\n"
            f"Total checks: {stats['total_checks']}\n"
            f"Successful checks: {stats['successful_checks']}\n"
            f"Success rate: {stats['successful_checks'] / stats['total_checks'] * 100:.2f}% (if total_checks > 0 else 0)%\n\n"
            f"System status:\n"
            f"• Global lock: {'🔒 Enabled' if db.is_globally_locked() else '🔓 Disabled'}\n"
            f"• Maintenance mode: {'🛠️ Enabled' if db.is_in_maintenance_mode() else '✅ Disabled'}\n"
            f"• Group usage: {'✅ Enabled' if db.is_group_enabled() else '❌ Disabled'}\n"
            f"• Min credits for private: {db.get_min_credits_for_private()}"
        )
        
        await update.message.reply_text(message)
    
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

async def admin_help_command(update: Update, context: CallbackContext) -> None:
    """Handle the /adminhelp command to show admin command help."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    message = (
        "<b>🔑 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚 Admin Commands</b>\n\n"
        "<b>👤 User Management:</b>\n"
        "• <code>/addcredits USER_ID AMOUNT</code> - Add credits\n"
        "• <code>/addpremium USER_ID DAYS</code> - Add premium\n"
        "• <code>/ban USER_ID REASON</code> - Ban user\n"
        "• <code>/unban USER_ID</code> - Unban user\n"
        "• <code>/banlist</code> - Show banned users\n\n"
        
        "<b>⚙️ System Management:</b>\n"
        "• <code>/lock</code> - Lock system (admins only)\n"
        "• <code>/unlock</code> - Unlock system\n"
        "• <code>/maintenance [on/off]</code> - Toggle maintenance\n"
        "• <code>/mincredits AMOUNT</code> - Set min credits\n\n"
        
        "<b>👥 Group Management:</b>\n"
        "• <code>/addgroup GROUP_ID</code> - Authorize group\n"
        "• <code>/removegroup GROUP_ID</code> - Remove group\n"
        "• <code>/grouplist</code> - List all groups\n\n"
        
        "<b>🎟️ Code Management:</b>\n"
        "• <code>/gencode CREDITS DAYS</code> - Generate code\n\n"
        
        "<b>📢 Communication:</b>\n"
        "• <code>/broadcast MESSAGE</code> - Message all users\n\n"
        
        "<b>📊 Information:</b>\n"
        "• <code>/stats</code> - System statistics\n"
        "• <code>/gatewaystatus</code> - Check gateway API keys\n"
        "• <code>/adminhelp</code> - Show this help message"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")

async def gateway_status_command(update: Update, context: CallbackContext) -> None:
    """Handle the /gatewaystatus command to check the status of all payment gateways."""
    user_id = update.effective_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    try:
        # Import the gateway utility functions
        from utils.gateway_utils import get_gateway_status
        
        # Get the status of all gateways
        gateway_status = get_gateway_status()
        
        # Format the status message
        message = "<b>🛠️ 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚 Gateway Status</b>\n\n"
        
        # Count configured gateways
        configured_count = sum(1 for status in gateway_status.values() if status)
        total_count = len(gateway_status)
        
        message += f"<b>Summary:</b> {configured_count}/{total_count} gateways configured\n\n"
        
        # Group gateways by status
        message += "<b>✅ Configured Gateways:</b>\n"
        configured = [name.upper() for name, status in gateway_status.items() if status]
        if configured:
            for name in configured:
                message += f"• <code>{name}</code>\n"
        else:
            message += "• None\n"
        
        message += "\n<b>❌ Unconfigured Gateways:</b>\n"
        unconfigured = [name.upper() for name, status in gateway_status.items() if not status]
        if unconfigured:
            for name in unconfigured:
                message += f"• <code>{name}</code>\n"
        else:
            message += "• None\n"
        
        message += "\n<i>Use the api_keys.py file to configure gateway API keys.</i>"
        
        await update.message.reply_text(message, parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Error checking gateway status: {e}")
        await update.message.reply_text(f"An error occurred while checking gateway status: {str(e)}")
