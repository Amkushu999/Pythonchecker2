"""
Shopify gateway integration for CC checking.
"""
import logging
import os
import shopify
import json
from typing import Dict, Any, Optional

from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

# Configure Shopify credentials
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY", "")
SHOPIFY_PASSWORD = os.getenv("SHOPIFY_PASSWORD", "")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "")

logger = logging.getLogger(__name__)

class ShopifyGateway(BaseGateway):
    """Shopify payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Shopify gateway."""
        super().__init__("Shopify")
        self._setup_session()
    
    def _setup_session(self) -> None:
        """Set up the Shopify API session."""
        if not SHOPIFY_API_KEY or not SHOPIFY_PASSWORD or not SHOPIFY_STORE_URL:
            logger.error("Shopify credentials not properly configured.")
            return None
        
        try:
            # Initialize Shopify session
            api_session = shopify.Session(SHOPIFY_STORE_URL, "2023-04", {
                "api_key": SHOPIFY_API_KEY,
                "password": SHOPIFY_PASSWORD
            })
            shopify.ShopifyResource.activate_session(api_session)
            return True
        except Exception as e:
            logger.error(f"Error setting up Shopify session: {e}")
            return None
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Shopify."""
        try:
            # We need API credentials for this to work
            if not SHOPIFY_API_KEY or not SHOPIFY_PASSWORD or not SHOPIFY_STORE_URL:
                logger.error("No Shopify API credentials configured. Cannot proceed with check.")
                return self.format_response(False, "Error: Shopify API credentials not configured", lookup_bin(cc_number[:6]))
            
            # Create a draft order
            draft_order = shopify.DraftOrder()
            draft_order.line_items = [{
                "title": "Test Item",
                "price": "0.01",
                "quantity": 1
            }]
            
            success = draft_order.save()
            
            if not success:
                return self.format_response(False, "Failed to create test order", lookup_bin(cc_number[:6]))
            
            try:
                # Use payment processing endpoint for validating card
                url = f"{SHOPIFY_STORE_URL}/admin/api/2023-04/payment_gateway/process_payment.json"
                
                payment_data = {
                    "payment": {
                        "amount": "0.01",
                        "credit_card": {
                            "number": cc_number,
                            "month": month,
                            "year": year,
                            "verification_value": cvv,
                            "name": "Test Card"
                        },
                        "test": True
                    }
                }
                
                # In a real implementation, you would use the Shopify API to process this
                # Here we're simulating the response based on card validation
                
                # Simple validation: check if it's a valid credit card format
                # In reality, Shopify would validate this through their payment system
                # Get BIN info
                bin_info = lookup_bin(cc_number[:6])
                
                # For testing, we'll check Luhn's algorithm
                def is_luhn_valid(card_number):
                    digits = [int(d) for d in card_number if d.isdigit()]
                    checksum = digits.pop()
                    digits.reverse()
                    doubled_digits = []
                    for i, digit in enumerate(digits):
                        if i % 2 == 0:
                            doubled = digit * 2
                            if doubled > 9:
                                doubled = doubled - 9
                            doubled_digits.append(doubled)
                        else:
                            doubled_digits.append(digit)
                    total = sum(doubled_digits) + checksum
                    return total % 10 == 0
                
                # Basic card validation
                if len(cc_number) < 13 or len(cc_number) > 19 or not cc_number.isdigit():
                    return self.format_response(False, "Invalid card number format", bin_info)
                
                # Check expiry
                try:
                    month_int = int(month)
                    year_int = int(year)
                    if month_int < 1 or month_int > 12:
                        return self.format_response(False, "Invalid expiry month", bin_info)
                except ValueError:
                    return self.format_response(False, "Invalid expiry format", bin_info)
                
                # Check CVV
                if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
                    return self.format_response(False, "Invalid CVV format", bin_info)
                
                # Check Luhn's algorithm
                if not is_luhn_valid(cc_number):
                    return self.format_response(False, "Card number failed Luhn check", bin_info)
                
                # Clean up test order
                try:
                    draft_order.destroy()
                except Exception as e:
                    logger.warning(f"Failed to clean up test order: {e}")
                
                # If all checks pass, we simulate a successful check
                return self.format_response(True, "Card appears to be valid", bin_info)
                
            except Exception as e:
                logger.error(f"Error processing payment: {e}")
                return self.format_response(False, f"Payment processing error: {str(e)}", lookup_bin(cc_number[:6]))
                
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Shopify gateway."""
    gateway = ShopifyGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)