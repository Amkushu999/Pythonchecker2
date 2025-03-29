"""
Paytm gateway integration for CC checking.
"""
import json
import logging
import requests
import base64
import hashlib
import uuid
import time
from typing import Dict, Any, Optional

from config import PAYTM_MERCHANT_ID, PAYTM_MERCHANT_KEY
from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

logger = logging.getLogger(__name__)

class PaytmGateway(BaseGateway):
    """Paytm payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Paytm gateway."""
        super().__init__("Paytm")
        # Use the staging/test API URL
        self.api_url = "https://securegw-stage.paytm.in"
        # Merchant details
        self.merchant_id = PAYTM_MERCHANT_ID
        self.merchant_key = PAYTM_MERCHANT_KEY
        self.website = "WEBSTAGING"  # Test website code
        self.industry_type = "Retail"
        self.channel_id = "WEB"
        
    def _generate_checksum(self, parameters: Dict[str, str]) -> str:
        """
        Generate Paytm checksum for request authentication.
        
        Args:
            parameters: Dictionary of request parameters
            
        Returns:
            Checksum string
        """
        # Convert parameters to string with separators
        param_string = ""
        for key in sorted(parameters.keys()):
            param_string += (str(parameters[key]) + "|")
        
        param_string = param_string[:-1]  # Remove the last '|'
        
        # Generate checksum using merchant key
        checksum = hashlib.sha256((param_string + self.merchant_key).encode()).hexdigest()
        return checksum
        
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Paytm."""
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
            order_id = f"ORDER_{int(time.time())}"
            # Generate a unique customer ID
            cust_id = f"CUST_{uuid.uuid4().hex[:16]}"
            
            # If Paytm credentials aren't configured, simulate the check
            if not PAYTM_MERCHANT_ID or not PAYTM_MERCHANT_KEY:
                # Simulate success for test numbers
                if cc_number.startswith(('4111111111111111', '5555555555554444', '378282246310005')):
                    bin_info = lookup_bin(cc_number[:6])
                    return self.format_response(True, "Test card verification successful with Paytm", bin_info)
                else:
                    return self.format_response(False, "Card verification failed with Paytm (simulated)")
            
            # Step 1: Initiate a transaction
            # Prepare parameters for transaction initiation
            paytm_params = {
                "MID": self.merchant_id,
                "ORDER_ID": order_id,
                "CUST_ID": cust_id,
                "INDUSTRY_TYPE_ID": self.industry_type,
                "CHANNEL_ID": self.channel_id,
                "TXN_AMOUNT": "1.00",  # Minimal amount for verification
                "WEBSITE": self.website,
                "CALLBACK_URL": "https://example.com/callback",
                # Include payment option details - for card payments
                "PAYMENT_MODE_ONLY": "yes",
                "AUTH_MODE": "3D",  # 3D secure authentication
                "PAYMENT_TYPE_ID": "CC",  # Credit Card
            }
            
            # Generate checksum
            checksum = self._generate_checksum(paytm_params)
            paytm_params["CHECKSUMHASH"] = checksum
            
            # Make API request to initiate transaction
            txn_url = f"{self.api_url}/theia/api/v1/initiateTransaction?mid={self.merchant_id}&orderId={order_id}"
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(txn_url, headers=headers, json={"requestType": "Payment", "body": paytm_params})
            
            if response.status_code == 200:
                txn_data = response.json()
                if txn_data.get("body", {}).get("resultInfo", {}).get("resultStatus") == "S":
                    # Transaction initiated successfully
                    txn_token = txn_data.get("body", {}).get("txnToken")
                    
                    # Step 2: Process payment with card details
                    # Note: In a real implementation, this would be done on the client side with JS SDK
                    # We're simulating the API call server-side for demonstration
                    
                    payment_params = {
                        "requestType": "NATIVE_CSV",
                        "mid": self.merchant_id,
                        "orderId": order_id,
                        "txnToken": txn_token,
                        "paymentMode": "CC",
                        "cardInfo": f"{cc_number}|{month}{year[-2:]}|{cvv}|Test Customer",
                        "authMode": "3D"
                    }
                    
                    process_url = f"{self.api_url}/theia/api/v1/processTransaction"
                    process_response = requests.post(process_url, headers=headers, json=payment_params)
                    
                    if process_response.status_code == 200:
                        process_data = process_response.json()
                        process_status = process_data.get("body", {}).get("resultInfo", {}).get("resultStatus")
                        
                        if process_status == "S" or process_status == "PENDING":
                            # Card verification successful or pending authentication
                            bin_info = lookup_bin(cc_number[:6])
                            return self.format_response(True, f"Card verification successful with Paytm (Status: {process_status})", bin_info)
                        else:
                            error_code = process_data.get("body", {}).get("resultInfo", {}).get("resultCode")
                            error_msg = process_data.get("body", {}).get("resultInfo", {}).get("resultMsg")
                            return self.format_response(False, f"Card verification failed with Paytm: {error_msg} (Code: {error_code})")
                    else:
                        # Process request failed
                        return self.format_response(False, "Failed to process card verification with Paytm")
                else:
                    # Transaction initiation failed
                    error_msg = txn_data.get("body", {}).get("resultInfo", {}).get("resultMsg")
                    return self.format_response(False, f"Failed to initiate card verification with Paytm: {error_msg}")
            else:
                # Request failed
                return self.format_response(False, "Failed to connect to Paytm payment gateway")
                
        except Exception as e:
            logger.error(f"Error in Paytm gateway: {str(e)}")
            return self.handle_error(e)


def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Paytm gateway."""
    gateway = PaytmGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)