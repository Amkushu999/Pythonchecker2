"""
Utility functions for working with payment gateways.
"""
import logging
from typing import Dict, Any, List

# Import API keys configuration
import api_keys

logger = logging.getLogger(__name__)

def check_gateway_keys(gateway: str) -> bool:
    """
    Check if the required API keys are available for a specific gateway.
    
    Args:
        gateway: The name of the gateway to check
        
    Returns:
        True if all required API keys for the gateway are available, False otherwise
    """
    required_keys = {
        'stripe': [api_keys.STRIPE_SECRET_KEY],
        'adyen': [api_keys.ADYEN_API_KEY, api_keys.ADYEN_MERCHANT_ACCOUNT],
        'braintree_b3': [api_keys.BRAINTREE_MERCHANT_ID, api_keys.BRAINTREE_PUBLIC_KEY, api_keys.BRAINTREE_PRIVATE_KEY],
        'braintree_vbv': [api_keys.BRAINTREE_MERCHANT_ID, api_keys.BRAINTREE_PUBLIC_KEY, api_keys.BRAINTREE_PRIVATE_KEY],
        'authnet': [api_keys.AUTHNET_LOGIN_ID, api_keys.AUTHNET_TRANSACTION_KEY],
        'paypal': [api_keys.PAYPAL_CLIENT_ID, api_keys.PAYPAL_CLIENT_SECRET],
        'checkout': [api_keys.CHECKOUT_SECRET_KEY],
        'cybersource': [api_keys.CYBERSOURCE_MERCHANT_ID, api_keys.CYBERSOURCE_API_KEY_ID, api_keys.CYBERSOURCE_SECRET_KEY],
        'shopify': [api_keys.SHOPIFY_API_KEY, api_keys.SHOPIFY_API_SECRET, api_keys.SHOPIFY_SHOP_NAME],
        'worldpay': [api_keys.WORLDPAY_SERVICE_KEY],
        'klarna': [api_keys.KLARNA_USERNAME, api_keys.KLARNA_PASSWORD],
        'mollie': [api_keys.MOLLIE_API_KEY],
        'mercadopago': [api_keys.MERCADOPAGO_ACCESS_TOKEN]
    }
    
    # If gateway not in our list, assume it's not available
    if gateway not in required_keys:
        return False
    
    # Check if all required keys for the gateway are available
    for key in required_keys[gateway]:
        if not key:
            return False
    
    return True

def get_gateway_status() -> Dict[str, bool]:
    """
    Get the status of all supported gateways.
    
    Returns:
        A dictionary with gateway names as keys and their availability status as values
    """
    gateways = [
        'stripe', 'adyen', 'braintree_b3', 'braintree_vbv', 'authnet', 
        'paypal', 'checkout', 'cybersource', 'shopify', 'worldpay', 
        'klarna', 'mollie', 'mercadopago'
    ]
    
    status = {}
    for gateway in gateways:
        status[gateway] = check_gateway_keys(gateway)
    
    return status

def format_unavailable_gateway_response(cc: str, month: str, year: str, cvv: str, gateway: str) -> Dict[str, Any]:
    """
    Format a response for when a gateway is unavailable due to missing API keys.
    
    Args:
        cc: Credit card number
        month: Expiry month
        year: Expiry year
        cvv: CVV code
        gateway: Gateway name
        
    Returns:
        A standard format response dictionary
    """
    bin_info = {
        "bank": "Unknown",
        "country": "Unknown",
        "type": "Unknown",
        "brand": "Unknown",
        "category": "Unknown"
    }
    
    # Try to determine card brand from the first digit
    first_digit = cc[0] if cc else "0"
    
    if first_digit == "4":
        bin_info["brand"] = "Visa"
    elif first_digit == "5":
        bin_info["brand"] = "Mastercard"
    elif first_digit == "3":
        bin_info["brand"] = "American Express"
    elif first_digit == "6":
        bin_info["brand"] = "Discover"
    
    return {
        "success": False,
        "message": f"Gateway '{gateway}' is currently unavailable. API keys have not been configured.",
        "risk_level": "Unknown",
        "bin_info": bin_info
    }