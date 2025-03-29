"""
Configuration settings for the HUMBL3 CH3CK4R bot.
"""
import os

# Telegram bot settings
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "VoidViSa_bot")
BOT_NAME = "VoidViSa"
BOT_AUTHOR = "@amkuush"

# Admin user IDs
ADMIN_USER_IDS = [7367527491]  # Your Telegram user ID
if os.getenv("ADMIN_USER_IDS"):
    ADMIN_USER_IDS.extend([int(id) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id])

# Admin username for direct messaging
ADMIN_USERNAME = "amkuush"

# Default credit settings
DEFAULT_CREDITS = 100
CREDITS_PER_CHECK = 1

# Rate limiting
MAX_CHECKS_PER_MINUTE = 10
PREMIUM_MAX_CHECKS_PER_MINUTE = 30

# API keys for gateways
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
ADYEN_API_KEY = os.getenv("ADYEN_API_KEY", "")
ADYEN_MERCHANT_ACCOUNT = os.getenv("ADYEN_MERCHANT_ACCOUNT", "")
BRAINTREE_MERCHANT_ID = os.getenv("BRAINTREE_MERCHANT_ID", "")
BRAINTREE_PUBLIC_KEY = os.getenv("BRAINTREE_PUBLIC_KEY", "")
BRAINTREE_PRIVATE_KEY = os.getenv("BRAINTREE_PRIVATE_KEY", "")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
WORLDPAY_API_KEY = os.getenv("WORLDPAY_API_KEY", "")
CHECKOUT_API_KEY = os.getenv("CHECKOUT_API_KEY", "")
CYBERSOURCE_MERCHANT_ID = os.getenv("CYBERSOURCE_MERCHANT_ID", "")
CYBERSOURCE_API_KEY = os.getenv("CYBERSOURCE_API_KEY", "")
CYBERSOURCE_SECRET_KEY = os.getenv("CYBERSOURCE_SECRET_KEY", "")
SAGEPAY_VENDOR = os.getenv("SAGEPAY_VENDOR", "")
SAGEPAY_KEY = os.getenv("SAGEPAY_KEY", "")
TWOCHECKOUT_API_KEY = os.getenv("TWOCHECKOUT_API_KEY", "")
TWOCHECKOUT_SELLER_ID = os.getenv("TWOCHECKOUT_SELLER_ID", "")
TWOCHECKOUT_SECRET_KEY = os.getenv("TWOCHECKOUT_SECRET_KEY", "")
SITEBASE_API_KEY = os.getenv("SITEBASE_API_KEY", "")
SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN", "")
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY", "")
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD", "")
SHOPIFY_SHOP_NAME = os.getenv("SHOPIFY_SHOP_NAME", "")
KLARNA_USERNAME = os.getenv("KLARNA_USERNAME", "")
KLARNA_PASSWORD = os.getenv("KLARNA_PASSWORD", "")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
PAYSAFE_API_KEY = os.getenv("PAYSAFE_API_KEY", "")
PAYSAFE_USERNAME = os.getenv("PAYSAFE_USERNAME", "")
PAYSAFE_PASSWORD = os.getenv("PAYSAFE_PASSWORD", "")
AUTHORIZE_NET_LOGIN_ID = os.getenv("AUTHORIZE_NET_LOGIN_ID", "")
AUTHORIZE_NET_TRANSACTION_KEY = os.getenv("AUTHORIZE_NET_TRANSACTION_KEY", "")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
MOLLIE_API_KEY = os.getenv("MOLLIE_API_KEY", "")
PAYTM_MERCHANT_ID = os.getenv("PAYTM_MERCHANT_ID", "")
PAYTM_MERCHANT_KEY = os.getenv("PAYTM_MERCHANT_KEY", "")
ADYEN_TEST_API_KEY = os.getenv("ADYEN_TEST_API_KEY", "")
PAYU_MERCHANT_KEY = os.getenv("PAYU_MERCHANT_KEY", "")
PAYU_MERCHANT_SALT = os.getenv("PAYU_MERCHANT_SALT", "")

# Database configuration (using in-memory JSON for simplicity)
DATABASE_FILE = "bot_data.json"

# BIN database file
BIN_DATABASE_FILE = "bin_database.json"
