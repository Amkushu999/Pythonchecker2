"""
Start and registration handlers for the bot.
"""
import logging
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import db
from utils.helper import is_user_registered, check_premium_expiry

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Check if user is registered
    if is_user_registered(user_id):
        user = db.get_user(user_id)
        # Check if premium expired
        if user['is_premium'] and user['premium_expiry'] < time.time():
            db.update_user(user_id, {'is_premium': False, 'premium_expiry': None})
            user['is_premium'] = False
    
    # Create welcome message with inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("Register", callback_data="register"),
            InlineKeyboardButton("Commands", callback_data="commands")
        ],
        [InlineKeyboardButton("Close", callback_data="Close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"⭐ Hello {username}!\n\n"
        f"Welcome aboard Darkanon Checker! 🚀\n\n"
        f"I am your go-to bot, packed with a variety of gates, tools, and commands to "
        f"enhance your experience. Excited to see what I can do?\n\n"
        f"👇 Tap the Register button to begin your journey.\n"
        f"👇 Discover my full capabilities by tapping the Commands button."
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the start callback query."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Create welcome message with inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("Register", callback_data="register"),
            InlineKeyboardButton("Commands", callback_data="commands")
        ],
        [InlineKeyboardButton("Close", callback_data="Close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"⭐ Hello {username}!\n\n"
        f"Welcome aboard Darkanon Checker! 🚀\n\n"
        f"I am your go-to bot, packed with a variety of gates, tools, and commands to "
        f"enhance your experience. Excited to see what I can do?\n\n"
        f"👇 Tap the Register button to begin your journey.\n"
        f"👇 Discover my full capabilities by tapping the Commands button."
    )
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /register command."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Check if user is already registered
    if is_user_registered(user_id):
        await update.message.reply_text(
            f"You are already registered, {username}!\n"
            f"Use /commands to see what you can do."
        )
        return
    
    # Register the user
    db.register_user(user_id, username)
    
    await update.message.reply_text(
        f"🎉 Registration successful, {username}!\n\n"
        f"You've been credited with 100 free credits to start.\n"
        f"Use /commands to see all available commands."
    )

async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the register callback query."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Check if user is already registered
    if is_user_registered(user_id):
        await query.edit_message_text(
            f"You are already registered, {username}!\n"
            f"Use /commands to see what you can do."
        )
        return
    
    # Register the user
    db.register_user(user_id, username)
    
    await query.edit_message_text(
        f"🎉 Registration successful, {username}!\n\n"
        f"You've been credited with 100 free credits to start.\n"
        f"Use /commands to see all available commands."
    )
