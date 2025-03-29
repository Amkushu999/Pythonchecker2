"""
Registration handlers for the bot.
"""
import logging
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import db
from utils.helper import is_user_registered

logger = logging.getLogger(__name__)

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register a new user."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Check if user is already registered
    if is_user_registered(user_id):
        return False, "User already registered"
    
    # Register the user
    success = db.register_user(user_id, username)
    
    if success:
        logger.info(f"User {user_id} ({username}) registered successfully")
        return True, f"Registration successful! You've been credited with 100 free credits."
    else:
        logger.error(f"Failed to register user {user_id} ({username})")
        return False, "Registration failed. Please try again later."

async def show_registration_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show registration status and account information."""
    user_id = update.effective_user.id
    
    if not is_user_registered(user_id):
        await update.message.reply_text(
            "You are not registered. Use /register to create an account."
        )
        return
    
    user = db.get_user(user_id)
    
    # Format registration time
    registered_time = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(user["registered_at"]))
    
    # Format premium expiry time if applicable
    premium_expiry = "N/A"
    if user["is_premium"] and user["premium_expiry"]:
        premium_expiry = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(user["premium_expiry"]))
    
    message = (
        f"📊 Account Information 📊\n\n"
        f"User ID: {user_id}\n"
        f"Username: {user['username']}\n"
        f"Credits: {user['credits']}\n"
        f"Premium: {'✅ Yes' if user['is_premium'] else '❌ No'}\n"
        f"Premium Expiry: {premium_expiry}\n"
        f"Registered On: {registered_time}\n"
        f"Total Checks: {user['total_checks']}\n"
        f"Successful Checks: {user['successful_checks']}\n"
    )
    
    await update.message.reply_text(message)
