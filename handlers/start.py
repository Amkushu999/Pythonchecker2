"""
Start and registration handlers for the bot.
"""
import logging
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from database import db
from utils.helper import is_user_registered, check_premium_expiry

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: CallbackContext) -> None:
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
    
    # Check if this is a deep link for purchasing
    if context.args and len(context.args) > 0:
        deep_link = context.args[0]
        
        # Check if it's a buy_ command (from premium purchase flow)
        if deep_link.startswith('buy_'):
            parts = deep_link.split('_')
            if len(parts) >= 4:  # buy_plan_reference_id_user_id format
                plan = parts[1]
                reference_id = parts[2]
                buyer_user_id = parts[3]
                
                # Check if the current user is an admin (only admins should handle buy requests)
                from config import ADMIN_USER_IDS
                if user_id in ADMIN_USER_IDS:
                    # Handle the buy request
                    await handle_buy_request(update, plan, reference_id, buyer_user_id)
                    return
    
    # If not a deep link or user is not admin, show normal welcome message
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
        f"Welcome aboard HUMBL3 CH3CK4R! 🚀\n\n"
        f"I am your go-to bot, packed with a variety of gates, tools, and commands to "
        f"enhance your experience. Excited to see what I can do?\n\n"
        f"👇 Tap the Register button to begin your journey.\n"
        f"👇 Discover my full capabilities by tapping the Commands button."
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_buy_request(update: Update, plan: str, reference_id: str, buyer_user_id: str) -> None:
    """Handle premium purchase requests from deep links."""
    plan_details = {
        "basic": {"name": "Basic Tier", "duration": 30, "price": 9.99},
        "silver": {"name": "Silver Tier", "duration": 90, "price": 24.99},
        "gold": {"name": "Gold Tier", "duration": 180, "price": 44.99},
        "platinum": {"name": "Platinum Tier", "duration": 365, "price": 79.99}
    }
    
    if plan not in plan_details:
        await update.message.reply_text("Invalid plan specified in the request.")
        return
    
    selected_plan = plan_details[plan]
    
    # Create admin message for handling the payment
    message = (
        f"💳 <b>New Premium Purchase Request</b> 💳\n\n"
        f"👤 <b>User ID:</b> {buyer_user_id}\n"
        f"🛒 <b>Plan:</b> {selected_plan['name']}\n"
        f"💲 <b>Price:</b> ${selected_plan['price']}\n"
        f"⏱️ <b>Duration:</b> {selected_plan['duration']} days\n"
        f"🔑 <b>Reference:</b> {reference_id}\n\n"
        f"<i>Instructions:</i>\n"
        f"1. Collect payment from the user\n"
        f"2. Use the 'Add Premium' command to add premium status\n"
        f"3. Format: /addpremium {buyer_user_id} {selected_plan['duration']}"
    )
    
    # Create keyboard with admin actions
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve (30 days)", callback_data=f"approve_premium_{buyer_user_id}_30"),
            InlineKeyboardButton("✅ Approve (90 days)", callback_data=f"approve_premium_{buyer_user_id}_90")
        ],
        [
            InlineKeyboardButton("✅ Approve (180 days)", callback_data=f"approve_premium_{buyer_user_id}_180"),
            InlineKeyboardButton("✅ Approve (365 days)", callback_data=f"approve_premium_{buyer_user_id}_365")
        ],
        [
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_premium_{buyer_user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")

async def start_handler(update: Update, context: CallbackContext) -> None:
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
        f"Welcome aboard HUMBL3 CH3CK4R! 🚀\n\n"
        f"I am your go-to bot, packed with a variety of gates, tools, and commands to "
        f"enhance your experience. Excited to see what I can do?\n\n"
        f"👇 Tap the Register button to begin your journey.\n"
        f"👇 Discover my full capabilities by tapping the Commands button."
    )
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def register_command(update: Update, context: CallbackContext) -> None:
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

async def register_handler(update: Update, context: CallbackContext) -> None:
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
