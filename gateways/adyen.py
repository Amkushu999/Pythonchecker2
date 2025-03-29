"""
Adyen gateway integration for CC checking.
"""
import logging
import json
import requests
from typing import Dict, Any
from gateways.base import BaseGateway
from config import ADYEN_API_KEY, ADYEN_MERCHANT_ACCOUNT
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class AdyenGateway(BaseGateway):
    """Adyen payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Adyen gateway."""
        super().__init__("Adyen")
        self.api_key = ADYEN_API_KEY
        self.merchant_account = ADYEN_MERCHANT_ACCOUNT
        self.api_url = "https://checkout-test.adyen.com/v67/payments"
        self.headers = {
            "x-API-key": self.api_key,
            "content-type": "application/json"
        }
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Adyen."""
        try:
            # Return error if API credentials aren't properly configured
            if not self.api_key or not self.merchant_account:
                return self.format_response(False, "Adyen API credentials not configured")
            
            # Format the expiry date
            expiry_month = month.zfill(2)
            expiry_year = year if len(year) == 4 else f"20{year}"
            
            # Prepare the payload
            payload = {
                "amount": {
                    "currency": "USD",
                    "value": 100  # $1.00
                },
                "reference": f"cc_check_{cc_number[-4:]}",
                "paymentMethod": {
                    "type": "scheme",
                    "encryptedCardNumber": cc_number,
                    "encryptedExpiryMonth": expiry_month,
                    "encryptedExpiryYear": expiry_year,
                    "encryptedSecurityCode": cvv
                },
                "merchantAccount": self.merchant_account,
                "returnUrl": "https://example.com/return",
            }
            
            # Make the API call
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            # Parse the response
            if response.status_code == 200:
                data = response.json()
                result_code = data.get("resultCode", "")
                
                if result_code in ["Authorised", "Received"]:
                    message = "Card is valid and chargeable"
                    success = True
                elif result_code == "RedirectShopper":
                    message = "3D Secure authentication required"
                    success = False
                else:
                    message = f"Card declined: {result_code}"
                    success = False
            else:
                message = f"Gateway error: {response.status_code}"
                success = False
            
            # Get BIN info
            bin_info = lookup_bin(cc_number[:6])
            
            return self.format_response(success, message, bin_info)
        
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Adyen gateway."""
    gateway = AdyenGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)
