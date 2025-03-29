"""
Worldpay gateway integration for CC checking.
"""
import logging
import os
import requests
import json
from typing import Dict, Any, Optional

from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

# Configure Worldpay credentials
WORLDPAY_SERVICE_KEY = os.getenv("WORLDPAY_SERVICE_KEY", "")
WORLDPAY_CLIENT_KEY = os.getenv("WORLDPAY_CLIENT_KEY", "")
WORLDPAY_ENVIRONMENT = os.getenv("WORLDPAY_ENVIRONMENT", "test").lower()

logger = logging.getLogger(__name__)

class WorldpayGateway(BaseGateway):
    """Worldpay payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Worldpay gateway."""
        super().__init__("Worldpay")
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Worldpay."""
        try:
            # We need API credentials for this to work
            if not WORLDPAY_SERVICE_KEY:
                logger.error("No Worldpay API credentials configured. Cannot proceed with check.")
                return self.format_response(False, "Error: Worldpay API credentials not configured", lookup_bin(cc_number[:6]))
            
            # Define API endpoint based on environment
            if WORLDPAY_ENVIRONMENT == "production":
                api_url = "https://api.worldpay.com/v1/orders"
            else:
                api_url = "https://api.worldpay.com/v1/orders/test"
            
            # Format expiry date
            expiry_month = month.zfill(2)
            expiry_year = year[-2:] if len(year) > 2 else year
            
            # Create the payment request payload
            payload = {
                "token": "",  # We don't have a token
                "orderDescription": "Card Validation Check",
                "amount": 100,  # £1.00 in pence
                "currencyCode": "GBP",
                "name": "CC Validation",
                "customerOrderCode": f"check-{cc_number[-4:]}",
                "orderType": "AUTHORIZATION",
                "paymentMethod": {
                    "type": "Card",
                    "name": "Test Card",
                    "expiryMonth": expiry_month,
                    "expiryYear": expiry_year,
                    "cardNumber": cc_number,
                    "cvc": cvv
                }
            }
            
            # Set up headers
            headers = {
                "Authorization": f"Bearer {WORLDPAY_SERVICE_KEY}",
                "Content-Type": "application/json"
            }
            
            # Make the API request
            response = requests.post(api_url, json=payload, headers=headers)
            
            # Get BIN info
            bin_info = lookup_bin(cc_number[:6])
            
            # Process the response
            if response.status_code == 200:
                response_data = response.json()
                
                # Check payment status
                if "paymentStatus" in response_data:
                    if response_data["paymentStatus"] == "AUTHORIZED":
                        return self.format_response(True, "Card is valid and authorized", bin_info)
                    else:
                        return self.format_response(False, f"Card verification failed: {response_data['paymentStatus']}", bin_info)
                else:
                    return self.format_response(False, "Invalid response from Worldpay", bin_info)
            else:
                # Handle error response
                error_message = "Unknown error"
                
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                    elif "description" in error_data:
                        error_message = error_data["description"]
                except:
                    error_message = f"HTTP error {response.status_code}"
                
                return self.format_response(False, f"Card declined: {error_message}", bin_info)
                
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Worldpay gateway."""
    gateway = WorldpayGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)