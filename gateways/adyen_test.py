"""
Adyen Test gateway integration for CC checking.
"""
import json
import logging
import requests
import uuid
from typing import Dict, Any, Optional

from config import ADYEN_TEST_API_KEY 
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class AdyenTestGateway(BaseGateway):
    """Adyen Test payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Adyen Test gateway."""
        super().__init__("Adyen Test")
        self.api_url = "https://checkout-test.adyen.com/v70"
        self.headers = {
            "x-API-key": ADYEN_TEST_API_KEY,
            "Content-Type": "application/json"
        }
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Adyen Test."""
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
            
            # If Adyen Test API key is not configured, return an error
            if not ADYEN_TEST_API_KEY:
                return self.format_response(False, "Adyen Test API key not configured")
            
            # Generate a unique reference
            merchant_reference = f"check_{uuid.uuid4()}"
            
            # Prepare the payment payload
            payload = {
                "merchantAccount": "YOUR_MERCHANT_ACCOUNT",  # This should be provided by the user
                "amount": {
                    "value": 100,  # 1.00 in minor units
                    "currency": "USD"
                },
                "reference": merchant_reference,
                "paymentMethod": {
                    "type": "scheme",
                    "encryptedCardNumber": cc_number,
                    "encryptedExpiryMonth": month,
                    "encryptedExpiryYear": year,
                    "encryptedSecurityCode": cvv,
                    "holderName": "Test Customer"
                },
                "shopperReference": "test_shopper",
                "shopperEmail": "test@example.com",
                "shopperIP": "127.0.0.1",
                "browserInfo": {
                    "userAgent": "Mozilla/5.0",
                    "acceptHeader": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                },
                "returnUrl": "https://your-company.com/checkout/",
                "billingAddress": {
                    "street": "123 Test Street",
                    "houseNumberOrName": "Apt 1",
                    "city": "Test City",
                    "postalCode": "12345",
                    "country": "US",
                    "stateOrProvince": "CA"
                }
            }
            
            # Make API request to Adyen
            response = requests.post(f"{self.api_url}/payments", 
                                      headers=self.headers, 
                                      json=payload)
            
            if response.status_code == 200:
                result = response.json()
                result_code = result.get("resultCode", "").upper()
                
                if result_code in ("AUTHORISED", "PENDING", "RECEIVED"):
                    # Card passed the check
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, f"Card verification successful with Adyen Test (Status: {result_code})", bin_info)
                elif result_code == "REDIRECTSHOPPER":
                    # Requires further authentication (3D Secure)
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, "Card requires 3D Secure authentication", bin_info)
                else:
                    # Card verification failed
                    refusal_reason = result.get("refusalReason", "Unknown reason")
                    return self.format_response(False, f"Card verification failed with Adyen Test: {refusal_reason}")
            else:
                # Request failed
                error_message = "Card verification failed with Adyen Test"
                if response.text:
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_message = f"{error_message}: {error_data['message']}"
                    except json.JSONDecodeError:
                        pass
                
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in Adyen Test gateway: {str(e)}")
            return self.handle_error(e)


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Adyen Test gateway."""
    gateway = AdyenTestGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)