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
from config import BOT_USERNAME
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
            InlineKeyboardButton("✨ Commands", callback_data="commands")
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="Close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"<b>💳 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚 𝐂𝐡𝐞𝐜𝐤𝐞𝐫</b>\n"
        f"👋 <b>Hello {update.effective_user.first_name}!</b> Welcome aboard...\n\n"
        f"<i>Explore my various commands and abilities by tapping on the Commands button below</i>"
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")

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
        [InlineKeyboardButton("Back", callback_data="back")],
        [InlineKeyboardButton("Close", callback_data="Close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"<b>💳 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚 Commands Center</b>\n\n"
        f"<i>Explore the various command categories below:</i>\n\n"
        f"1️⃣ <b>AUTH/B3/VBV</b> - Authentication gateways\n"
        f"2️⃣ <b>CHARGE</b> - Charge gateways\n"
        f"3️⃣ <b>TOOLS</b> - Utility tools\n"
        f"4️⃣ <b>HELPER</b> - Help commands\n\n"
        f"<i>Select a category to view available commands.</i>"
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
            InlineKeyboardButton("Klarna Auth", callback_data="klarna"),
            InlineKeyboardButton("Mollie Auth", callback_data="mollie")
        ],
        [
            InlineKeyboardButton("MercadoPago", callback_data="mercadopago"),
            InlineKeyboardButton("Adyen Test", callback_data="adyen_test")
        ],
        [
            InlineKeyboardButton("Back", callback_data="Back"),
            InlineKeyboardButton("Close", callback_data="Close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"<b>🔹 AUTH GATES of 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>\n"
        f"<b>🔹 Status:</b> <code>✅ ACTIVE</code>\n\n"
        f"<b>🚀 Available Commands:</b>\n\n"
        f"<b>👤 Auth Options:</b>\n"
        f"1. Auth: <code>/au cc|mm|yy|cvv</code> ✅\n"
        f"→ Single: <code>/au cc|mm|yy|cvv</code> ✅\n"
        f"→ Mass: <code>/mass cc|mm|yy|cvv</code> ✅\n\n"
        f"<i>Select a gateway button below to check cards with that gateway</i>"
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
            InlineKeyboardButton("Square", callback_data="square"),
            InlineKeyboardButton("Razorpay", callback_data="razorpay")
        ],
        [
            InlineKeyboardButton("PaySafe", callback_data="paysafe"),
            InlineKeyboardButton("PayU", callback_data="payu")
        ],
        [
            InlineKeyboardButton("Back", callback_data="Back"),
            InlineKeyboardButton("Close", callback_data="Close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"<b>🔹 CHARGE GATES of 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>\n"
        f"<b>🔹 Status:</b> <code>✅ ACTIVE</code>\n\n"
        f"<b>🚀 Available Commands:</b>\n\n"
        f"<b>👤 Charge Options:</b>\n"
        f"1. Stripe Charge: <code>/charge cc|mm|yy|cvv</code> ✅\n"
        f"2. Shopify Charge: <code>/shopify cc|mm|yy|cvv</code> ✅\n"
        f"3. WorldPay Charge: <code>/worldpay cc|mm|yy|cvv</code> ✅\n"
        f"4. CyberSource Charge: <code>/cybersource cc|mm|yy|cvv</code> ✅\n\n"
        f"<i>Select a gateway button below to check cards with that gateway</i>"
    )
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_tools(query) -> None:
    """Show available tools."""
    message = (
        f"<b>♦️ Generator Tools of 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>\n"
        f"<b>♦️ Status:</b> <code>✅ ACTIVE</code>\n\n"
        f"<b>🚀 Available Commands:</b>\n\n"
        f"<b>👤 Generator Tools:</b>\n"
        f"1. Random CC Generator: <code>/gen 440393 500</code> ✅ (Limit: 10k)\n"
        f"2. Fake Address Generator: <code>/fakeus</code> ✅\n\n"
        f"<i>Use these tools to generate test data for your checks</i>"
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
    from config import ADMIN_USER_IDS
    
    # Check if user is admin to show admin commands
    is_admin = query.from_user.id in ADMIN_USER_IDS
    
    message = (
        f"<b>♦️ Helper Commands of 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>\n"
        f"<b>♦️ Status:</b> <code>✅ ACTIVE</code>\n\n"
        
        f"<b>👤 Account Management:</b>\n"
        f"1. Start Bot: <code>/start</code> ✅\n"
        f"2. Create Account: <code>/register</code> ✅\n" 
        f"3. User ID: <code>/id</code> ✅\n"
        f"4. Account Info: <code>/info</code> ✅\n"
        f"5. Credit Balance: <code>/credits</code> ✅\n\n"
        
        f"<b>💳 Card Checker Gates:</b>\n"
        f"1. Stripe Gateway: <code>/stripe cc|mm|yy|cvv</code> ✅\n"
        f"2. Adyen Gateway: <code>/adyen cc|mm|yy|cvv</code> ✅\n"
        f"3. Braintree B3: <code>/b3 cc|mm|yy|cvv</code> ✅\n"
        f"4. Braintree VBV: <code>/vbv cc|mm|yy|cvv</code> ✅\n"
        f"5. PayPal Auth: <code>/paypal cc|mm|yy|cvv</code> ✅\n\n"
        
        f"<b>🛠️ Generator Tools:</b>\n"
        f"1. CC Generator: <code>/gen BIN AMOUNT</code> ✅\n"
        f"2. Address Generator: <code>/fake</code> ✅\n"
        f"3. BIN Lookup: <code>/bin 440393</code> ✅\n\n"
        
        f"<b>💎 Premium Features:</b>\n"
        f"1. Buy Premium: <code>/buy</code> ✅\n"
        f"2. Redeem Code: <code>/redeem CODE</code> ✅\n"
        f"3. Premium Info: <code>/howpm</code> ✅\n"
        f"4. Credits System: <code>/howcrd</code> ✅\n\n"
        
        f"<b>📢 Other Commands:</b>\n"
        f"1. Group Usage: <code>/howgp</code> ✅\n"
        f"2. Bot Status: <code>/ping</code> ✅\n\n"
    )
    
    # Add admin commands if user is an admin
    if is_admin:
        message += (
            f"<b>🔑 Admin Commands of 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>\n"
            f"<b>🔑 Status:</b> <code>✅ ACTIVE</code>\n\n"
            
            f"<b>👥 User Management:</b>\n"
            f"1. Add Credits: <code>/addcredits USER_ID AMOUNT</code> ✅\n"
            f"2. Add Premium: <code>/addpremium USER_ID DAYS</code> ✅\n"
            f"3. Ban User: <code>/ban USER_ID REASON</code> ✅\n"
            f"4. Unban User: <code>/unban USER_ID</code> ✅\n"
            f"5. Banned List: <code>/banlist</code> ✅\n\n"
            
            f"<b>⚙️ System Management:</b>\n"
            f"1. Lock System: <code>/lock</code> ✅\n"
            f"2. Unlock System: <code>/unlock</code> ✅\n"
            f"3. Maintenance: <code>/maintenance [on/off]</code> ✅\n"
            f"4. Min Credits: <code>/mincredits AMOUNT</code> ✅\n\n"
            
            f"<b>👥 Group Management:</b>\n"
            f"1. Add Group: <code>/addgroup GROUP_ID</code> ✅\n"
            f"2. Remove Group: <code>/removegroup GROUP_ID</code> ✅\n"
            f"3. Group List: <code>/grouplist</code> ✅\n\n"
            
            f"<b>🛠️ Other Tools:</b>\n"
            f"1. Generate Code: <code>/gencode CREDITS DAYS</code> ✅\n"
            f"2. System Stats: <code>/stats</code> ✅\n"
            f"3. Broadcast: <code>/broadcast MESSAGE</code> ✅\n\n"
        )
    
    message += f"<i>Use these commands to manage your account and get help</i>"
    
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
        f"<b>🔹 {gateway_name} Gate of 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>\n"
        f"<b>🔹 Status:</b> <code>✅ ACTIVE</code>\n\n"
        f"<b>FORMAT INSTRUCTIONS</b>\n\n"
        f"<b>• Format:</b> <code>XXXXXXXXXXXXXXXX|MM|YYYY|CVV</code>\n"
        f"<b>• Example:</b> <code>4111111111111111|01|2025|123</code>\n\n"
        f"<b>USAGE OPTIONS</b>\n\n"
        f"<b>• Command:</b> <code>/{gateway.split('_')[0]} cc|mm|yy|cvv</code>\n"
        f"<b>• Direct:</b> Simply send the card in the format above\n\n"
        f"<b>• Cost:</b> 1 credit per check\n"
        f"<b>• Status:</b> ✅ Working\n\n"
        f"<i>Results will be displayed with BIN information</i>"
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
        
        await status_message.edit_text(response, parse_mode="HTML")
    
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
    
    # If this is from a command, expect the card in args
    if update.message and context.args:
        card_data = " ".join(context.args)
        await process_cc_check(update, context, card_data)
    else:
        # Send instructions on how to use the gateway
        message = (
            f"<b>🔹 {gateway_name} Gate of 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>\n"
            f"<b>🔹 Status:</b> <code>✅ ACTIVE</code>\n\n"
            f"<b>FORMAT INSTRUCTIONS</b>\n\n"
            f"<b>• Format:</b> <code>XXXXXXXXXXXXXXXX|MM|YYYY|CVV</code>\n"
            f"<b>• Example:</b> <code>4111111111111111|01|2025|123</code>\n\n"
            f"<b>USAGE OPTIONS</b>\n\n"
            f"<b>• Command:</b> <code>/{gateway.split('_')[0]} cc|mm|yy|cvv</code>\n"
            f"<b>• Direct:</b> Simply send the card in the format above\n\n"
            f"<b>• Cost:</b> 1 credit per check\n"
            f"<b>• Status:</b> ✅ Working\n\n"
            f"<i>Simply reply with your card in the correct format</i>"
        )
        
        if update.message:
            await update.message.reply_text(message, parse_mode="HTML")

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
    
    # Build modern formatted response with HTML styling
    status_text = "APPROVED" if success else "DECLINED"
    
    # Base response format with branding at top
    response = (
        f"<b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>        <code>CC CHECKER</code>\n\n"
        f"{status_emoji} <b>{status_text}</b>\n\n"
        f"<b>• Card:</b> {cc[:6]}xxxxxx{cc[-4:]}\n"
        f"<b>• Expiry:</b> {month}/{year}\n"
        f"<b>• CVV:</b> {cvv}\n"
        f"<b>• Gateway:</b> {gateway.upper()}\n"
        f"<b>• Result:</b> {message}\n\n"
    )
    
    # Add extra details if available
    if "bin_info" in result:
        bin_info = result["bin_info"]
        response += (
            f"<b>━━━ BIN INFO ━━━</b>\n\n"
            f"<b>• Bank:</b> {bin_info.get('bank', 'Unknown')}\n"
            f"<b>• Country:</b> {bin_info.get('country', 'Unknown')}\n"
            f"<b>• Type:</b> {bin_info.get('type', 'Unknown')}\n"
            f"<b>• Brand:</b> {bin_info.get('brand', 'Unknown')}\n"
            f"<b>• Category:</b> {bin_info.get('category', 'Unknown')}\n\n"
        )
    
    # Add timestamps and unique check ID
    import time
    import uuid
    
    check_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    check_id = str(uuid.uuid4())[:8]
    
    footer = (
        f"<b>━━━ INFO ━━━</b>\n\n"
        f"<b>• Time:</b> {check_time}\n"
        f"<b>• ID:</b> {check_id}\n"
        f"<b>• Bot:</b> @VoidViSaBot"
    )
    
    return response + footer

@require_registration
async def id_command(update: Update, context: CallbackContext) -> None:
    """Handle the /id command to show user ID."""
    user_id = update.effective_user.id
    
    message = (
        f"<b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>        <code>INFO</code>\n\n"
        f"<b>USER ID</b>\n\n"
        f"<code>{user_id}</code>\n\n"
        f"<i>This is your unique user identifier in the system</i>"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")

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
    
    # Get username if available
    username = update.effective_user.username or "None"
    
    # Format message with new style
    message = (
        f"<b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>        <code>USER INFO</code>\n\n"
        f"<b>ACCOUNT DETAILS</b>\n\n"
        f"<b>• User ID:</b> <code>{user_id}</code>\n"
        f"<b>• Username:</b> @{username}\n"
        f"<b>• Status:</b> {'PREMIUM 💎' if user['is_premium'] else 'FREE'}\n"
        f"<b>• Credits:</b> {user['credits']}\n"
        f"<b>• Joined:</b> {registered_at}\n\n"
        
        f"<b>PREMIUM INFO</b>\n\n"
        f"<b>• Plan:</b> {'Premium' if user['is_premium'] else 'N/A'}\n"
        f"<b>• Expires:</b> {premium_expiry}\n"
        f"<b>• Codes Used:</b> {len(user['redeemed_codes'])}\n\n"
        
        f"<i>Use /credits to check your balance</i>"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")

@require_registration
async def credits_command(update: Update, context: CallbackContext) -> None:
    """Handle the /credits command to show credit balance."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    message = (
        f"<b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>        <code>BALANCE</code>\n\n"
        f"<b>CREDIT BALANCE</b>\n\n"
        f"<b>• Current Balance:</b> <code>{user['credits']}</code> credits\n\n"
        f"<b>PRICING INFO</b>\n\n"
        f"<b>• CC Check:</b> 1 credit\n"
        f"<b>• Address Generate:</b> 1 credit\n"
        f"<b>• CC Generate:</b> 1 credit\n"
        f"<b>• Scraping Tools:</b> 5 credits\n\n"
        f"<i>Use /buy to purchase premium access</i>"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")

@require_registration
async def buy_command(update: Update, context: CallbackContext) -> None:
    """Handle the /buy command to show premium purchase options."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import os
    
    user_id = update.effective_user.id
    
    # Define plan details
    plan_details = {
        "basic": {"name": "Basic Tier", "duration": 1, "price": 9.99},
        "silver": {"name": "Silver Tier", "duration": 3, "price": 24.99},
        "gold": {"name": "Gold Tier", "duration": 6, "price": 44.99},
        "platinum": {"name": "Platinum Tier", "duration": 12, "price": 79.99}
    }
    
    # Create premium plans message
    message = (
        f"<b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>        <code>PREMIUM PLANS</code>\n\n"
        f"<b>PREMIUM SUBSCRIPTION OPTIONS</b>\n\n"
        
        f"<b>💠 BASIC - 1 MONTH</b>\n"
        f"<b>• Price:</b> <code>${plan_details['basic']['price']}</code>\n"
        f"<b>• Features:</b>\n"
        f"  - Unlimited private checks\n"
        f"  - All gateway access\n"
        f"  - Higher limits\n\n"
        
        f"<b>🔶 SILVER - 3 MONTHS</b>\n"
        f"<b>• Price:</b> <code>${plan_details['silver']['price']} (15% discount)</code>\n"
        f"<b>• Features:</b>\n"
        f"  - All Basic features\n"
        f"  - Priority support\n"
        f"  - Bulk checking\n\n"
        
        f"<b>🌟 GOLD - 6 MONTHS</b>\n"
        f"<b>• Price:</b> <code>${plan_details['gold']['price']} (25% discount)</code>\n"
        f"<b>• Features:</b>\n"
        f"  - All Silver features\n"
        f"  - Extended history\n"
        f"  - Gateway updates\n\n"
        
        f"<b>💎 PLATINUM - 12 MONTHS</b>\n"
        f"<b>• Price:</b> <code>${plan_details['platinum']['price']} (33% discount)</code>\n"
        f"<b>• Features:</b>\n"
        f"  - All Gold features\n"
        f"  - Early new features\n"
        f"  - Advanced BIN lookup\n\n"
        
        f"<i>Click a plan below to purchase:</i>"
    )
    
    # Get admin username from config
    from config import ADMIN_USERNAME
    
    # Create contact button
    keyboard = [
        [
            InlineKeyboardButton("💠 Basic (1 month)", callback_data=f"buy_basic_{user_id}"),
            InlineKeyboardButton("🔶 Silver (3 months)", callback_data=f"buy_silver_{user_id}"),
        ],
        [
            InlineKeyboardButton("🌟 Gold (6 months)", callback_data=f"buy_gold_{user_id}"),
            InlineKeyboardButton("💎 Platinum (12 months)", callback_data=f"buy_platinum_{user_id}"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

@require_registration
async def process_payment(query, plan: str, user_id: int) -> None:
    """
    Process payment for premium subscription by directing users to contact the admin.
    
    Args:
        query: Callback query
        plan: Subscription plan (basic, silver, gold, platinum)
        user_id: User ID
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    import uuid
    
    # Define plan details
    plan_details = {
        "basic": {"name": "Basic Tier", "duration": 1, "price": 9.99},
        "silver": {"name": "Silver Tier", "duration": 3, "price": 24.99},
        "gold": {"name": "Gold Tier", "duration": 6, "price": 44.99},
        "platinum": {"name": "Platinum Tier", "duration": 12, "price": 79.99}
    }
    
    if plan not in plan_details:
        await query.message.reply_text("Invalid subscription plan selected.")
        return
    
    # Get plan information
    selected_plan = plan_details[plan]
    
    # Generate a unique reference ID for this transaction
    reference_id = str(uuid.uuid4())[:8]
    
    # Get admin username from config
    from config import ADMIN_USERNAME
    
    # Create payment message with plan details and admin contact info
    message = (
        f"🛒 <b>{selected_plan['name']} Subscription</b>\n\n"
        f"💲 <b>Price:</b> ${selected_plan['price']}\n"
        f"⏱️ <b>Duration:</b> {selected_plan['duration']} {'month' if selected_plan['duration'] == 1 else 'months'}\n"
        f"🔑 <b>Reference:</b> {reference_id}\n\n"
        f"<b>How to purchase:</b>\n"
        f"1. Click the button below to message the admin directly\n"
        f"2. Include the reference number and selected plan in your message\n"
        f"3. The admin will provide payment instructions\n"
        f"4. After payment confirmation, your premium status will be activated\n\n"
        f"<i>Example message:</i>\n"
        f"<code>I want to buy {selected_plan['name']} (Ref: {reference_id})</code>"
    )
    
    # Create contact admin button with hardcoded username per request
    keyboard = [
        [InlineKeyboardButton("💬 Contact Admin", url=f"https://t.me/amkuush?start=buy_{plan}_{reference_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="HTML")

async def ping_command(update: Update, context: CallbackContext) -> None:
    """Handle the /ping command to check bot status."""
    import time
    start_time = time.time()
    message = await update.message.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 2)  # Convert to ms with 2 decimal places
    
    # Format as shown in the screenshot
    await message.edit_text(
        f"🤖 Bot Name: HUMBL3 CH3CK4R\n"
        f"✅ Bot Status: Running\n" 
        f"📊 Ping: {ping_time} ms"
    )

@require_registration
@require_credits(1)
@check_rate_limit
async def gen_command(update: Update, context: CallbackContext) -> None:
    """Handle the /gen command to generate random CCs."""
    user_id = update.effective_user.id
    
    # Define valid bin prefixes for default generation
    valid_bins = ["401234", "402345", "403456", "441234", "511234", "521234", "531234", "551234", "601234", "651234", "371234", "391234"]
    
    try:
        # Default to 10 cards with random BINs if no arguments provided
        if not context.args:
            bin_prefix = ""
            amount = 10
        # If only one argument, treat it as the BIN and default to 10 cards
        elif len(context.args) == 1:
            bin_prefix = context.args[0]
            amount = 10
        # If both arguments provided
        else:
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
        
        # If no BIN provided, use 10 different valid BINs
        if not bin_prefix:
            for i in range(min(amount, len(valid_bins))):
                card = generate_random_cc(valid_bins[i])
                cards.append(f"{card['cc']}|{card['month']}|{card['year']}|{card['cvv']}")
        # Otherwise generate cards with the specified BIN
        else:
            for _ in range(amount):
                card = generate_random_cc(bin_prefix)
                cards.append(f"{card['cc']}|{card['month']}|{card['year']}|{card['cvv']}")
        
        # Format in the styled way matching other commands
        response = (
            f"<b>♦️ CC Generator of HUMBL3 CH3CK4R</b>\n"
            f"<b>♦️ Status:</b> <code>✅ ACTIVE</code>\n\n"
            f"<b>GENERATED CARDS:</b>\n\n"
        )
        
        # Add each card with formatting
        for i, card in enumerate(cards, 1):
            response += f"<code>{i}. {card}</code>\n"
        
        response += f"\n<b>• Generated:</b> {amount} cards\n"
        response += f"<b>• Credits used:</b> 1\n"
        response += f"<b>• Status:</b> ✅ Success\n\n"
        response += f"<i>Use a card with any gateway by sending it directly</i>"
        
        await update.message.reply_text(response, parse_mode="HTML")
    
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
        f"<b>♦️ Address Generator of HUMBL3 CH3CK4R</b>\n"
        f"<b>♦️ Status:</b> <code>✅ ACTIVE</code>\n\n"
        f"<b>GENERATED {address['country']} ADDRESS</b>\n\n"
        f"<b>• Name:</b> {address['name']}\n"
        f"<b>• Street:</b> {address['street']}\n"
        f"<b>• City:</b> {address['city']}\n"
        f"<b>• State:</b> {address['state']}\n"
        f"<b>• ZIP:</b> {address['zip']}\n"
        f"<b>• Phone:</b> {address['phone']}\n"
        f"<b>• Email:</b> {address['email']}\n\n"
        f"<b>• Country:</b> {address['country']}\n"
        f"<b>• Credits used:</b> 1\n"
        f"<b>• Status:</b> ✅ Success\n\n"
        f"<i>Use this address with any payment gateway</i>"
    )
    
    await update.message.reply_text(response, parse_mode="HTML")

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
    message = (
        f"<b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>        <code>CREDIT SYSTEM</code>\n\n"
        f"<b>HOW CREDITS WORK</b>\n\n"
        f"<b>• Initial Credits:</b> Each new user gets 100 free credits\n"
        f"<b>• Free Limit:</b> When credits run out, use bot in groups\n"
        f"<b>• Premium:</b> Unlimited private usage for premium users\n\n"
        
        f"<b>CREDIT COSTS</b>\n\n"
        f"<b>• CC Check:</b> 1 credit per card check\n"
        f"<b>• CC Generate:</b> 1 credit per generation\n"
        f"<b>• Address Gen:</b> 1 credit per address\n"
        f"<b>• Scraper Tools:</b> 5 credits per use\n\n"
        
        f"<b>GET MORE CREDITS</b>\n\n"
        f"<b>• Buy Premium:</b> Use /buy command\n"
        f"<b>• Redeem Codes:</b> Use /redeem CODE\n"
        f"<b>• Invite Friends:</b> Share with others\n\n"
        
        f"<i>Check your balance with /credits</i>"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")

@require_registration
async def howpm_command(update: Update, context: CallbackContext) -> None:
    """Handle the /howpm command to explain premium benefits."""
    message = (
        f"<b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>        <code>PREMIUM</code>\n\n"
        f"<b>PREMIUM BENEFITS</b>\n\n"
        f"<b>• Unlimited Access:</b> Use privately without credit limits\n"
        f"<b>• Higher Limits:</b> 30 checks/minute (vs 10 for free)\n"
        f"<b>• All Gateways:</b> Access to premium gateways\n\n"
        
        f"<b>ADVANCED FEATURES</b>\n\n"
        f"<b>• Priority Support:</b> Get help faster\n"
        f"<b>• Bulk Checking:</b> Check multiple cards at once\n"
        f"<b>• Advanced BIN:</b> Detailed BIN lookups\n"
        f"<b>• History:</b> Extended check history\n\n"
        
        f"<b>PREMIUM PLANS</b>\n\n"
        f"<b>• Basic:</b> $9.99/month\n"
        f"<b>• Silver:</b> $24.99/3 months (save 15%)\n"
        f"<b>• Gold:</b> $44.99/6 months (save 25%)\n"
        f"<b>• Platinum:</b> $79.99/year (save 33%)\n\n"
        
        f"<i>Use /buy to purchase premium access</i>"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")

@require_registration
async def howgp_command(update: Update, context: CallbackContext) -> None:
    """Handle the /howgp command to explain group usage."""
    message = (
        f"<b>𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚</b>        <code>GROUP USAGE</code>\n\n"
        f"<b>ADDING BOT TO GROUP</b>\n\n"
        f"<b>• Step 1:</b> Add @{BOT_USERNAME} to your group\n"
        f"<b>• Step 2:</b> Make the bot an admin\n"
        f"<b>• Step 3:</b> Required permissions:\n"
        f"  - Delete Messages\n"
        f"  - Pin Messages\n\n"
        
        f"<b>GROUP RULES</b>\n\n"
        f"<b>• Registration:</b> Users must register individually\n"
        f"<b>• Free Access:</b> Users can use bot when out of credits\n"
        f"<b>• Credits:</b> Credits tracked per individual user\n"
        f"<b>• Premium:</b> Premium features work in groups\n\n"
        
        f"<b>GROUP BENEFITS</b>\n\n"
        f"<b>• Public Access:</b> All members can use the bot\n"
        f"<b>• New Members:</b> Automatic welcome & registration\n"
        f"<b>• Community:</b> Share results with the group\n\n"
        
        f"<i>Need help? Contact @amkuush</i>"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")
