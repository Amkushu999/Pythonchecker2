"""
Base gateway implementation and common functions.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseGateway:
    """Base class for payment gateway implementations."""
    
    def __init__(self, name: str):
        """Initialize the gateway with a name."""
        self.name = name
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """
        Check a credit card with the payment gateway.
        This method should be overridden by subclasses.
        """
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
