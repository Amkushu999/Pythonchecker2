"""
PayU gateway integration for CC checking.
"""
import json
import logging
import hashlib
import requests
import uuid
import time
from typing import Dict, Any, Optional

from config import PAYU_MERCHANT_KEY, PAYU_MERCHANT_SALT
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class PayUGateway(BaseGateway):
    """PayU payment gateway implementation."""
    
    def __init__(self):
        """Initialize the PayU gateway."""
        super().__init__("PayU")
        # Use test/sandbox API URL
        self.api_url = "https://test.payu.in/_payment"
        self.merchant_key = PAYU_MERCHANT_KEY
        self.merchant_salt = PAYU_MERCHANT_SALT
        self.surl = "https://example.com/success"  # Success URL
        self.furl = "https://example.com/failure"  # Failure URL
        
    def _generate_hash(self, data: Dict[str, Any]) -> str:
        """
        Generate PayU hash for request authentication.
        
        Args:
            data: Dictionary of request parameters
            
        Returns:
            Hash string
        """
        # The hash string format is specific to PayU
        hash_string = (
            f"{self.merchant_key}|{data['txnid']}|{data['amount']}|{data['productinfo']}|"
            f"{data['firstname']}|{data['email']}|||||||||||{self.merchant_salt}"
        )
        
        # Generate SHA512 hash
        return hashlib.sha512(hash_string.encode()).hexdigest()
        
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with PayU."""
        # First do the basic validation in the parent class
        validation_result = super().check_card(cc_number, month, year, cvv, **kwargs)
        if not validation_result.get("success", False):
            return validation_result
        
        try:
            # Format month and year correctly
            month = month.zfill(2)
            
            if len(year) == 2:
                year = "20" + year
                
            # Generate a unique transaction ID
            txn_id = f"TXN_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            
            # If PayU credentials aren't configured, return an error
            if not PAYU_MERCHANT_KEY or not PAYU_MERCHANT_SALT:
                return self.format_response(False, "PayU API credentials not configured")
            
            # Prepare the payment payload
            payload = {
                "key": self.merchant_key,
                "txnid": txn_id,
                "amount": "1.00",  # Minimal amount for verification
                "productinfo": "Card Verification",
                "firstname": "Test",
                "lastname": "Customer",
                "email": "test@example.com",
                "phone": "9999999999",
                "address1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "country": "Test Country",
                "zipcode": "123456",
                "surl": self.surl,
                "furl": self.furl,
                "pg": "CC",  # Credit Card payment mode
                # Card details
                "bankcode": self._detect_card_type(cc_number),
                "ccnum": cc_number,
                "ccvv": cvv,
                "ccname": "Test Customer",
                "ccexpmon": month,
                "ccexpyr": year[-2:],  # PayU expects YY format
            }
            
            # Generate hash
            payload["hash"] = self._generate_hash(payload)
            
            # Make API request to PayU
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Note: In a real implementation, this would typically be a form POST from the browser
            # For verification purposes, we're making a direct API call
            response = requests.post(self.api_url, 
                                     headers=headers, 
                                     data=payload)
            
            # PayU typically responds with a redirect to a payment page or a response page
            # For card verification, we're checking if the request was accepted by the gateway
            if response.status_code in (200, 302):
                # Check if response contains error messages
                response_text = response.text.lower()
                
                if "error" in response_text or "invalid" in response_text:
                    error_message = "Card verification failed with PayU"
                    return self.format_response(False, error_message)
                    
                # For verification purposes, assume success if no clear error is found
                bin_info = lookup_bin(cc_number[:6])
                return self.format_response(True, "Card verification initiated with PayU", bin_info)
            else:
                # Request failed
                error_message = "Card verification failed with PayU"
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in PayU gateway: {str(e)}")
            return self.handle_error(e)
    
    def _detect_card_type(self, cc_number: str) -> str:
        """
        Detect the credit card type based on its number pattern.
        
        Args:
            cc_number: The credit card number.
            
        Returns:
            Card type code as expected by PayU.
        """
        # Simplified detection based on common patterns
        if cc_number.startswith('4'):
            return "VISA"
        elif cc_number.startswith(('51', '52', '53', '54', '55')):
            return "MAST"  # MasterCard
        elif cc_number.startswith(('34', '37')):
            return "AMEX"
        elif cc_number.startswith(('300', '301', '302', '303', '304', '305', '36', '38')):
            return "DINR"  # Diners
        elif cc_number.startswith(('6011', '644', '645', '646', '647', '648', '649', '65')):
            return "DISC"  # Discover
        elif cc_number.startswith(('35')):
            return "JCB"
        else:
            return "VISA"  # Default to VISA if pattern not recognized


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with PayU gateway."""
    gateway = PayUGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)