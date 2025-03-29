"""
Square gateway integration for CC checking.
"""
import os
import time
import json
import random
import requests
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from api_keys import SQUARE_API_KEY, SQUARE_LOCATION_ID
from gateways.base import BaseGateway
from utils.bin_lookup import get_bin_info

class SquareGateway(BaseGateway):
    """Square payment gateway implementation."""

    def __init__(self):
        """Initialize the Square gateway."""
        super().__init__("Square")
        self.api_key = SQUARE_API_KEY
        self.location_id = SQUARE_LOCATION_ID
        self.api_base_url = "https://connect.squareup.com"
        self.api_version = "v2"

    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Square."""
        # Call the parent method to validate card format first
        validation_result = super().check_card(cc_number, month, year, cvv)
        if not validation_result["success"]:
            return validation_result

        # If we don't have an API key, return a message
        if not self.api_key or self.api_key == "your_square_api_key_here":
            return self.format_response(
                False,
                "Square API key is not set. Please configure your API key.",
                get_bin_info(cc_number[:6])
            )

        try:
            # Format the expiration date as required by Square (MM/YY)
            expiry = f"{month.zfill(2)}/{year[2:] if len(year) == 4 else year}"
            
            # Generate a unique nonce (normally this would come from Square's SqPaymentForm)
            # In a real implementation, we would use Square's JavaScript SDK to generate this
            nonce = f"cnon:{uuid.uuid4()}"
            
            # Construct the request headers
            headers = {
                "Square-Version": "2023-09-25",
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Construct the request payload for a card verification
            payload = {
                "idempotency_key": str(uuid.uuid4()),
                "source_id": nonce,
                "amount_money": {
                    "amount": 100,  # $1.00 in cents
                    "currency": "USD"
                },
                "card_details": {
                    "card": {
                        "number": cc_number,
                        "expiration_date": expiry,
                        "cvv": cvv
                    }
                },
                "autocomplete": False,  # Don't complete the payment, just verify
                "location_id": self.location_id
            }
            
            # Make the request to Square API
            response = requests.post(
                f"{self.api_base_url}/{self.api_version}/payments",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            # Parse the response
            result = response.json()
            
            # Check if the verification was successful
            if response.status_code == 200 and "payment" in result:
                payment_status = result["payment"].get("status")
                if payment_status == "APPROVED":
                    return self.format_response(
                        True,
                        "Card approved",
                        get_bin_info(cc_number[:6])
                    )
                elif payment_status == "PENDING":
                    return self.format_response(
                        True,
                        "Card verification pending",
                        get_bin_info(cc_number[:6])
                    )
                else:
                    return self.format_response(
                        False,
                        f"Card declined: {payment_status}",
                        get_bin_info(cc_number[:6])
                    )
            elif "errors" in result:
                error_detail = result["errors"][0].get("detail", "Unknown error")
                # Check for common decline reasons
                if "insufficient funds" in error_detail.lower():
                    return self.format_response(
                        True,
                        "Card approved (insufficient funds)",
                        get_bin_info(cc_number[:6])
                    )
                elif "card declined" in error_detail.lower():
                    return self.format_response(
                        False,
                        f"Card declined: {error_detail}",
                        get_bin_info(cc_number[:6])
                    )
                elif "card not supported" in error_detail.lower():
                    return self.format_response(
                        False,
                        f"Card not supported: {error_detail}",
                        get_bin_info(cc_number[:6])
                    )
                else:
                    return self.format_response(
                        False,
                        f"Error: {error_detail}",
                        get_bin_info(cc_number[:6])
                    )
            else:
                return self.format_response(
                    False,
                    "Card declined or verification failed",
                    get_bin_info(cc_number[:6])
                )
                
        except requests.RequestException as e:
            return self.handle_error(e)
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Square gateway."""
    gateway = SquareGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)