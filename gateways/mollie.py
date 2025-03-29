"""
Mollie gateway integration for CC checking.
"""
import json
import logging
import requests
from typing import Dict, Any, Optional
import uuid

from config import MOLLIE_API_KEY
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class MollieGateway(BaseGateway):
    """Mollie payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Mollie gateway."""
        super().__init__("Mollie")
        self.api_url = "https://api.mollie.com/v2"
        self.headers = {
            "Authorization": f"Bearer {MOLLIE_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Mollie."""
        # First do the basic validation in the parent class
        validation_result = super().check_card(cc_number, month, year, cvv, **kwargs)
        if not validation_result.get("success", False):
            return validation_result
        
        try:
            # Format month and year correctly
            month = month.zfill(2)
            
            if len(year) == 2:
                year = "20" + year
                
            # Generate a unique order ID
            order_id = str(uuid.uuid4())
            
            # Prepare the payment payload
            # Note: Mollie doesn't accept direct card details via API for security reasons
            # In a real implementation, you would use their Components API with a frontend
            # For this example, we're using a simplified approach
            payment_payload = {
                "amount": {
                    "currency": "EUR",
                    "value": "0.01"  # Minimal amount for testing
                },
                "description": "Card Verification",
                "redirectUrl": "https://example.com/redirect",
                "webhookUrl": "https://example.com/webhook",
                "method": "creditcard",
                "metadata": {
                    "order_id": order_id
                }
            }
            
            # If Mollie API key isn't configured, return an error
            if not MOLLIE_API_KEY:
                return self.format_response(False, "Mollie API key not configured")
            
            # Create a payment at Mollie
            response = requests.post(f"{self.api_url}/payments", 
                                      headers=self.headers, 
                                      json=payment_payload)
            
            if response.status_code in (200, 201):
                # Successfully initiated payment process
                # In a real implementation, the next step would be to redirect the user to checkoutUrl
                result = response.json()
                payment_id = result.get("id")
                
                # For testing purposes, we need to simulate the completion of the process
                # In a real-world scenario, we would wait for the webhook callback
                
                # Check the payment status (this is a simplified example)
                check_response = requests.get(f"{self.api_url}/payments/{payment_id}", 
                                               headers=self.headers)
                
                if check_response.status_code == 200:
                    payment_data = check_response.json()
                    status = payment_data.get("status")
                    
                    # In reality, a new payment would be in "open" status
                    # We're checking if the API call is successful, which means
                    # we could proceed with the payment flow
                    if status in ("open", "pending", "authorized", "paid"):
                        bin_info = lookup_bin(cc_number[:6])
                        return self.format_response(True, f"Card verification initiated with Mollie (Status: {status})", bin_info)
                    else:
                        error_message = f"Card verification failed with Mollie (Status: {status})"
                        return self.format_response(False, error_message)
                else:
                    error_message = "Failed to check payment status"
                    return self.format_response(False, error_message)
            else:
                # Request failed
                error_message = "Card verification failed with Mollie"
                if response.text:
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            error_message = f"{error_message}: {error_data.get('detail', '')}"
                        elif "message" in error_data:
                            error_message = f"{error_message}: {error_data.get('message', '')}"
                    except json.JSONDecodeError:
                        pass
                
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in Mollie gateway: {str(e)}")
            return self.handle_error(e)


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Mollie gateway."""
    gateway = MollieGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)