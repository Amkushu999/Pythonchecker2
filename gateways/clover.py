"""
Clover gateway integration for CC checking.
"""
import os
import time
import json
import random
import requests
from datetime import datetime
from typing import Dict, Any, Optional

from api_keys import CLOVER_API_KEY
from gateways.base import BaseGateway
from utils.bin_lookup import get_bin_info

class CloverGateway(BaseGateway):
    """Clover payment gateway implementation."""

    def __init__(self):
        """Initialize the Clover gateway."""
        super().__init__("Clover")
        self.api_key = CLOVER_API_KEY
        self.api_base_url = "https://api.clover.com"
        self.api_version = "v1"

    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Clover."""
        # Call the parent method to validate card format first
        validation_result = super().check_card(cc_number, month, year, cvv)
        if not validation_result["success"]:
            return validation_result

        # If we don't have an API key, return a message
        if not self.api_key or self.api_key == "your_clover_api_key_here":
            return self.format_response(
                False,
                "Clover API key is not set. Please configure your API key.",
                get_bin_info(cc_number[:6])
            )

        try:
            # Get the expiration date in the format required by Clover (MMYY)
            expiry = f"{month.zfill(2)}{year[2:] if len(year) == 4 else year}"
            
            # Construct the request headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "X-Clover-Merchant-ID": "your_merchant_id",  # Replace with actual merchant ID
            }
            
            # Construct the request payload
            payload = {
                "amount": 100,  # $1.00 in cents
                "currency": "USD",
                "source": {
                    "type": "card",
                    "card": {
                        "number": cc_number,
                        "exp_month": int(month),
                        "exp_year": int(year if len(year) == 4 else f"20{year}"),
                        "cvv": cvv
                    }
                },
                "capture": False,  # Auth only, no capture
                "description": "Card verification",
            }
            
            # Make the request to Clover API
            response = requests.post(
                f"{self.api_base_url}/{self.api_version}/charges",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            # Parse the response
            result = response.json()
            
            # Determine if the check was successful
            if response.status_code == 200 and result.get("status") == "succeeded":
                return self.format_response(
                    True,
                    "Card approved",
                    get_bin_info(cc_number[:6])
                )
            elif "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                if "insufficient_funds" in error_msg:
                    # Card is valid but has insufficient funds
                    return self.format_response(
                        True,
                        "Card approved (insufficient funds)",
                        get_bin_info(cc_number[:6])
                    )
                elif "stolen_card" in error_msg or "lost_card" in error_msg:
                    return self.format_response(
                        False,
                        "Card declined (reported as stolen or lost)",
                        get_bin_info(cc_number[:6])
                    )
                else:
                    return self.format_response(
                        False,
                        f"Card declined: {error_msg}",
                        get_bin_info(cc_number[:6])
                    )
            else:
                return self.format_response(
                    False,
                    "Card declined",
                    get_bin_info(cc_number[:6])
                )
                
        except requests.RequestException as e:
            return self.handle_error(e)
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Clover gateway."""
    gateway = CloverGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)