"""
Braintree gateway integration for CC checking.
"""
import logging
from typing import Dict, Any, Optional
from gateways.base import BaseGateway
from config import BRAINTREE_MERCHANT_ID, BRAINTREE_PUBLIC_KEY, BRAINTREE_PRIVATE_KEY
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

# Import braintree module
import braintree
BRAINTREE_AVAILABLE = True

class BraintreeGateway(BaseGateway):
    """Braintree payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Braintree gateway."""
        super().__init__("Braintree")
        self.gateway = self._setup_gateway()
    
    def _setup_gateway(self) -> Optional[Any]:
        """Set up the Braintree gateway client."""
        if not BRAINTREE_AVAILABLE:
            logger.error("Braintree module not available.")
            return None
        
        if not all([BRAINTREE_MERCHANT_ID, BRAINTREE_PUBLIC_KEY, BRAINTREE_PRIVATE_KEY]):
            logger.error("Braintree credentials not set.")
            return None
        
        return braintree.BraintreeGateway(
            braintree.Configuration(
                environment=braintree.Environment.Sandbox,
                merchant_id=BRAINTREE_MERCHANT_ID,
                public_key=BRAINTREE_PUBLIC_KEY,
                private_key=BRAINTREE_PRIVATE_KEY
            )
        )
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Braintree."""
        check_type = kwargs.get("check_type", "b3")  # 'b3' or 'vbv'
        
        try:
            # Return error if Braintree gateway is not set up
            if not self.gateway:
                return self.format_response(False, "Braintree API credentials not configured")
            
            # Format the expiry date
            expiry_month = month.zfill(2)
            expiry_year = year if len(year) == 4 else f"20{year}"
            
            # Create a payment method nonce
            result = self.gateway.payment_method.create({
                "credit_card": {
                    "number": cc_number,
                    "expiration_month": expiry_month,
                    "expiration_year": expiry_year,
                    "cvv": cvv
                }
            })
            
            if not result.is_success:
                message = f"Card validation failed: {result.message}"
                return self.format_response(False, message, lookup_bin(cc_number[:6]))
            
            nonce = result.payment_method.token
            
            # Check the card based on the check type
            if check_type == "b3":
                verification_result = self.gateway.payment_method.create({
                    "payment_method_nonce": nonce,
                    "options": {
                        "verify_card": True
                    }
                })
            else:  # vbv
                verification_result = self.gateway.transaction.sale({
                    "amount": "1.00",
                    "payment_method_nonce": nonce,
                    "options": {
                        "submit_for_settlement": False,
                        "three_d_secure": {
                            "required": True
                        }
                    }
                })
            
            if verification_result.is_success:
                message = f"Card passed {check_type.upper()} verification"
                success = True
            else:
                message = f"Card failed {check_type.upper()} verification: {verification_result.message}"
                success = False
            
            # Get BIN info
            bin_info = lookup_bin(cc_number[:6])
            
            return self.format_response(success, message, bin_info)
        
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, check_type: str = "b3", **kwargs) -> Dict[str, Any]:
    """Check a credit card with Braintree gateway."""
    gateway = BraintreeGateway()
    return gateway.check_card(cc_number, month, year, cvv, check_type=check_type, **kwargs)
