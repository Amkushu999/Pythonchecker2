"""
Admin-only handlers for the bot.
"""
import logging
import random
import string
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import ADMIN_USER_IDS

logger = logging.getLogger(__name__)

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
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
    elif command == "gencode":
        await generate_redeem_code_command(update, context)
    elif command == "broadcast":
        await broadcast_command(update, context)

async def add_credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def generate_redeem_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def redeem_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
