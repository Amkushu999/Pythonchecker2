"""
PayU gateway integration for CC checking.
"""
import os
import time
import json
import random
import requests
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from api_keys import PAYU_MERCHANT_KEY, PAYU_MERCHANT_SALT
from gateways.base import BaseGateway
from utils.bin_lookup import get_bin_info

class PayUGateway(BaseGateway):
    """PayU payment gateway implementation."""

    def __init__(self):
        """Initialize the PayU gateway."""
        super().__init__("PayU")
        self.merchant_key = PAYU_MERCHANT_KEY
        self.merchant_salt = PAYU_MERCHANT_SALT
        self.api_base_url = "https://secure.payu.com"
        self.api_version = "api"

    def _generate_hash(self, data_dict: Dict) -> str:
        """Generate a hash for PayU API request."""
        # Keys to be included in the hash, in the correct order
        hash_sequence = ["key", "txnid", "amount", "productinfo", "firstname", "email"]
        
        # Start with empty hash string
        hash_string = ""
        
        # Add each value from the sequence
        for key in hash_sequence:
            hash_string += str(data_dict.get(key, ""))
            hash_string += "|"
        
        # Add the salt
        hash_string += self.merchant_salt
        
        # Create the hash using SHA512
        return hashlib.sha512(hash_string.encode('utf-8')).hexdigest()

    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with PayU."""
        # Call the parent method to validate card format first
        validation_result = super().check_card(cc_number, month, year, cvv)
        if not validation_result["success"]:
            return validation_result

        # If we don't have API keys, return a message
        if not self.merchant_key or not self.merchant_salt or self.merchant_key == "your_payu_merchant_key_here":
            return self.format_response(
                False,
                "PayU API credentials are not set. Please configure your merchant key and salt.",
                get_bin_info(cc_number[:6])
            )

        try:
            # Prepare a unique transaction ID
            txn_id = f"TXN{int(time.time())}{random.randint(1000, 9999)}"
            
            # Prepare required parameters for PayU
            data = {
                "key": self.merchant_key,
                "txnid": txn_id,
                "amount": "1.00",
                "productinfo": "Card Verification",
                "firstname": "Test",
                "email": "test@example.com",
                "phone": "1234567890",
                "surl": "https://www.merchant.com/success",
                "furl": "https://www.merchant.com/failure",
                "pg": "CC",
                "bankcode": "",
                "ccnum": cc_number,
                "ccname": "Test User",
                "ccvv": cvv,
                "ccexpmon": month.zfill(2),
                "ccexpyr": year if len(year) == 4 else f"20{year}",
                "enforce_paymethod": "creditcard",
                "action": "verify"  # Use verify option only
            }
            
            # Generate hash for the request
            data["hash"] = self._generate_hash(data)
            
            # Make the request to PayU API
            response = requests.post(
                f"{self.api_base_url}/{self.api_version}/verify",
                data=data,
                timeout=10
            )
            
            # Parse the response
            result = response.json()
            
            # Check if the verification was successful
            if response.status_code == 200 and result.get("status") == "success":
                return self.format_response(
                    True,
                    "Card approved",
                    get_bin_info(cc_number[:6])
                )
            elif "error" in result:
                error_message = result.get("error_message", "Unknown error")
                # Check common error messages
                if "insufficient funds" in error_message.lower():
                    return self.format_response(
                        True,
                        "Card approved (insufficient funds)",
                        get_bin_info(cc_number[:6])
                    )
                elif "card declined" in error_message.lower():
                    return self.format_response(
                        False,
                        f"Card declined: {error_message}",
                        get_bin_info(cc_number[:6])
                    )
                elif "invalid card" in error_message.lower():
                    return self.format_response(
                        False,
                        f"Invalid card: {error_message}",
                        get_bin_info(cc_number[:6])
                    )
                else:
                    return self.format_response(
                        False,
                        f"Error: {error_message}",
                        get_bin_info(cc_number[:6])
                    )
            else:
                return self.format_response(
                    False,
                    "Card verification failed",
                    get_bin_info(cc_number[:6])
                )
                
        except requests.RequestException as e:
            return self.handle_error(e)
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with PayU gateway."""
    gateway = PayUGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)