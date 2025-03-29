"""
Razorpay gateway integration for CC checking.
"""
import json
import logging
import base64
import requests
from typing import Dict, Any, Optional

from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class RazorpayGateway(BaseGateway):
    """Razorpay payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Razorpay gateway."""
        super().__init__("Razorpay")
        self.api_url = "https://api.razorpay.com/v1"
        self.auth_string = base64.b64encode(f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode()).decode('utf-8')
        self.headers = {
            "Authorization": f"Basic {self.auth_string}",
            "Content-Type": "application/json"
        }
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Razorpay."""
        # First do the basic validation in the parent class
        validation_result = super().check_card(cc_number, month, year, cvv, **kwargs)
        if not validation_result.get("success", False):
            return validation_result
        
        try:
            # Format expiry date and year correctly
            month = month.zfill(2)
            if len(year) == 2:
                year = "20" + year
                
            # Prepare order creation request
            order_payload = {
                "amount": 100,  # amount in paise (₹1)
                "currency": "INR",
                "receipt": "receipt_cc_verification",
                "payment_capture": 0,  # Don't capture payment automatically
                "notes": {
                    "purpose": "card_verification"
                }
            }
            
            # If Razorpay credentials aren't configured, simulate the check
            if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
                # Simulate success for test numbers
                if cc_number.startswith(('4111111111111111', '5555555555554444', '378282246310005')):
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, "Test card verification successful with Razorpay", bin_info)
                else:
                    return self.format_response(False, "Card verification failed with Razorpay (simulated)")
                    
            # 1. Create an order
            order_response = requests.post(f"{self.api_url}/orders", headers=self.headers, json=order_payload)
            
            if order_response.status_code != 200:
                error_message = "Failed to create order for card verification"
                try:
                    error_data = order_response.json()
                    if "error" in error_data and "description" in error_data["error"]:
                        error_message = error_data["error"]["description"]
                except json.JSONDecodeError:
                    pass
                return self.format_response(False, error_message)
                
            order_data = order_response.json()
            order_id = order_data["id"]
            
            # 2. Use the order to create a payment
            payment_payload = {
                "amount": order_data["amount"],
                "currency": order_data["currency"],
                "order_id": order_id,
                "email": "test@example.com",
                "contact": "+919999999999",
                "method": "card",
                "card": {
                    "number": cc_number,
                    "name": "Test Customer",
                    "expiry_month": month,
                    "expiry_year": year,
                    "cvv": cvv
                }
            }
            
            payment_response = requests.post(f"{self.api_url}/payments/create/validate", 
                                             headers=self.headers, 
                                             json=payment_payload)
            
            if payment_response.status_code == 200:
                bin_info = lookup_bin(cc_number[:6])
                return self.format_response(True, "Card verification successful with Razorpay", bin_info)
            else:
                error_message = "Card verification failed with Razorpay"
                try:
                    error_data = payment_response.json()
                    if "error" in error_data and "description" in error_data["error"]:
                        error_message = error_data["error"]["description"]
                except json.JSONDecodeError:
                    pass
                
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in Razorpay gateway: {str(e)}")
            return self.handle_error(e)


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Razorpay gateway."""
    gateway = RazorpayGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)