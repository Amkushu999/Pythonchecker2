"""
2Checkout gateway integration for CC checking.
"""
import json
import logging
import requests
import hashlib
import time
from typing import Dict, Any, Optional

from config import TWOCHECKOUT_API_KEY, TWOCHECKOUT_SELLER_ID, TWOCHECKOUT_SECRET_KEY
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class TwoCheckoutGateway(BaseGateway):
    """2Checkout payment gateway implementation."""
    
    def __init__(self):
        """Initialize the 2Checkout gateway."""
        super().__init__("2Checkout")
        # Set the API URL - use sandbox for testing
        self.api_url = "https://api.2checkout.com/rest/6.0"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Avangate-Authentication": f"code=\"{TWOCHECKOUT_SELLER_ID}\" date=\"{int(time.time())}\" hash=\"{self._generate_header_hash()}\"",
        }
        
    def _generate_header_hash(self) -> str:
        """
        Generate hash for 2Checkout API authentication header.
        
        Returns:
            Authentication hash string
        """
        timestamp = str(int(time.time()))
        string_to_hash = len(TWOCHECKOUT_SELLER_ID) + TWOCHECKOUT_SELLER_ID + len(timestamp) + timestamp
        return hashlib.md5((string_to_hash + TWOCHECKOUT_SECRET_KEY).encode()).hexdigest()
        
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with 2Checkout."""
        # First do the basic validation in the parent class
        validation_result = super().check_card(cc_number, month, year, cvv, **kwargs)
        if not validation_result.get("success", False):
            return validation_result
        
        try:
            # Format month and year correctly
            month = month.zfill(2)
            
            if len(year) == 2:
                year = "20" + year
            
            # If 2Checkout credentials aren't configured, simulate the check
            if not TWOCHECKOUT_API_KEY or not TWOCHECKOUT_SELLER_ID or not TWOCHECKOUT_SECRET_KEY:
                # Simulate success for test numbers
                if cc_number.startswith(('4111111111111111', '5555555555554444', '378282246310005')):
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, "Test card verification successful with 2Checkout", bin_info)
                else:
                    return self.format_response(False, "Card verification failed with 2Checkout (simulated)")
            
            # Prepare the payment payload
            # Using 2Checkout's Authorize Only API
            payload = {
                "Country": "US",
                "Currency": "USD",
                "CustomerIP": "127.0.0.1",
                "CustomerReference": f"verify_{int(time.time())}",
                "ExternalReference": f"verify_{int(time.time())}",
                "Language": "en",
                "PaymentDetails": {
                    "Type": "TEST",  # Use TEST to avoid actual charges
                    "Currency": "USD",
                    "PaymentMethod": {
                        "CardNumber": cc_number,
                        "CardType": self._detect_card_type(cc_number),
                        "ExpirationMonth": month,
                        "ExpirationYear": year,
                        "CCID": cvv,
                        "HolderName": "Test Customer",
                        "RecurringEnabled": False,
                        "HolderNameTime": 1,
                        "CardNumberTime": 1
                    }
                },
                "BillingDetails": {
                    "Address1": "123 Test St",
                    "City": "Columbus", 
                    "CountryCode": "US",
                    "Email": "test@example.com",
                    "FirstName": "Test",
                    "LastName": "Customer",
                    "Zip": "43210",
                    "State": "OH"
                },
                "Items": [{
                    "Code": "TEST123",
                    "Name": "Credit Card Validation",
                    "Quantity": 1,
                    "Price": {
                        "Amount": 0.01,  # Minimal amount
                        "Type": "CUSTOM"
                    },
                    "Type": "PRODUCT"
                }]
            }
            
            # Make API request to 2Checkout
            response = requests.post(f"{self.api_url}/orders/", 
                                     headers=self.headers, 
                                     json=payload)
            
            if response.status_code in (200, 201):
                # Order created successfully - card is valid
                result = response.json()
                bin_info = lookup_bin(cc_number[:6])
                
                # Check order status
                order_status = result.get("Status")
                if order_status in ("PENDING", "AUTHRECEIVED", "COMPLETE"):
                    return self.format_response(True, f"Card verification successful with 2Checkout (Status: {order_status})", bin_info)
                else:
                    error_message = f"Card verification failed with 2Checkout (Status: {order_status})"
                    return self.format_response(False, error_message)
            else:
                # Request failed
                error_message = "Card verification failed with 2Checkout"
                if response.text:
                    try:
                        error_data = response.json()
                        if "Message" in error_data:
                            error_message = f"{error_message}: {error_data['Message']}"
                        elif "error_msg" in error_data:
                            error_message = f"{error_message}: {error_data['error_msg']}"
                    except json.JSONDecodeError:
                        pass
                
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in 2Checkout gateway: {str(e)}")
            return self.handle_error(e)
    
    def _detect_card_type(self, cc_number: str) -> str:
        """
        Detect the credit card type based on its number pattern.
        
        Args:
            cc_number: The credit card number.
            
        Returns:
            Card type string as expected by 2Checkout.
        """
        # Simplified detection based on common patterns
        if cc_number.startswith('4'):
            return "VISA"
        elif cc_number.startswith(('51', '52', '53', '54', '55')):
            return "MASTERCARD"
        elif cc_number.startswith(('34', '37')):
            return "AMEX"
        elif cc_number.startswith(('300', '301', '302', '303', '304', '305', '36', '38')):
            return "DINERS"
        elif cc_number.startswith(('6011', '644', '645', '646', '647', '648', '649', '65')):
            return "DISCOVER"
        elif cc_number.startswith(('35')):
            return "JCB"
        else:
            return "VISA"  # Default to VISA if pattern not recognized


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with 2Checkout gateway."""
    gateway = TwoCheckoutGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)