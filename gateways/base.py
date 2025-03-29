"""
Base gateway implementation and common functions.
"""
import logging
import re
from typing import Dict, Any, Optional
from utils.card_utils import luhn_check, validate_cc_format

logger = logging.getLogger(__name__)

class BaseGateway:
    """Base class for payment gateway implementations."""
    
    def __init__(self, name: str):
        """Initialize the gateway with a name."""
        self.name = name
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """
        Check a credit card with the payment gateway.
        Performs Luhn algorithm validation before proceeding with the gateway check.
        
        This method should be overridden by subclasses, but they should call super().check_card()
        first to validate the card format and Luhn check.
        """
        # Validate basic card format
        if not validate_cc_format(cc_number, month, year, cvv):
            return self.format_response(False, "Invalid card format or failed Luhn check")
        
        # Perform Luhn algorithm check
        if not luhn_check(cc_number):
            return self.format_response(False, "Card number failed Luhn validation")
            
        # Subclasses should implement their specific gateway logic
        raise NotImplementedError("Subclasses must implement this method")
    
    def format_response(self, success: bool, message: str, bin_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Format a standardized response."""
        response = {
            "success": success,
            "message": message,
            "gateway": self.name
        }
        
        if bin_info:
            response["bin_info"] = bin_info
        
        return response
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors in a standardized way."""
        logger.error(f"Error in {self.name} gateway: {error}")
        return self.format_response(False, f"Gateway error: {type(error).__name__}")
