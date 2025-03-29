"""
MercadoPago gateway integration for CC checking.
"""
import json
import logging
import requests
from typing import Dict, Any, Optional
import uuid

from config import MERCADOPAGO_ACCESS_TOKEN
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class MercadoPagoGateway(BaseGateway):
    """MercadoPago payment gateway implementation."""
    
    def __init__(self):
        """Initialize the MercadoPago gateway."""
        super().__init__("MercadoPago")
        self.api_url = "https://api.mercadopago.com/v1"
        self.headers = {
            "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with MercadoPago."""
        # First do the basic validation in the parent class
        validation_result = super().check_card(cc_number, month, year, cvv, **kwargs)
        if not validation_result.get("success", False):
            return validation_result
        
        try:
            # Format month and year correctly
            month = month.zfill(2)
            
            if len(year) == 2:
                year = "20" + year
                
            # Generate a unique external reference
            external_reference = str(uuid.uuid4())
            
            # If MercadoPago credentials aren't configured, simulate the check
            if not MERCADOPAGO_ACCESS_TOKEN:
                # Simulate success for test numbers
                if cc_number.startswith(('4111111111111111', '5555555555554444', '378282246310005')):
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, "Test card verification successful with MercadoPago", bin_info)
                else:
                    return self.format_response(False, "Card verification failed with MercadoPago (simulated)")
            
            # Step 1: Create a customer
            customer_payload = {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "Customer",
                "identification": {
                    "type": "CPF",
                    "number": "12345678909"
                }
            }
            
            customer_response = requests.post(f"{self.api_url}/customers", 
                                              headers=self.headers, 
                                              json=customer_payload)
            
            if customer_response.status_code != 201:
                error_message = "Failed to create customer for card verification"
                try:
                    error_data = customer_response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                except json.JSONDecodeError:
                    pass
                return self.format_response(False, error_message)
                
            customer_data = customer_response.json()
            customer_id = customer_data["id"]
            
            # Step 2: Create a card token
            token_payload = {
                "card_number": cc_number,
                "security_code": cvv,
                "expiration_month": month,
                "expiration_year": year,
                "cardholder": {
                    "name": "Test Customer",
                    "identification": {
                        "type": "CPF",
                        "number": "12345678909"
                    }
                }
            }
            
            token_response = requests.post(f"{self.api_url}/card_tokens", 
                                           headers=self.headers, 
                                           json=token_payload)
            
            if token_response.status_code != 201:
                error_message = "Failed to tokenize card"
                try:
                    error_data = token_response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                    elif "error" in error_data:
                        error_message = error_data["error"]
                except json.JSONDecodeError:
                    pass
                return self.format_response(False, error_message)
                
            token_data = token_response.json()
            card_token = token_data["id"]
            
            # Step 3: Associate the card with the customer
            card_payload = {
                "token": card_token
            }
            
            card_response = requests.post(f"{self.api_url}/customers/{customer_id}/cards", 
                                          headers=self.headers, 
                                          json=card_payload)
            
            if card_response.status_code in (200, 201):
                # Card was successfully associated with customer
                bin_info = lookup_bin(cc_number[:6])
                return self.format_response(True, "Card verification successful with MercadoPago", bin_info)
            else:
                error_message = "Card verification failed with MercadoPago"
                try:
                    error_data = card_response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                except json.JSONDecodeError:
                    pass
                
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in MercadoPago gateway: {str(e)}")
            return self.handle_error(e)


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with MercadoPago gateway."""
    gateway = MercadoPagoGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)