"""
BIN lookup functionality for credit card information.
Uses real BIN databases to provide accurate information.
"""
import os
import json
import requests
import time
from typing import Dict, Any, Optional

from api_keys import BIN_LOOKUP_API_KEY

# File containing the BIN database
BIN_DATABASE_FILE = "bin_database.json"

def get_bin_info(bin_digits: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a Bank Identification Number (BIN).
    Uses a combination of local database and API lookup.
    
    Args:
        bin_digits: First 6 digits of the credit card number (BIN/IIN)
        
    Returns:
        Dictionary containing BIN information or None if not found
    """
    # First, try to get BIN info from the local database (faster and no API call needed)
    local_bin_info = get_bin_info_from_local_db(bin_digits)
    if local_bin_info:
        return local_bin_info
    
    # If not found locally, try to get BIN info from online API
    api_bin_info = get_bin_info_from_api(bin_digits)
    if api_bin_info:
        # Add to local database for future use
        add_bin_to_local_db(bin_digits, api_bin_info)
        return api_bin_info
    
    # If we couldn't find information, return a standard format with unknown values
    return {
        "bin": bin_digits,
        "bank": "Unknown",
        "country": "Unknown",
        "country_code": "XX",
        "type": "Unknown",
        "brand": "Unknown",
        "category": "Unknown",
        "timestamp": int(time.time())
    }

def get_bin_info_from_local_db(bin_digits: str) -> Optional[Dict[str, Any]]:
    """
    Get BIN information from the local database file.
    
    Args:
        bin_digits: First 6 digits of the credit card number
        
    Returns:
        Dictionary containing BIN information or None if not found
    """
    try:
        if not os.path.exists(BIN_DATABASE_FILE):
            # If the database file doesn't exist, create it with an empty structure
            with open(BIN_DATABASE_FILE, 'w') as f:
                json.dump({}, f)
            return None
            
        with open(BIN_DATABASE_FILE, 'r') as f:
            bin_database = json.load(f)
            
        if bin_digits in bin_database:
            return bin_database[bin_digits]
        return None
    except Exception as e:
        print(f"Error accessing local BIN database: {e}")
        return None

def add_bin_to_local_db(bin_digits: str, bin_info: Dict[str, Any]) -> bool:
    """
    Add BIN information to the local database file.
    
    Args:
        bin_digits: First 6 digits of the credit card number
        bin_info: Dictionary containing BIN information
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(BIN_DATABASE_FILE):
            bin_database = {}
        else:
            with open(BIN_DATABASE_FILE, 'r') as f:
                bin_database = json.load(f)
                
        bin_database[bin_digits] = bin_info
        
        with open(BIN_DATABASE_FILE, 'w') as f:
            json.dump(bin_database, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error adding BIN to local database: {e}")
        return False

def get_bin_info_from_api(bin_digits: str) -> Optional[Dict[str, Any]]:
    """
    Get BIN information from an online API.
    Supports multiple BIN lookup APIs for fallback.
    
    Args:
        bin_digits: First 6 digits of the credit card number
        
    Returns:
        Dictionary containing BIN information or None if not found
    """
    # Function to check if any API key is available
    if not BIN_LOOKUP_API_KEY:
        print("No BIN lookup API key available")
        return use_fallback_bin_database(bin_digits)
    
    try:
        # Primary BIN lookup API
        url = f"https://lookup.binlist.net/{bin_digits}"
        headers = {
            "Accept-Version": "3",
            "User-Agent": "BINCheckerBot/1.0"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Format the response in a standard format
            bin_info = {
                "bin": bin_digits,
                "bank": data.get("bank", {}).get("name", "Unknown"),
                "country": data.get("country", {}).get("name", "Unknown"),
                "country_code": data.get("country", {}).get("alpha2", "XX"),
                "type": data.get("type", "Unknown"),
                "brand": data.get("scheme", "Unknown"),
                "category": data.get("type", "Unknown"),
                "timestamp": int(time.time())
            }
            return bin_info
            
        # Try secondary BIN lookup API if primary fails
        if response.status_code != 200:
            return try_secondary_bin_api(bin_digits)
            
    except Exception as e:
        print(f"Error fetching BIN info from API: {e}")
        return try_secondary_bin_api(bin_digits)

def try_secondary_bin_api(bin_digits: str) -> Optional[Dict[str, Any]]:
    """
    Try a secondary BIN lookup API when the primary one fails.
    
    Args:
        bin_digits: First 6 digits of the credit card number
        
    Returns:
        Dictionary containing BIN information or None if not found
    """
    try:
        url = f"https://api.bincodes.com/bin/?format=json&api_key={BIN_LOOKUP_API_KEY}&bin={bin_digits}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if "error" in data:
                return use_fallback_bin_database(bin_digits)
                
            bin_info = {
                "bin": bin_digits,
                "bank": data.get("bank", "Unknown"),
                "country": data.get("country", "Unknown"),
                "country_code": data.get("countrycode", "XX"),
                "type": data.get("card_type", "Unknown"),
                "brand": data.get("card", "Unknown"),
                "category": data.get("level", "Unknown"),
                "timestamp": int(time.time())
            }
            return bin_info
            
        return use_fallback_bin_database(bin_digits)
        
    except Exception as e:
        print(f"Error fetching BIN info from secondary API: {e}")
        return use_fallback_bin_database(bin_digits)

def use_fallback_bin_database(bin_digits: str) -> Optional[Dict[str, Any]]:
    """
    Use a fallback method to determine card brand and type based on BIN patterns.
    This is used when no API is available or all API calls fail.
    
    Args:
        bin_digits: First 6 digits of the credit card number
        
    Returns:
        Dictionary containing basic BIN information
    """
    bin_prefix = bin_digits[:2]
    
    # Determine card brand based on IIN ranges
    brand = "Unknown"
    card_type = "Unknown"
    country = "Unknown"
    country_code = "XX"
    bank = "Unknown"
    
    # Visa
    if bin_digits.startswith("4"):
        brand = "Visa"
        if bin_digits.startswith("4026") or bin_digits.startswith("417500") or bin_digits.startswith("4508") or bin_digits.startswith("4844") or bin_digits.startswith("491"):
            card_type = "Debit"
        else:
            card_type = "Credit"
    
    # Mastercard
    elif bin_digits.startswith("5") and 1 <= int(bin_digits[1]) <= 5:
        brand = "Mastercard"
        card_type = "Credit"
    elif bin_digits.startswith("2") and bin_digits[1:4] in ["221", "222", "223", "224", "225", "226", "227", "228", "229", "23", "24", "25", "26", "270", "271", "272"]:
        brand = "Mastercard"
        card_type = "Credit"
    
    # American Express
    elif bin_digits.startswith("34") or bin_digits.startswith("37"):
        brand = "American Express"
        card_type = "Credit"
    
    # Discover
    elif bin_digits.startswith("6011") or bin_digits.startswith("644") or bin_digits.startswith("645") or bin_digits.startswith("646") or bin_digits.startswith("647") or bin_digits.startswith("648") or bin_digits.startswith("649") or bin_digits.startswith("65"):
        brand = "Discover"
        card_type = "Credit"
    
    # JCB
    elif bin_digits.startswith("35"):
        brand = "JCB"
        card_type = "Credit"
    
    # Diners Club
    elif bin_digits.startswith("300") or bin_digits.startswith("301") or bin_digits.startswith("302") or bin_digits.startswith("303") or bin_digits.startswith("304") or bin_digits.startswith("305") or bin_digits.startswith("36"):
        brand = "Diners Club"
        card_type = "Credit"
        
    # UnionPay
    elif bin_digits.startswith("62"):
        brand = "UnionPay"
        card_type = "Credit/Debit"
        country = "China"
        country_code = "CN"
        
    # Maestro
    elif bin_digits.startswith("5018") or bin_digits.startswith("5020") or bin_digits.startswith("5038") or bin_digits.startswith("6304") or bin_digits.startswith("6759") or bin_digits.startswith("676"):
        brand = "Maestro"
        card_type = "Debit"
    
    bin_info = {
        "bin": bin_digits,
        "bank": bank,
        "country": country,
        "country_code": country_code,
        "type": card_type,
        "brand": brand,
        "category": card_type,
        "timestamp": int(time.time())
    }
    
    return bin_info

def preload_common_bins():
    """
    Preload the most common BINs into the local database.
    This helps avoid too many API calls and ensures data availability.
    """
    # This would typically be a long list of common BINs
    # Here we just add a few as an example
    common_bins = {
        "400000": {
            "bin": "400000",
            "bank": "Visa",
            "country": "United States",
            "country_code": "US",
            "type": "Credit",
            "brand": "Visa",
            "category": "Classic",
            "timestamp": int(time.time())
        },
        "411111": {
            "bin": "411111",
            "bank": "Chase",
            "country": "United States",
            "country_code": "US",
            "type": "Credit",
            "brand": "Visa",
            "category": "Classic",
            "timestamp": int(time.time())
        },
        "521234": {
            "bin": "521234",
            "bank": "Mastercard",
            "country": "United States",
            "country_code": "US",
            "type": "Credit",
            "brand": "Mastercard",
            "category": "Standard",
            "timestamp": int(time.time())
        },
        "371234": {
            "bin": "371234",
            "bank": "American Express",
            "country": "United States",
            "country_code": "US",
            "type": "Credit",
            "brand": "American Express",
            "category": "Premium",
            "timestamp": int(time.time())
        }
    }
    
    # Check if database file exists
    if not os.path.exists(BIN_DATABASE_FILE):
        with open(BIN_DATABASE_FILE, 'w') as f:
            json.dump(common_bins, f, indent=2)
        return
        
    # Load existing database
    try:
        with open(BIN_DATABASE_FILE, 'r') as f:
            bin_database = json.load(f)
            
        # Add common BINs
        for bin_code, bin_data in common_bins.items():
            if bin_code not in bin_database:
                bin_database[bin_code] = bin_data
                
        # Save updated database
        with open(BIN_DATABASE_FILE, 'w') as f:
            json.dump(bin_database, f, indent=2)
            
    except Exception as e:
        print(f"Error preloading common BINs: {e}")

# Preload common BINs when module is imported
preload_common_bins()