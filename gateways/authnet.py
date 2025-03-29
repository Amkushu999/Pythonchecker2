"""
Authorize.Net gateway integration for CC checking.
"""
import logging
import os
from typing import Dict, Any, Optional

from authorizenet import apicontractsv1
from authorizenet.apicontrollers import createTransactionController

from gateways.base import BaseGateway
from utils.bin_lookup import lookup_bin

# Configure Authorize.Net credentials
AUTHNET_API_LOGIN_ID = os.getenv("AUTHNET_API_LOGIN_ID", "")
AUTHNET_TRANSACTION_KEY = os.getenv("AUTHNET_TRANSACTION_KEY", "")
AUTHNET_SANDBOX = os.getenv("AUTHNET_ENVIRONMENT", "sandbox").lower() == "sandbox"

logger = logging.getLogger(__name__)

class AuthNetGateway(BaseGateway):
    """Authorize.Net payment gateway implementation."""
    
    def __init__(self):
        """Initialize the Authorize.Net gateway."""
        super().__init__("Authorize.Net")
    
    def check_card(self, cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
        """Check a credit card with Authorize.Net."""
        try:
            # We need API credentials for this to work
            if not AUTHNET_API_LOGIN_ID or not AUTHNET_TRANSACTION_KEY:
                logger.error("No Authorize.Net API credentials configured. Cannot proceed with check.")
                return self.format_response(False, "Error: Authorize.Net API credentials not configured", lookup_bin(cc_number[:6]))
            
            # Create a payment object
            merchantAuth = apicontractsv1.merchantAuthenticationType()
            merchantAuth.name = AUTHNET_API_LOGIN_ID
            merchantAuth.transactionKey = AUTHNET_TRANSACTION_KEY
            
            # Create the payment data for a credit card
            creditCard = apicontractsv1.creditCardType()
            creditCard.cardNumber = cc_number
            creditCard.expirationDate = f"{year}-{month}"
            creditCard.cardCode = cvv
            
            # Add the payment data to a paymentType object
            payment = apicontractsv1.paymentType()
            payment.creditCard = creditCard
            
            # Create an auth transaction
            transactionRequest = apicontractsv1.transactionRequestType()
            transactionRequest.transactionType = "authOnlyTransaction"
            transactionRequest.amount = "0.01"  # Use a small amount for auth only
            transactionRequest.payment = payment
            
            # Assemble the complete transaction request
            createTransactionRequest = apicontractsv1.createTransactionRequest()
            createTransactionRequest.merchantAuthentication = merchantAuth
            createTransactionRequest.refId = "cc_check_ref_" + cc_number[-4:]
            createTransactionRequest.transactionRequest = transactionRequest
            
            # Create the controller
            createTransactionController = createTransactionController(createTransactionRequest)
            if AUTHNET_SANDBOX:
                createTransactionController.setenvironment("sandbox")
            else:
                createTransactionController.setenvironment("production")
                
            createTransactionController.execute()
            
            # Get response
            response = createTransactionController.getresponse()
            
            # Check response
            bin_info = lookup_bin(cc_number[:6])
            
            if response is not None:
                if response.messages.resultCode == "Ok":
                    # Success
                    return self.format_response(True, "Card is valid and chargeable", bin_info)
                else:
                    # Decline
                    error_message = response.messages.message[0].text if response.messages is not None else "Unknown error"
                    return self.format_response(False, f"Card declined: {error_message}", bin_info)
            else:
                # No response
                return self.format_response(False, "No response from Authorize.Net", bin_info)
                
        except Exception as e:
            return self.handle_error(e)

def check_card(cc_number: str, month: str, year: str, cvv: str, **kwargs) -> Dict[str, Any]:
    """Check a credit card with Authorize.Net gateway."""
    gateway = AuthNetGateway()
    return gateway.check_card(cc_number, month, year, cvv, **kwargs)