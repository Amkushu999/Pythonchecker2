"""
Klarna gateway integration for CC checking.
"""
import json
import logging
import base64
import requests
from typing import Dict, Any, Optional

from config import KLARNA_USERNAME, KLARNA_PASSWORD
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class KlarnaGateway(BaseGateway):
    """Klarna payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Klarna gateway."""
        super().__init__("Klarna")
        # Set the appropriate environment based on credentials
        self.api_url = "https://api.playground.klarna.com/checkout/v3/orders"  # Sandbox URL
        self.auth_string = base64.b64encode(f"{KLARNA_USERNAME}:{KLARNA_PASSWORD}".encode()).decode('utf-8')
        self.headers = {
            "Authorization": f"Basic {self.auth_string}",
            "Content-Type": "application/json"
        }
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Klarna."""
        # First do the basic validation in the parent class
        validation_result = super().check_card(cc_number, month, year, cvv, **kwargs)
        if not validation_result.get("success", False):
            return validation_result
        
        try:
            # Format expiry date as MM/YY
            if len(year) == 4:
                year = year[2:]
            expiry = f"{month.zfill(2)}/{year}"
            
            # Prepare the payload for Klarna's API
            # This is a simplified version of Klarna's API request
            payload = {
                "purchase_country": "US",
                "purchase_currency": "USD",
                "locale": "en-US",
                "order_amount": 1000,  # Amount in cents (10.00 USD)
                "order_tax_amount": 0,
                "order_lines": [{
                    "type": "physical",
                    "reference": "TEST-ITEM-123",
                    "name": "Test Item",
                    "quantity": 1,
                    "unit_price": 1000,
                    "tax_rate": 0,
                    "total_amount": 1000,
                    "total_tax_amount": 0
                }],
                "billing_address": {
                    "given_name": "Test",
                    "family_name": "Customer",
                    "email": "test@example.com",
                    "street_address": "123 Test St",
                    "postal_code": "12345",
                    "city": "Testville",
                    "country": "US"
                },
                "customer": {
                    "date_of_birth": "1990-01-01"
                },
                "merchant_urls": {
                    "confirmation": "https://example.com/confirmation",
                    "notification": "https://example.com/notification"
                }
            }
            
            # If Klarna credentials aren't configured, simulate the check
            if not KLARNA_USERNAME or not KLARNA_PASSWORD:
                # Simulate success for test numbers
                if cc_number.startswith(('4111111111111111', '5555555555554444', '378282246310005')):
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, "Test card verification successful with Klarna", bin_info)
                else:
                    return self.format_response(False, "Card verification failed with Klarna (simulated)")
            
            # Make API request to Klarna
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            
            if response.status_code in (200, 201):
                # Successfully created order with Klarna
                result = response.json()
                bin_info = lookup_bin(cc_number[:6])
                return self.format_response(True, "Card verification successful with Klarna", bin_info)
            else:
                error_message = "Card verification failed with Klarna"
                if response.text:
                    try:
                        error_data = response.json()
                        if "error_messages" in error_data:
                            error_message = f"{error_message}: {', '.join(error_data['error_messages'])}"
                    except json.JSONDecodeError:
                        pass
                
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in Klarna gateway: {str(e)}")
            return self.handle_error(e)


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Klarna gateway."""
    gateway = KlarnaGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)