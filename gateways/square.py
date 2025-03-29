"""
Square gateway integration for CC checking.
"""
import json
import logging
import requests
from typing import Dict, Any, Optional

from config import SQUARE_ACCESS_TOKEN
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class SquareGateway(BaseGateway):
    """Square payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Square gateway."""
        super().__init__("Square")
        self.api_url = "https://connect.squareup.com/v2"
        self.headers = {
            "Square-Version": "2023-06-08",
            "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Square."""
        # First do the basic validation in the parent class
        validation_result = super().check_card(cc_number, month, year, cvv, **kwargs)
        if not validation_result.get("success", False):
            return validation_result

        # Square requires a nonce, which we'd normally get from their JS SDK
        # For checking purposes, we'll use their API to tokenize the card
        # This is a slightly simplified version for demonstration purposes
        
        try:
            # Format card data for Square
            # Make sure the year is in YYYY format
            if len(year) == 2:
                expiration_year = "20" + year
            else:
                expiration_year = year
                
            # Format month as MM (with leading zero if needed)
            expiration_month = month.zfill(2)
            
            # First, get a reference ID for tokenization
            url = f"{self.api_url}/cards"
            payload = {
                "source_id": "cnon:card-nonce-ok",  # This is a test nonce that Square accepts
                "card": {
                    "number": cc_number,
                    "expiration_month": expiration_month,
                    "expiration_year": expiration_year,
                    "cvv": cvv,
                    "cardholder_name": "Test Customer",  # Required by Square
                    "billing_address": {
                        "address_line_1": "123 Main St",
                        "locality": "San Francisco",
                        "administrative_district_level_1": "CA",
                        "postal_code": "94105",
                        "country": "US"
                    }
                }
            }
            
            # If Square API key is not configured, simulate the check
            if not SQUARE_ACCESS_TOKEN:
                # Simulate success for test numbers
                if cc_number.startswith(('4111111111111111', '5555555555554444', '378282246310005')):
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, "Test card verification successful", bin_info)
                else:
                    return self.format_response(False, "Card verification failed (simulated)")
            
            # Make API request to Square
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code in (200, 201):
                result = response.json()
                bin_info = lookup_bin(cc_number[:6])
                return self.format_response(True, "Card verification successful", bin_info)
            else:
                error_message = "Card verification failed"
                if response.text:
                    try:
                        error_data = response.json()
                        if "errors" in error_data and error_data["errors"]:
                            error_message = error_data["errors"][0].get("detail", error_message)
                    except json.JSONDecodeError:
                        pass
                
                return self.format_response(False, error_message)
                
        except Exception as e:
            logger.error(f"Error in Square gateway: {str(e)}")
            return self.handle_error(e)


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Square gateway."""
    gateway = SquareGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)