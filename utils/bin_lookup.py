"""
BIN (Bank Identification Number) lookup functionality.
"""
import os
import json
import logging
from typing import Dict, Optional
from config import BIN_DATABASE_FILE

logger = logging.getLogger(__name__)

# Sample BIN database (minimal for demo)
SAMPLE_BIN_DATABASE = {
    "4": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "United States",
        "bank": "JPMorgan Chase"
    },
    "5": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Standard",
        "country": "United States",
        "bank": "Citibank"
    },
    "3": {
        "brand": "American Express",
        "type": "Credit",
        "category": "Premium",
        "country": "United States",
        "bank": "American Express"
    },
    "6": {
        "brand": "Discover",
        "type": "Credit",
        "category": "Standard",
        "country": "United States",
        "bank": "Discover Bank"
    }
}

# More specific BINs
SPECIFIC_BINS = {
    "401200": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "United States",
        "bank": "Bank of America"
    },
    "528913": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "United States",
        "bank": "Wells Fargo"
    },
    "440393": {
        "brand": "Visa",
        "type": "Debit",
        "category": "Classic",
        "country": "United States",
        "bank": "Chase Bank"
    }
}

def load_bin_database() -> Dict:
    """Load the BIN database from file or create a sample one."""
    if os.path.exists(BIN_DATABASE_FILE):
        try:
            with open(BIN_DATABASE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading BIN database: {e}")
            # Fall back to sample database
    
    # Create a sample BIN database
    sample_db = {**SAMPLE_BIN_DATABASE, **SPECIFIC_BINS}
    try:
        with open(BIN_DATABASE_FILE, 'w') as f:
            json.dump(sample_db, f, indent=2)
    except IOError as e:
        logger.error(f"Error saving BIN database: {e}")
    
    return sample_db

# Load BIN database on module import
bin_database = load_bin_database()

def lookup_bin(bin_code: str) -> Optional[Dict]:
    """
    Look up a BIN code in the database.
    
    Args:
        bin_code: The BIN code to look up (first 6 digits of a card number).
        
    Returns:
        A dictionary with BIN information or None if not found.
    """
    # Try exact match first
    if bin_code in SPECIFIC_BINS:
        return SPECIFIC_BINS[bin_code]
    
    # Try first digit match
    if bin_code[0] in SAMPLE_BIN_DATABASE:
        return SAMPLE_BIN_DATABASE[bin_code[0]]
    
    # Return a generic response if nothing found
    return {
        "brand": "Unknown",
        "type": "Unknown",
        "country": "Unknown",
        "bank": "Unknown"
    }
