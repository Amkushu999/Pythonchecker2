"""
PayPal gateway integration for CC checking.
"""
import logging
import requests
import base64
from typing import Dict, Any
from gateways.base import BaseGateway
from config import PAYPAL_CLIENT_ID, PAYPAL_SECRET
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class PayPalGateway(BaseGateway):
    """PayPal payment gateway implementation."""
    
    def __init__(self):
        """Initialize the PayPal gateway."""
        super().__init__("PayPal")
        self.client_id = PAYPAL_CLIENT_ID
        self.client_secret = PAYPAL_SECRET
        self.base_url = "https://api-m.sandbox.paypal.com"
        self.auth_token = self._get_auth_token()
    
    def _get_auth_token(self) -> str:
        """Get OAuth token for PayPal API."""
        if not self.client_id or not self.client_secret:
            logger.warning("PayPal credentials not set. Using simulation mode.")
            return ""
        
        try:
            auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = "grant_type=client_credentials"
            
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                return response.json().get("access_token", "")
            else:
                logger.error(f"Failed to get PayPal auth token: {response.text}")
                return ""
        
        except Exception as e:
            logger.error(f"Error getting PayPal auth token: {e}")
            return ""
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with PayPal."""
        try:
            # Skip the actual API call if we don't have auth token
            if not self.auth_token:
                # Simulate a response based on the card number
                if cc_number.startswith('4') and int(cvv) % 2 == 0:
                    return self.format_response(True, "Card is valid for PayPal", lookup_bin(cc_number[:6]))
                else:
                    return self.format_response(False, "Card declined by PayPal", lookup_bin(cc_number[:6]))
            
            # Format the expiry date
            expiry_month = month.zfill(2)
            expiry_year = year if len(year) == 4 else f"20{year}"
            
            # Create a payment source
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": "USD",
                            "value": "1.00"
                        }
                    }
                ],
                "payment_source": {
                    "card": {
                        "number": cc_number,
                        "expiry": f"{expiry_month}/{expiry_year[-2:]}",
                        "security_code": cvv
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=headers,
                json=payload
            )
            
            # Parse the response
            if response.status_code in [200, 201]:
                data = response.json()
                status = data.get("status", "")
                
                if status == "CREATED":
                    message = "Card is valid for PayPal"
                    success = True
                elif status == "PAYER_ACTION_REQUIRED":
                    message = "3D Secure authentication required"
                    success = False
                else:
                    message = f"Unknown status: {status}"
                    success = False
            else:
                error_details = response.json().get("details", [{}])[0]
                message = f"Card declined: {error_details.get('issue', 'Unknown error')}"
                success = False
            
            # Get BIN info
            bin_info = lookup_bin(cc_number[:6])
            
            return self.format_response(success, message, bin_info)
        
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with PayPal gateway."""
    gateway = PayPalGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)
