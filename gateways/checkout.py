"""
Checkout.com gateway integration for CC checking.
"""
import logging
import os
import requests
import json
from typing import Dict, Any, Optional

from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

# Configure Checkout.com credentials
CHECKOUT_SECRET_KEY = os.getenv("CHECKOUT_SECRET_KEY", "")
CHECKOUT_PUBLIC_KEY = os.getenv("CHECKOUT_PUBLIC_KEY", "")
CHECKOUT_ENVIRONMENT = os.getenv("CHECKOUT_ENVIRONMENT", "sandbox").lower()

logger = logging.getLogger(__name__)

class CheckoutGateway(BaseGateway):
    """Checkout.com payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Checkout.com gateway."""
        super().__init__("Checkout.com")
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Checkout.com."""
        try:
            # We need API credentials for this to work
            if not CHECKOUT_SECRET_KEY:
                logger.error("No Checkout.com API credentials configured. Cannot proceed with check.")
                return self.format_response(False, "Error: Checkout.com API credentials not configured", lookup_bin(cc_number[:6]))
            
            # Define API endpoint based on environment
            if CHECKOUT_ENVIRONMENT == "production":
                api_url = "https://api.checkout.com/payments"
            else:
                api_url = "https://api.sandbox.checkout.com/payments"
            
            # Format expiry date
            expiry_month = month.zfill(2)
            expiry_year = year.zfill(4) if len(year) <= 2 else year
            
            # Create the payment request payload
            payload = {
                "source": {
                    "type": "card",
                    "number": cc_number,
                    "expiry_month": int(expiry_month),
                    "expiry_year": int(expiry_year),
                    "cvv": cvv
                },
                "amount": 100,  # £1.00 in pence
                "currency": "GBP",
                "capture": False,  # Auth only, no capture
                "reference": f"cc-check-{cc_number[-4:]}",
                "description": "Card Validation Check"
            }
            
            # Set up headers
            headers = {
                "Authorization": f"Bearer {CHECKOUT_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            # Make the API request
            response = requests.post(api_url, json=payload, headers=headers)
            
            # Get BIN info
            bin_info = lookup_bin(cc_number[:6])
            
            # Process the response
            if response.status_code in (200, 201):
                response_data = response.json()
                
                # Check payment status
                if "approved" in response_data:
                    if response_data["approved"]:
                        return self.format_response(True, "Card is valid and authorized", bin_info)
                    else:
                        reason = response_data.get("response_summary", "Card declined")
                        return self.format_response(False, f"Card declined: {reason}", bin_info)
                else:
                    return self.format_response(False, "Invalid response from Checkout.com", bin_info)
            else:
                # Handle error response
                error_message = "Unknown error"
                
                try:
                    error_data = response.json()
                    if "error_type" in error_data:
                        error_message = f"{error_data['error_type']}: {error_data.get('error_codes', ['Unknown'])[0]}"
                    elif "response_summary" in error_data:
                        error_message = error_data["response_summary"]
                except:
                    error_message = f"HTTP error {response.status_code}"
                
                return self.format_response(False, f"Card declined: {error_message}", bin_info)
                
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Checkout.com gateway."""
    gateway = CheckoutGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)