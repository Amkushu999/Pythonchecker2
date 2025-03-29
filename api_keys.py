"""
API keys configuration for various payment gateways.
These values should be replaced with actual API keys for the gateways to function properly.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

# Adyen configuration
ADYEN_API_KEY = os.environ.get('ADYEN_API_KEY')
ADYEN_MERCHANT_ACCOUNT = os.environ.get('ADYEN_MERCHANT_ACCOUNT')
ADYEN_CLIENT_KEY = os.environ.get('ADYEN_CLIENT_KEY')

# Braintree configuration
BRAINTREE_MERCHANT_ID = os.environ.get('BRAINTREE_MERCHANT_ID')
BRAINTREE_PUBLIC_KEY = os.environ.get('BRAINTREE_PUBLIC_KEY')
BRAINTREE_PRIVATE_KEY = os.environ.get('BRAINTREE_PRIVATE_KEY')
BRAINTREE_ENVIRONMENT = os.environ.get('BRAINTREE_ENVIRONMENT', 'sandbox')

# Authorize.Net configuration
AUTHNET_LOGIN_ID = os.environ.get('AUTHNET_LOGIN_ID')
AUTHNET_TRANSACTION_KEY = os.environ.get('AUTHNET_TRANSACTION_KEY')
AUTHNET_ENVIRONMENT = os.environ.get('AUTHNET_ENVIRONMENT', 'sandbox')

# PayPal configuration
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
PAYPAL_ENVIRONMENT = os.environ.get('PAYPAL_ENVIRONMENT', 'sandbox')

# Checkout.com configuration
CHECKOUT_SECRET_KEY = os.environ.get('CHECKOUT_SECRET_KEY')
CHECKOUT_PUBLIC_KEY = os.environ.get('CHECKOUT_PUBLIC_KEY')

# CyberSource configuration
CYBERSOURCE_MERCHANT_ID = os.environ.get('CYBERSOURCE_MERCHANT_ID')
CYBERSOURCE_API_KEY_ID = os.environ.get('CYBERSOURCE_API_KEY_ID')
CYBERSOURCE_SECRET_KEY = os.environ.get('CYBERSOURCE_SECRET_KEY')

# Shopify configuration
SHOPIFY_API_KEY = os.environ.get('SHOPIFY_API_KEY')
SHOPIFY_API_SECRET = os.environ.get('SHOPIFY_API_SECRET')
SHOPIFY_SHOP_NAME = os.environ.get('SHOPIFY_SHOP_NAME')

# Worldpay configuration
WORLDPAY_SERVICE_KEY = os.environ.get('WORLDPAY_SERVICE_KEY')
WORLDPAY_CLIENT_KEY = os.environ.get('WORLDPAY_CLIENT_KEY')

# Klarna configuration
KLARNA_USERNAME = os.environ.get('KLARNA_USERNAME')
KLARNA_PASSWORD = os.environ.get('KLARNA_PASSWORD')
KLARNA_ENVIRONMENT = os.environ.get('KLARNA_ENVIRONMENT', 'playground')

# Mollie configuration
MOLLIE_API_KEY = os.environ.get('MOLLIE_API_KEY')

# MercadoPago configuration
MERCADOPAGO_ACCESS_TOKEN = os.environ.get('MERCADOPAGO_ACCESS_TOKEN')

# BIN database API keys
BIN_LOOKUP_API_KEY = os.environ.get('BIN_LOOKUP_API_KEY')