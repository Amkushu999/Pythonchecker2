"""
Paysafe gateway integration for CC checking.
"""
import json
import logging
import base64
import requests
from typing import Dict, Any, Optional
import uuid

from config import PAYSAFE_API_KEY, PAYSAFE_USERNAME, PAYSAFE_PASSWORD
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class PaysafeGateway(BaseGateway):
    """Paysafe payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Paysafe gateway."""
        super().__init__("Paysafe")
        self.api_url = "https://api.test.paysafe.com/cardpayments/v1"  # Test environment
        # Use basic auth with API key
        if PAYSAFE_API_KEY:
            self.auth_string = base64.b64encode(f"{PAYSAFE_API_KEY}:".encode()).decode('utf-8')
        else:
            # Fall back to username/password if available
            self.auth_string = base64.b64encode(f"{PAYSAFE_USERNAME}:{PAYSAFE_PASSWORD}".encode()).decode('utf-8')
            
        self.headers = {
            "Authorization": f"Basic {self.auth_string}",
            "Content-Type": "application/json"
        }
        
        # Merchant account ID - would normally be configured
        self.merchant_account_id = "MERCHANT_ACCOUNT_ID"
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Paysafe."""
        # First do the basic validation in the parent class
        validation_result = super().check_card(cc_number, month, year, cvv, **kwargs)
        if not validation_result.get("success", False):
            return validation_result
        
        try:
            # Format month as MM with leading zero if needed
            month = month.zfill(2)
            
            # If year is given as YY format, convert to YYYY
            if len(year) == 2:
                year = "20" + year
                
            # Generate a unique merchant reference number
            merchant_ref_num = str(uuid.uuid4())
            
            # Prepare the authentication request
            payload = {
                "merchantRefNum": merchant_ref_num,
                "amount": 100,  # $1.00 for verification
                "settleWithAuth": False,  # Don't settle, just authenticate
                "card": {
                    "cardNum": cc_number,
                    "cardExpiry": {
                        "month": month,
                        "year": year
                    },
                    "cvv": cvv
                },
                "billingDetails": {
                    "street": "100 Queen Street West",
                    "city": "Toronto",
                    "state": "ON",
                    "country": "CA",
                    "zip": "M5H 2N2"
                }
            }
            
            # If Paysafe credentials aren't configured, simulate the check
            if not (PAYSAFE_API_KEY or (PAYSAFE_USERNAME and PAYSAFE_PASSWORD)):
                # Simulate success for test numbers
                if cc_number.startswith(('4111111111111111', '5555555555554444', '378282246310005')):
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, "Test card verification successful with Paysafe", bin_info)
                else:
                    return self.format_response(False, "Card verification failed with Paysafe (simulated)")
            
            # Send authentication request to Paysafe
            url = f"{self.api_url}/accounts/{self.merchant_account_id}/auths"
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code in (200, 201, 202):
                # Card authentication successful
                result = response.json()
                status = result.get("status", "").lower()
                
                if status in ("completed", "pending", "available"):
                    # Card is valid
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, f"Card verification successful with Paysafe (Status: {status})", bin_info)
                else:
                    # Authentication failed
                    error_message = f"Card verification failed with Paysafe (Status: {status})"
                    return self.format_response(False, error_message)
            else:
                # Request failed
                error_message = "Card verification failed with Paysafe"
                if response.text:
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_code = error_data["error"].get("code", "")
                            error_message = f"{error_message}: {error_data['error'].get('message', '')} (Code: {error_code})"
                    except json.JSONDecodeError:
                        pass
                
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in Paysafe gateway: {str(e)}")
            return self.handle_error(e)


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Paysafe gateway."""
    gateway = PaysafeGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)