"""
Command handlers for the bot.
"""
import logging
import time
import random
from typing import Optional, Dict, List, Union
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from database import db
from utils.helper import (
    is_user_registered, 
    check_premium_expiry, 
    require_registration,
    require_credits,
    check_rate_limit
)
from utils.card_utils import (
    validate_cc_format,
    generate_random_cc,
    generate_fake_address
)
from gateways import (
    check_card_stripe,
    check_card_adyen,
    check_card_braintree,
    check_card_paypal,
    check_card_authnet,
    check_card_shopify,
    check_card_worldpay,
    check_card_checkout,
    check_card_cybersource
)

logger = logging.getLogger(__name__)

# Define gateway mapping
GATEWAYS = {
    "stripe": check_card_stripe,
    "adyen": check_card_adyen,
    "braintree_b3": lambda cc, month, year, cvv: check_card_braintree(cc, month, year, cvv, "b3"),
    "braintree_vbv": lambda cc, month, year, cvv: check_card_braintree(cc, month, year, cvv, "vbv"),
    "paypal": check_card_paypal,
    "authnet": check_card_authnet,
    "shopify": check_card_shopify,
    "worldpay": check_card_worldpay,
    "checkout": check_card_checkout,
    "cybersource": check_card_cybersource
}

async def commands_command(update: Update, context: CallbackContext) -> None:
    """Handle the /commands command."""
    keyboard = [
        [
            InlineKeyboardButton("AUTH/B3/VBV", callback_data="AUTH/B3/VBV"),
            InlineKeyboardButton("CHARGE", callback_data="CHARGE")
        ],
        [
            InlineKeyboardButton("TOOLS", callback_data="TOOLS"),
            InlineKeyboardButton("HELPER", callback_data="HELPER")
        ],
        [InlineKeyboardButton("Close", callback_data="Close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"Hello User!\n\n"
        f"HUMBL3 CH3CK4R Checker Has plenty of Commands. We Have Auth Gates, "
        f"Charge Gates, Tools, And Other Things.\n\n"
        f"Click Each of Them Below to Know Them Better."
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def command_handler(update: Update, context: CallbackContext, command_type: Optional[str] = None) -> None:
    """Handle commands and callback queries."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Handle callback query if present
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Handle specific callback commands
        if command_type == "auth":
            await show_auth_gates(query)
            return
        elif command_type == "charge":
            await show_charge_gates(query)
            return
        elif command_type == "tools":
            await show_tools(query)
            return
        elif command_type == "helper":
            await show_helper(query)
            return
        elif command_type == "back":
            # Go back to main commands menu
            await commands_handler(query)
            return
        elif command_type and command_type.startswith("buy_"):
            # Handle buy callback - format is buy_[plan]_[user_id]
            parts = command_type.split('_')
            if len(parts) >= 3:
                plan = parts[1]  # basic, silver, gold, platinum
                user_id = int(parts[2])  # Ensure it's the same user
                
                if user_id == update.effective_user.id:
                    # Process payment request
                    await process_payment(query, plan, user_id)
                else:
                    await query.message.reply_text("You cannot use someone else's payment button.")
            return
        elif command_type in GATEWAYS:
            # Show instructions for specific gateway
            await show_gateway_instructions(query, command_type)
            return
        else:
            # Default commands menu
            await commands_handler(query)
            return
    
    # Handle text message (CC checking)
    if update.message and not command_type:
        # Check if message contains CC data
        message_text = update.message.text.strip()
        if not message_text or not "|" in message_text:
            await update.message.reply_text(
                "Invalid format. Please use the following format:\n"
                "XXXXXXXXXXXXXXXX|MM|YYYY|CVV"
            )
            return
        
        # Process CC data
        await process_cc_check(update, context, message_text)
        return
    
    # Handle specific command types
    if command_type == "stripe":
        await check_with_gateway(update, context, "stripe")
    elif command_type == "adyen":
        await check_with_gateway(update, context, "adyen")
    elif command_type == "braintree":
        await check_with_gateway(update, context, "braintree_b3")
    elif command_type == "b3":
        await check_with_gateway(update, context, "braintree_b3")
    elif command_type == "vbv":
        await check_with_gateway(update, context, "braintree_vbv")
    elif command_type == "paypal":
        await check_with_gateway(update, context, "paypal")
    elif command_type == "authnet":
        await check_with_gateway(update, context, "authnet")
    elif command_type == "shopify":
        await check_with_gateway(update, context, "shopify")
    elif command_type == "worldpay":
        await check_with_gateway(update, context, "worldpay")
    elif command_type == "checkout":
        await check_with_gateway(update, context, "checkout")
    elif command_type == "cybersource":
        await check_with_gateway(update, context, "cybersource")

async def commands_handler(query) -> None:
    """Show the commands menu."""
    keyboard = [
        [
            InlineKeyboardButton("AUTH/B3/VBV", callback_data="AUTH/B3/VBV"),
            InlineKeyboardButton("CHARGE", callback_data="CHARGE")
        ],
        [
            InlineKeyboardButton("TOOLS", callback_data="TOOLS"),
            InlineKeyboardButton("HELPER", callback_data="HELPER")
        ],
        [InlineKeyboardButton("Close", callback_data="Close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"Hello User!\n\n"
        f"HUMBL3 CH3CK4R Checker Has plenty of Commands. We Have Auth Gates, "
        f"Charge Gates, Tools, And Other Things.\n\n"
        f"Click Each of Them Below to Know Them Better."
    )
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_auth_gates(query) -> None:
    """Show available auth gates."""
    keyboard = [
        [
            InlineKeyboardButton("Stripe Auth", callback_data="stripe"),
            InlineKeyboardButton("Adyen Auth", callback_data="adyen")
        ],
        [
            InlineKeyboardButton("Braintree B3", callback_data="braintree_b3"),
            InlineKeyboardButton("Braintree VBV", callback_data="braintree_vbv")
        ],
        [
            InlineKeyboardButton("PayPal Auth", callback_data="paypal"),
            InlineKeyboardButton("AuthNet Auth", callback_data="authnet")
        ],
        [
            InlineKeyboardButton("Back", callback_data="Back"),
            InlineKeyboardButton("Close", callback_data="Close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"Hello User!\n\n"
        f"HUMBL3 CH3CK4R Auth Gates.\n\n"
        f"Click on each of them below to get to know them better."
    )
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_charge_gates(query) -> None:
    """Show available charge gates."""
    keyboard = [
        [
            InlineKeyboardButton("Stripe Charge", callback_data="stripe"),
            InlineKeyboardButton("Shopify", callback_data="shopify")
        ],
        [
            InlineKeyboardButton("WorldPay", callback_data="worldpay"),
            InlineKeyboardButton("Checkout", callback_data="checkout")
        ],
        [
            InlineKeyboardButton("CyberSource", callback_data="cybersource"),
            InlineKeyboardButton("AuthNet", callback_data="authnet")
        ],
        [
            InlineKeyboardButton("Back", callback_data="Back"),
            InlineKeyboardButton("Close", callback_data="Close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"Hello User!\n\n"
        f"HUMBL3 CH3CK4R Charge Gates.\n\n"
        f"Click on each of them below to get to know them better."
    )
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_tools(query) -> None:
    """Show available tools."""
    message = (
        f"♦️ Generator Tools of HUMBL3 CH3CK4R\n"
        f"♦️ Status: ✅ Active\n\n"
        f"🚀 Quick Commands Overview:\n\n"
        f"👤 Generator Tools:\n"
        f"1. Random CC Generator Gate: /gen 440393 500 ✅ (Limit: 10k)\n"
        f"2. Fake Address Generator Gate: /fakeus ✅\n\n"
        f"Total Commands: 2"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Back"),
            InlineKeyboardButton("Close", callback_data="Close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_helper(query) -> None:
    """Show helper commands."""
    message = (
        f"♦️ Helper Gates of HUMBL3 CH3CK4R\n"
        f"♦️ Status: ✅ Active\n\n"
        f"🚀 Quick Commands Overview:\n\n"
        f"👤 Account Management:\n"
        f"1. Start Bot: /start\n"
        f"2. Register: /register\n"
        f"3. User ID: /id\n"
        f"4. User Info: /info\n"
        f"5. Credits Balance: /credits\n\n"
        f"💡 Credits & Premiums:\n"
        f"6. Credits System: /howcrd\n"
        f"7. Premium Privileges: /howpm\n"
        f"8. Buy Premium: /buy\n\n"
        f"👥 Community Tools:\n"
        f"9. Add to Group: /howgp\n\n"
        f"✏️ Tech Support:\n"
        f"10. Ping Status: /ping\n\n"
        f"Total Commands: 10"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Back"),
            InlineKeyboardButton("Close", callback_data="Close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_gateway_instructions(query, gateway: str) -> None:
    """Show instructions for using a specific gateway."""
    gateway_name = {
        "stripe": "Stripe Auth",
        "adyen": "Adyen Auth",
        "braintree_b3": "Braintree B3",
        "braintree_vbv": "Braintree VBV",
        "otp": "OTP Lookup",
        "paypal": "PayPal Auth",
        "authnet": "Authorize.Net Auth",
        "shopify": "Shopify Auth",
        "worldpay": "WorldPay Auth",
        "checkout": "Checkout.com Auth",
        "cybersource": "CyberSource Auth"
    }.get(gateway, gateway.capitalize())
    
    message = (
        f"🔍 {gateway_name} Gate Instructions:\n\n"
        f"1. Format: XXXXXXXXXXXXXXXX|MM|YYYY|CVV\n"
        f"2. Example: 4111111111111111|01|2025|123\n\n"
        f"Simply send your card in the format above to check it.\n"
        f"Each check costs 1 credit."
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data="Back"),
            InlineKeyboardButton("Close", callback_data="Close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)

@require_registration
@require_credits(1)
@check_rate_limit
async def process_cc_check(update: Update, context: CallbackContext, message_text: str) -> None:
    """Process a credit card check from a text message."""
    user_id = update.effective_user.id
    
    # Parse CC data
    try:
        cc_parts = message_text.split("|")
        if len(cc_parts) < 4:
            await update.message.reply_text(
                "Invalid format. Please use: XXXXXXXXXXXXXXXX|MM|YYYY|CVV"
            )
            return
        
        cc_number = cc_parts[0].strip()
        month = cc_parts[1].strip()
        year = cc_parts[2].strip()
        cvv = cc_parts[3].strip()
        
        # Validate format
        if not validate_cc_format(cc_number, month, year, cvv):
            await update.message.reply_text(
                "Invalid card details. Please check the format and try again."
            )
            return
        
        # Determine which gateway to use (use stripe by default)
        gateway = "stripe"
        gateway_func = GATEWAYS.get(gateway)
        
        # Use 1 credit
        db.use_credits(user_id, 1)
        
        # Check the card
        status_message = await update.message.reply_text("Checking card, please wait...")
        
        result = gateway_func(cc_number, month, year, cvv)
        success = result.get("success", False)
        
        # Log the check
        db.log_check(user_id, success)
        
        # Format the response
        response = format_check_response(cc_number, month, year, cvv, result, gateway)
        
        await status_message.edit_text(response)
    
    except Exception as e:
        logger.error(f"Error processing CC check: {e}")
        await update.message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )

@require_registration
@require_credits(1)
@check_rate_limit
async def check_with_gateway(update: Update, context: CallbackContext, gateway: str) -> None:
    """Check a card with a specific gateway."""
    # If this is from a command, expect the card in args
    if update.message and context.args:
        card_data = " ".join(context.args)
        await process_cc_check(update, context, card_data)
    else:
        # Send instructions on how to use the gateway
        message = (
            f"To check a card with this gateway, send it in the following format:\n\n"
            f"XXXXXXXXXXXXXXXX|MM|YYYY|CVV\n\n"
            f"Example: 4111111111111111|01|2025|123"
        )
        
        if update.message:
            await update.message.reply_text(message)

def format_check_response(cc: str, month: str, year: str, cvv: str, result: Dict, gateway: str) -> str:
    """
    Format the response from a card check with proper formatting and emojis.
    
    Args:
        cc: Credit card number
        month: Expiry month
        year: Expiry year
        cvv: CVV code
        result: Check result dictionary
        gateway: Gateway name
        
    Returns:
        Formatted response string with emoji indicators
    """
    success = result.get("success", False)
    message = result.get("message", "Unknown result")
    
    # Define status emoji based on result
    status_emoji = "✅" if success else "❌"
    risk_level = result.get("risk_level", "Unknown")
    risk_emoji = {
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🔴",
        "Unknown": "⚪"
    }.get(risk_level, "⚪")
    
    # Format BIN details
    bin_digits = cc[:6]
    
    # Determine card brand icon
    card_brand = "Unknown"
    if "bin_info" in result:
        card_brand = result["bin_info"].get("brand", "Unknown")
    
    brand_emoji = {
        "Visa": "💳",
        "Mastercard": "💳",
        "American Express": "💳",
        "Discover": "💳", 
        "JCB": "💳",
        "Diners Club": "💳",
        "UnionPay": "💳",
        "Unknown": "💳"
    }.get(card_brand, "💳")
    
    # Build nicely formatted header with result banner
    header = f"{'=' * 35}\n"
    header += f"  {brand_emoji} CARD CHECK RESULT: {status_emoji} {'APPROVED' if success else 'DECLINED'}\n"
    header += f"{'=' * 35}\n\n"
    
    # Base response format
    response = header + (
        f"💳 Card: {cc[:6]}xxxxxx{cc[-4:]}\n"
        f"📆 Expiry: {month}/{year}\n"
        f"🔒 CVV: {cvv}\n"
        f"🔄 Gateway: {gateway.upper()}\n"
        f"{status_emoji} Status: {'APPROVED' if success else 'DECLINED'}\n"
        f"📝 Message: {message}\n\n"
    )
    
    # Add extra details if available
    if "bin_info" in result:
        bin_info = result["bin_info"]
        response += (
            f"📊 BIN INFORMATION:\n"
            f"➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            f"🏛️ Bank: {bin_info.get('bank', 'Unknown')}\n"
            f"🌍 Country: {bin_info.get('country', 'Unknown')}\n"
            f"💳 Type: {bin_info.get('type', 'Unknown')}\n"
            f"🏷️ Brand: {bin_info.get('brand', 'Unknown')}\n"
            f"🔰 Category: {bin_info.get('category', 'Unknown')}\n"
        )
    
    # Add timestamps and unique check ID
    import time
    import uuid
    
    check_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    check_id = str(uuid.uuid4())[:8]
    
    footer = (
        f"\n🕒 Checked at: {check_time}\n"
        f"🔑 Check ID: {check_id}\n"
        f"🤖 Checker: VOIDVISA by @amkuush\n"
        f"{'=' * 35}"
    )
    
    return response + footer

@require_registration
async def id_command(update: Update, context: CallbackContext) -> None:
    """Handle the /id command to show user ID."""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your User ID: {user_id}")

@require_registration
async def info_command(update: Update, context: CallbackContext) -> None:
    """Handle the /info command to show user information."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("You are not registered. Use /register to register.")
        return
    
    # Format registration date
    registered_at = time.strftime("%d-%m-%Y", time.localtime(user["registered_at"]))
    
    # Check if premium has expired
    if user["is_premium"] and user["premium_expiry"] < time.time():
        db.update_user(user_id, {"is_premium": False, "premium_expiry": None})
        user["is_premium"] = False
        user["premium_expiry"] = None
    
    # Format premium expiry
    premium_expiry = "N/A"
    if user["is_premium"] and user["premium_expiry"]:
        premium_expiry = time.strftime("%d-%m-%Y", time.localtime(user["premium_expiry"]))
    
    message = (
        f"🔓 User ID: {user_id}\n"
        f"🔒 Profile Link: [Profile Link](tg://user?id={user_id})\n"
        f"🔒 TG Restrictions: False\n"
        f"🔴 TG Scamtag: False\n"
        f"⭐ TG Premium: False\n"
        f"🔶 Status: {'PREMIUM' if user['is_premium'] else 'FREE'}\n"
        f"💰 Credit: {user['credits']}\n"
        f"📝 Plan: {'Premium' if user['is_premium'] else 'N/A'}\n"
        f"📅 Plan Expiry: {premium_expiry}\n"
        f"🔑 Keys Redeemed: {len(user['redeemed_codes'])}\n"
        f"📆 Registered At: {registered_at}\n"
    )
    
    await update.message.reply_text(message)

@require_registration
async def credits_command(update: Update, context: CallbackContext) -> None:
    """Handle the /credits command to show credit balance."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    await update.message.reply_text(
        f"💰 Your current credit balance: {user['credits']} credits\n\n"
        f"Use /howcrd to learn more about the credit system."
    )

@require_registration
async def buy_command(update: Update, context: CallbackContext) -> None:
    """Handle the /buy command to show premium purchase options."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import os
    
    user_id = update.effective_user.id
    
    # Get the host domain
    host_domain = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'
    
    keyboard = [
        [
            InlineKeyboardButton("💠 Basic Tier (1 month)", callback_data=f"buy_basic_{user_id}"),
        ],
        [
            InlineKeyboardButton("🔶 Silver Tier (3 months)", callback_data=f"buy_silver_{user_id}"),
        ],
        [
            InlineKeyboardButton("🌟 Gold Tier (6 months)", callback_data=f"buy_gold_{user_id}"),
        ],
        [
            InlineKeyboardButton("💎 Platinum Tier (12 months)", callback_data=f"buy_platinum_{user_id}"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"❗ Choose what suits best for your needs.\n"
        f"For more details about Premium, type /help command.\n\n",
        reply_markup=reply_markup
    )

@require_registration
async def ping_command(update: Update, context: CallbackContext) -> None:
    """Handle the /ping command to check bot status."""
    await update.message.reply_text(
        f"🟢 Bot is online and operational!\n"
        f"Latency: 0.3s"
    )

@require_registration
@require_credits(1)
@check_rate_limit
async def gen_command(update: Update, context: CallbackContext) -> None:
    """Handle the /gen command to generate random CCs."""
    user_id = update.effective_user.id
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /gen BIN AMOUNT\n"
            "Example: /gen 440393 5"
        )
        return
    
    try:
        bin_prefix = context.args[0]
        amount = int(context.args[1])
        
        # Validate amount
        if amount < 1 or amount > 10:
            await update.message.reply_text("Amount must be between 1 and 10.")
            return
        
        # Use 1 credit
        db.use_credits(user_id, 1)
        
        # Generate cards
        cards = []
        for _ in range(amount):
            card = generate_random_cc(bin_prefix)
            cards.append(f"{card['cc']}|{card['month']}|{card['year']}|{card['cvv']}")
        
        response = "Generated Cards:\n\n" + "\n".join(cards)
        await update.message.reply_text(response)
    
    except ValueError:
        await update.message.reply_text("Invalid arguments. Please provide a valid BIN and amount.")
    except Exception as e:
        logger.error(f"Error in gen_command: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

@require_registration
@require_credits(1)
async def fake_us_command(update: Update, context: CallbackContext, country_code: str = "US") -> None:
    """
    Handle the /fake command to generate a fake address for the specified country.
    
    Args:
        update: Update object
        context: CallbackContext object
        country_code: Two-letter country code (e.g., US, UK, CA, etc.)
    """
    user_id = update.effective_user.id
    
    # Use 1 credit
    db.use_credits(user_id, 1)
    
    # Generate fake address for the specified country
    address = generate_fake_address(country_code)
    
    response = (
        f"📍 Fake {address['country']} Address:\n\n"
        f"👤 Name: {address['name']}\n"
        f"🏠 Address: {address['street']}\n"
        f"🏙️ City: {address['city']}\n"
        f"🏛️ State/Region: {address['state']}\n"
        f"📮 ZIP/Postal Code: {address['zip']}\n"
        f"📱 Phone: {address['phone']}\n"
        f"📧 Email: {address['email']}"
    )
    
    await update.message.reply_text(response)

@require_registration
@require_credits(5)
@check_rate_limit
async def scr_command(update: Update, context: CallbackContext) -> None:
    """Handle the /scr command for CC scraping."""
    user_id = update.effective_user.id
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /scr CHANNEL_USERNAME AMOUNT\n"
            "Example: /scr carding_channel 10"
        )
        return
    
    try:
        channel = context.args[0]
        amount = int(context.args[1])
        
        # Validate amount
        if amount < 1 or amount > 100:
            await update.message.reply_text("Amount must be between 1 and 100.")
            return
        
        # Use 5 credits
        db.use_credits(user_id, 5)
        
        # In a real implementation, this would scrape cards from the channel
        # Here we'll just return a message
        await update.message.reply_text(
            f"Scraping CCs from {channel} is not implemented in this demo version."
        )
    
    except ValueError:
        await update.message.reply_text("Invalid arguments. Please provide a valid channel and amount.")
    except Exception as e:
        logger.error(f"Error in scr_command: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

@require_registration
@require_credits(5)
@check_rate_limit
async def scrbin_command(update: Update, context: CallbackContext) -> None:
    """Handle the /scrbin command for BIN-based CC scraping."""
    # Similar to scr_command but with BIN filtering
    await update.message.reply_text(
        "BIN-based scraping is not implemented in this demo version."
    )

@require_registration
@require_credits(5)
@check_rate_limit
async def scrsk_command(update: Update, context: CallbackContext) -> None:
    """Handle the /scrsk command for SK scraping."""
    # Similar to scr_command but for SK keys
    await update.message.reply_text(
        "SK key scraping is not implemented in this demo version."
    )

@require_registration
async def howcrd_command(update: Update, context: CallbackContext) -> None:
    """Handle the /howcrd command to explain the credit system."""
    await update.message.reply_text(
        f"💰 Credit System Explanation:\n\n"
        f"1. Each new user gets 100 free credits\n"
        f"2. Credits are used for various operations:\n"
        f"   - CC Check: 1 credit\n"
        f"   - Generate CC: 1 credit\n"
        f"   - Fake Address: 1 credit\n"
        f"   - Scraper tools: 5 credits\n\n"
        f"3. Get more credits by:\n"
        f"   - Purchasing premium plans\n"
        f"   - Redeeming gift codes\n"
        f"   - Special promotions\n\n"
        f"Check your balance with /credits"
    )

@require_registration
async def howpm_command(update: Update, context: CallbackContext) -> None:
    """Handle the /howpm command to explain premium benefits."""
    await update.message.reply_text(
        f"💎 Premium Benefits:\n\n"
        f"1. Higher rate limits (30 checks/minute vs 10)\n"
        f"2. Access to all premium gates\n"
        f"3. Priority support\n"
        f"4. Bulk checking capability\n"
        f"5. Advanced BIN lookup\n"
        f"6. Extended history storage\n\n"
        f"Get premium with /buy command"
    )

@require_registration
async def howgp_command(update: Update, context: CallbackContext) -> None:
    """Handle the /howgp command to explain group usage."""
    await update.message.reply_text(
        f"👥 Using the Bot in Groups:\n\n"
        f"1. Add the bot to your group\n"
        f"2. Make the bot an admin with these permissions:\n"
        f"   - Delete messages\n"
        f"   - Pin messages\n\n"
        f"3. Users must be registered individually\n"
        f"4. Credits are tracked per user, not per group\n\n"
        f"Note: Premium features work in groups too"
    )
