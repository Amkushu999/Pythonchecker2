"""
Group-related handlers for the bot.
"""
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.constants import ParseMode

from database import Database
from config import BOT_USERNAME

# Initialize database
db = Database()

logger = logging.getLogger(__name__)

async def new_member_handler(update: Update, context: CallbackContext) -> None:
    """Handle new members joining a group."""
    if update.message and update.message.new_chat_members:
        for new_member in update.message.new_chat_members:
            # Skip if the new member is the bot itself
            if new_member.id == context.bot.id:
                await send_group_welcome(update, context)
                continue
                
            # Check if the user is already registered
            is_registered = db.user_exists(new_member.id)
            
            # Get member name
            member_name = new_member.first_name
            if new_member.last_name:
                member_name += f" {new_member.last_name}"
            
            # Get username if available
            username = new_member.username or member_name
            
            # Send greeting message with "approved" GIF
            # Note: In a real implementation, you might want to check if the group is authorized
            approved_gif_url = "https://media.giphy.com/media/3oEjHULJ76Bp9ZECXe/giphy.gif"
            
            # Send welcome message with registration prompt if not registered
            welcome_message = (
                f"👋 Hey {username}!\n"
                f"Welcome to our group ❤️\n\n"
                f"📋 Please follow some rules:\n"
                f"1. 🚫 Don't send unwanted links.\n"
                f"2. 🚫 Don't spam.\n"
                f"3. 🚫 Promotion of your channel is prohibited.\n"
                f"4. 🚫 If you are against admins, fuck off.\n\n"
            )
            
            # Add registration prompt if user is not registered
            if not is_registered:
                welcome_message += (
                    f"✅ Just press /register once to continue using me 🥰"
                )
                # Create registration button
                keyboard = [
                    [InlineKeyboardButton("✅ Register Now", callback_data="register")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                # User is already registered
                welcome_message += (
                    f"✅ You're already registered! Enjoy using the bot."
                )
                reply_markup = None
            
            try:
                # First send the GIF
                await context.bot.send_animation(
                    chat_id=update.effective_chat.id,
                    animation=approved_gif_url,
                    caption="APPROVED!",
                    reply_to_message_id=update.message.message_id
                )
                
                # Then send the welcome message
                await update.effective_message.reply_text(
                    welcome_message,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                
            except Exception as e:
                logger.error(f"Error in new_member_handler: {str(e)}")

async def send_group_welcome(update: Update, context: CallbackContext) -> None:
    """Send welcome message when the bot is added to a group."""
    try:
        # Check if the group is already authorized
        group_id = update.effective_chat.id
        is_authorized = db.is_group_authorized(group_id)
        
        # Get group name
        group_name = update.effective_chat.title or "this group"
        
        if is_authorized:
            message = (
                f"🤖 <b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚 Bot</b> is already active in this group!\n\n"
                f"<i>Use /commands to see available commands</i>"
            )
        else:
            message = (
                f"🤖 <b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚 Bot</b> has been added to {group_name}!\n\n"
                f"ℹ️ <b>Important:</b> This group needs to be authorized by an admin.\n"
                f"Please ask an admin to run: <code>/addgroup {group_id}</code>\n\n"
                f"<i>Once authorized, users will be able to use the bot in this group.</i>"
            )
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Error in send_group_welcome: {str(e)}")

async def left_member_handler(update: Update, context: CallbackContext) -> None:
    """Handle members leaving the group."""
    if update.message and update.message.left_chat_member:
        # Check if the leaving member is the bot itself
        if update.message.left_chat_member.id == context.bot.id:
            # Bot was removed from the group, perform cleanup if needed
            group_id = update.effective_chat.id
            # Optionally remove group from authorized list if it was authorized
            if db.is_group_authorized(group_id):
                db.remove_authorized_group(group_id)
                logger.info(f"Bot was removed from group {group_id}, group authorization removed")