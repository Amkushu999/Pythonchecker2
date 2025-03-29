"""
Stripe gateway integration for CC checking.
"""
import logging
import json
import os
from typing import Dict, Any
import stripe
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

# Configure Stripe API key (prioritize environment variable)
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
# Fallback to old config if available
if not STRIPE_SECRET_KEY:
    from config import STRIPE_API_KEY
    STRIPE_SECRET_KEY = STRIPE_API_KEY

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

class StripeGateway(BaseGateway):
    """Stripe payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Stripe gateway."""
        super().__init__("Stripe")
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Stripe."""
        try:
            # We need a Stripe API key for this to work
            if not stripe.api_key:
                logger.error("No Stripe API key configured. Cannot proceed with check.")
                return self.format_response(False, "Error: Stripe API key not configured", lookup_bin(cc_number[:6]))
            
            # Create a payment method
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": cc_number,
                    "exp_month": int(month),
                    "exp_year": int(year),
                    "cvc": cvv,
                },
            )
            
            # Create a SetupIntent to verify the card
            setup_intent = stripe.SetupIntent.create(
                payment_method=payment_method.id,
                confirm=True,
                usage="off_session",
                return_url="https://example.com/return",
            )
            
            # Check the status
            status = setup_intent.status
            if status == "succeeded":
                message = "Card is valid and chargeable"
                success = True
            elif status == "requires_action":
                message = "3D Secure authentication required"
                success = False
            else:
                message = f"Card verification failed: {status}"
                success = False
            
            # Get BIN info
            bin_info = lookup_bin(cc_number[:6])
            
            return self.format_response(success, message, bin_info)
        
        except Exception as e:
            if "stripe" in str(type(e)).lower():
                # This is a Stripe error
                error_message = str(e)
                logger.error(f"Stripe error: {error_message}")
                bin_info = lookup_bin(cc_number[:6])
                return self.format_response(False, f"Card declined: {error_message}", bin_info)
            else:
                # Other exception
                return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Stripe gateway."""
    gateway = StripeGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)
