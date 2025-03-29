"""
CyberSource gateway integration for CC checking.
"""
import logging
import os
import requests
import json
import hmac
import hashlib
import base64
import datetime
import uuid
from typing import Dict, Any, Optional

from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

# Configure CyberSource credentials
CYBERSOURCE_MERCHANT_ID = os.getenv("CYBERSOURCE_MERCHANT_ID", "")
CYBERSOURCE_API_KEY = os.getenv("CYBERSOURCE_API_KEY", "")
CYBERSOURCE_SECRET_KEY = os.getenv("CYBERSOURCE_SECRET_KEY", "")
CYBERSOURCE_ENVIRONMENT = os.getenv("CYBERSOURCE_ENVIRONMENT", "apitest").lower()

logger = logging.getLogger(__name__)

class CybersourceGateway(BaseGateway):
    """CyberSource payment gateway implementation."""
    
    def __init__(self):
        """Initialize the CyberSource gateway."""
        super().__init__("CyberSource")
    
    def _generate_signature(self, host, resource, payload_string, date, digest):
        """Generate signature for CyberSource request."""
        target_host = host.replace("https://", "").replace("http://", "")
        signature_string = (
            "host: " + target_host + "\n" +
            "date: " + date + "\n" +
            "request-target: post " + resource + "\n" +
            "digest: " + digest + "\n" +
            "v-c-merchant-id: " + CYBERSOURCE_MERCHANT_ID
        )
        
        hmac_obj = hmac.new(
            base64.b64decode(CYBERSOURCE_SECRET_KEY),
            signature_string.encode('utf-8'),
            hashlib.sha256
        )
        signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
        return signature
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with CyberSource."""
        try:
            # We need API credentials for this to work
            if not CYBERSOURCE_MERCHANT_ID or not CYBERSOURCE_API_KEY or not CYBERSOURCE_SECRET_KEY:
                logger.error("No CyberSource API credentials configured. Cannot proceed with check.")
                return self.format_response(False, "Error: CyberSource API credentials not configured", lookup_bin(cc_number[:6]))
            
            # Define API endpoint based on environment
            if CYBERSOURCE_ENVIRONMENT == "production":
                api_host = "https://api.cybersource.com"
            else:
                api_host = "https://apitest.cybersource.com"
            
            # Define the API resource path
            resource_path = "/pts/v2/payments"
            
            # Format expiry date
            expiry_month = month.zfill(2)
            expiry_year = year.zfill(4) if len(year) <= 2 else year
            
            # Create a unique reference
            reference_number = str(uuid.uuid4())
            
            # Create the payment request payload
            payload = {
                "clientReferenceInformation": {
                    "code": f"cc-check-{cc_number[-4:]}"
                },
                "processingInformation": {
                    "commerceIndicator": "internet",
                    "actionList": ["VALIDATE"]
                },
                "paymentInformation": {
                    "card": {
                        "number": cc_number,
                        "expirationMonth": expiry_month,
                        "expirationYear": expiry_year,
                        "securityCode": cvv
                    }
                },
                "orderInformation": {
                    "amountDetails": {
                        "totalAmount": "1.00",
                        "currency": "USD"
                    },
                    "billTo": {
                        "firstName": "John",
                        "lastName": "Doe",
                        "address1": "1 Market St",
                        "locality": "San Francisco",
                        "administrativeArea": "CA",
                        "postalCode": "94105",
                        "country": "US",
                        "email": "test@example.com",
                        "phoneNumber": "4158880000"
                    }
                }
            }
            
            # Convert payload to string
            payload_string = json.dumps(payload)
            
            # Generate the digest
            digest_obj = hashlib.sha256(payload_string.encode('utf-8'))
            digest = "SHA-256=" + base64.b64encode(digest_obj.digest()).decode('utf-8')
            
            # Generate date
            date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            
            # Generate signature
            signature = self._generate_signature(api_host, resource_path, payload_string, date, digest)
            
            # Set up headers
            headers = {
                "v-c-merchant-id": CYBERSOURCE_MERCHANT_ID,
                "Host": api_host.replace("https://", "").replace("http://", ""),
                "Date": date,
                "Digest": digest,
                "Signature": 'keyid="' + CYBERSOURCE_API_KEY + '", algorithm="HmacSHA256", headers="host date request-target digest v-c-merchant-id", signature="' + signature + '"',
                "Content-Type": "application/json"
            }
            
            # Make the API request
            response = requests.post(api_host + resource_path, data=payload_string, headers=headers)
            
            # Get BIN info
            bin_info = lookup_bin(cc_number[:6])
            
            # Process the response
            if response.status_code in (200, 201, 202):
                response_data = response.json()
                
                # Check payment status
                if "status" in response_data:
                    if response_data["status"] == "AUTHORIZED" or response_data["status"] == "PENDING_AUTHENTICATION":
                        return self.format_response(True, "Card is valid", bin_info)
                    else:
                        reason = response_data.get("errorInformation", {}).get("message", "Card declined")
                        return self.format_response(False, f"Card declined: {reason}", bin_info)
                else:
                    return self.format_response(False, "Invalid response from CyberSource", bin_info)
            else:
                # Handle error response
                error_message = "Unknown error"
                
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                    elif "errorInformation" in error_data and "message" in error_data["errorInformation"]:
                        error_message = error_data["errorInformation"]["message"]
                except:
                    error_message = f"HTTP error {response.status_code}"
                
                return self.format_response(False, f"Card declined: {error_message}", bin_info)
                
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with CyberSource gateway."""
    gateway = CybersourceGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)