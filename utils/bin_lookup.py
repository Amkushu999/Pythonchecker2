"""
BIN (Bank Identification Number) lookup functionality.
"""
import os
import json
import logging
from typing import Dict, Optional
from config import BIN_DATABASE_FILE

logger = logging.getLogger(__name__)

# Major card network BIN prefixes
CARD_NETWORK_BINS = {
    "4": {
        "brand": "Visa",
        "type": "Credit/Debit",
        "category": "Various",
        "country": "International",
        "bank": "Various"
    },
    "5": {
        "brand": "Mastercard",
        "type": "Credit/Debit",
        "category": "Various",
        "country": "International",
        "bank": "Various"
    },
    "3": {
        "brand": "American Express",
        "type": "Credit",
        "category": "Premium",
        "country": "International",
        "bank": "American Express"
    },
    "6": {
        "brand": "Discover/UnionPay",
        "type": "Credit/Debit",
        "category": "Various",
        "country": "International",
        "bank": "Various"
    },
    "35": {
        "brand": "JCB",
        "type": "Credit",
        "category": "Various",
        "country": "Japan/International",
        "bank": "Various Japanese Banks"
    },
    "30": {
        "brand": "Diners Club",
        "type": "Credit",
        "category": "Premium",
        "country": "International",
        "bank": "Various"
    },
    "36": {
        "brand": "Diners Club",
        "type": "Credit",
        "category": "Premium",
        "country": "International",
        "bank": "Various"
    },
    "38": {
        "brand": "Diners Club",
        "type": "Credit",
        "category": "Premium",
        "country": "International",
        "bank": "Various"
    },
    "62": {
        "brand": "UnionPay",
        "type": "Credit/Debit",
        "category": "Various",
        "country": "China/International",
        "bank": "Various Chinese Banks"
    },
    "81": {
        "brand": "Humo",
        "type": "Debit",
        "category": "National",
        "country": "Uzbekistan",
        "bank": "Various Uzbek Banks"
    }
}

# Specific country BINs (more comprehensive)
SPECIFIC_BINS = {
    # US Banks
    "401200": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "United States",
        "bank": "Bank of America"
    },
    "414720": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Signature",
        "country": "United States",
        "bank": "Chase Bank"
    },
    "440393": {
        "brand": "Visa",
        "type": "Debit",
        "category": "Classic",
        "country": "United States",
        "bank": "Chase Bank"
    },
    "528913": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "United States",
        "bank": "Wells Fargo"
    },
    "542418": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Platinum",
        "country": "United States",
        "bank": "Citibank"
    },
    "371449": {
        "brand": "American Express",
        "type": "Credit",
        "category": "Gold",
        "country": "United States",
        "bank": "American Express"
    },
    "378282": {
        "brand": "American Express",
        "type": "Credit",
        "category": "Platinum",
        "country": "United States",
        "bank": "American Express"
    },
    
    # UK Banks
    "454313": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "United Kingdom",
        "bank": "Barclays"
    },
    "492181": {
        "brand": "Visa",
        "type": "Debit",
        "category": "Classic",
        "country": "United Kingdom",
        "bank": "HSBC"
    },
    "543460": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "United Kingdom",
        "bank": "Lloyds Bank"
    },
    
    # Canadian Banks
    "450803": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "Canada",
        "bank": "Royal Bank of Canada"
    },
    "516075": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "Canada",
        "bank": "TD Bank"
    },
    
    # Australian Banks
    "456475": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "Australia",
        "bank": "Commonwealth Bank"
    },
    "522980": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Platinum",
        "country": "Australia",
        "bank": "ANZ Bank"
    },
    
    # German Banks
    "491361": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "Germany",
        "bank": "Deutsche Bank"
    },
    "520058": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "Germany",
        "bank": "Commerzbank"
    },
    
    # French Banks
    "497017": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "France",
        "bank": "BNP Paribas"
    },
    "513381": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "France",
        "bank": "Société Générale"
    },
    
    # Japanese Banks
    "456789": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Gold",
        "country": "Japan",
        "bank": "Mitsubishi UFJ"
    },
    "358673": {
        "brand": "JCB",
        "type": "Credit",
        "category": "Classic",
        "country": "Japan",
        "bank": "Mizuho Bank"
    },
    "356778": {
        "brand": "JCB",
        "type": "Credit",
        "category": "Gold",
        "country": "Japan",
        "bank": "Sumitomo Mitsui"
    },
    
    # Brazilian Banks
    "411825": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "Brazil",
        "bank": "Banco do Brasil"
    },
    "551011": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "Brazil",
        "bank": "Itaú Unibanco"
    },
    
    # Indian Banks
    "489015": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "India",
        "bank": "State Bank of India"
    },
    "512881": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "India",
        "bank": "HDFC Bank"
    },
    
    # South African Banks
    "478943": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "South Africa",
        "bank": "Standard Bank"
    },
    "538612": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "South Africa",
        "bank": "FNB"
    },
    
    # Chinese Banks
    "621785": {
        "brand": "UnionPay",
        "type": "Debit",
        "category": "Classic",
        "country": "China",
        "bank": "ICBC"
    },
    "625209": {
        "brand": "UnionPay",
        "type": "Credit",
        "category": "Gold",
        "country": "China",
        "bank": "Bank of China"
    },
    
    # Russian Banks
    "427683": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "Russia",
        "bank": "Sberbank"
    },
    "532301": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "Russia",
        "bank": "VTB Bank"
    },
    
    # UAE Banks
    "419860": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Platinum",
        "country": "United Arab Emirates",
        "bank": "Emirates NBD"
    },
    "552033": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "World",
        "country": "United Arab Emirates",
        "bank": "Abu Dhabi Commercial Bank"
    },
    
    # Mexican Banks
    "471324": {
        "brand": "Visa",
        "type": "Credit",
        "category": "Classic",
        "country": "Mexico",
        "bank": "BBVA Bancomer"
    },
    "557910": {
        "brand": "Mastercard",
        "type": "Credit",
        "category": "Gold",
        "country": "Mexico",
        "bank": "Santander Mexico"
    }
}

def load_bin_database() -> Dict:
    """Load the BIN database from file or create a comprehensive one if it doesn't exist."""
    if os.path.exists(BIN_DATABASE_FILE):
        try:
            with open(BIN_DATABASE_FILE, 'r') as f:
                loaded_db = json.load(f)
                logger.info(f"Loaded BIN database with {len(loaded_db)} entries")
                return loaded_db
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading BIN database: {e}")
            # Fall back to built-in database
    
    # Create a comprehensive BIN database by combining all sources
    combined_db = {**CARD_NETWORK_BINS, **SPECIFIC_BINS}
    
    # Add BINs for more countries to ensure worldwide coverage
    more_countries = {
        # Spain
        "471491": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Spain", "bank": "BBVA"},
        "548519": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Spain", "bank": "Santander"},
        
        # Italy
        "432382": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Italy", "bank": "UniCredit"},
        "534025": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Italy", "bank": "Intesa Sanpaolo"},
        
        # Netherlands
        "412356": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Netherlands", "bank": "ING Bank"},
        "515941": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Netherlands", "bank": "ABN AMRO"},
        
        # Sweden
        "476701": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Sweden", "bank": "Nordea"},
        "527518": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Sweden", "bank": "SEB"},
        
        # Norway
        "422275": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Norway", "bank": "DNB"},
        "531980": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Norway", "bank": "Sparebank"},
        
        # Denmark
        "457382": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Denmark", "bank": "Danske Bank"},
        "559004": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Denmark", "bank": "Jyske Bank"},
        
        # Finland
        "402936": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Finland", "bank": "OP Bank"},
        "529756": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Finland", "bank": "Nordea Finland"},
        
        # Singapore
        "472836": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Singapore", "bank": "DBS Bank"},
        "522188": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Singapore", "bank": "OCBC Bank"},
        
        # Hong Kong
        "431673": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Hong Kong", "bank": "HSBC Hong Kong"},
        "518880": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Hong Kong", "bank": "Bank of China (HK)"},
        
        # South Korea
        "409538": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "South Korea", "bank": "KB Kookmin Bank"},
        "537043": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "South Korea", "bank": "Shinhan Bank"},
        
        # Indonesia
        "476285": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Indonesia", "bank": "Bank Mandiri"},
        "524435": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Indonesia", "bank": "BCA"},
        
        # Malaysia
        "483766": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Malaysia", "bank": "Maybank"},
        "552289": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Malaysia", "bank": "CIMB Bank"},
        
        # Thailand
        "492194": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Thailand", "bank": "Kasikornbank"},
        "526289": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Thailand", "bank": "Bangkok Bank"},
        
        # Vietnam
        "496212": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Vietnam", "bank": "Vietcombank"},
        "524523": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Vietnam", "bank": "BIDV"},
        
        # Philippines
        "428685": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Philippines", "bank": "BDO"},
        "533817": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Philippines", "bank": "BPI"},
        
        # Turkey
        "479633": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Turkey", "bank": "Garanti BBVA"},
        "525795": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Turkey", "bank": "Akbank"},
        
        # Israel
        "485234": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Israel", "bank": "Bank Leumi"},
        "543817": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Israel", "bank": "Bank Hapoalim"},
        
        # Saudi Arabia
        "440647": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Saudi Arabia", "bank": "Al Rajhi Bank"},
        "536924": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Saudi Arabia", "bank": "National Commercial Bank"},
        
        # Qatar
        "459360": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Qatar", "bank": "QNB"},
        "521076": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Qatar", "bank": "Masraf Al Rayan"},
        
        # Egypt
        "412123": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Egypt", "bank": "National Bank of Egypt"},
        "539154": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Egypt", "bank": "Commercial International Bank"},
        
        # Nigeria
        "419286": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Nigeria", "bank": "Zenith Bank"},
        "553188": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Nigeria", "bank": "GTBank"},
        
        # Kenya
        "465901": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Kenya", "bank": "Equity Bank"},
        "512834": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Kenya", "bank": "KCB Group"},
        
        # Argentina
        "423693": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Argentina", "bank": "Banco Galicia"},
        "542735": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Argentina", "bank": "Banco Santander Rio"},
        
        # Chile
        "493151": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Chile", "bank": "Banco de Chile"},
        "518154": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Chile", "bank": "Banco Santander Chile"},
        
        # Colombia
        "408593": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Colombia", "bank": "Bancolombia"},
        "516131": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Colombia", "bank": "Banco de Bogotá"},
        
        # Peru
        "451015": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Peru", "bank": "BCP"},
        "532123": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Peru", "bank": "Interbank"},
        
        # Pakistan
        "442732": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Pakistan", "bank": "HBL"},
        "535420": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Pakistan", "bank": "MCB Bank"},
        
        # Bangladesh
        "490670": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Bangladesh", "bank": "Eastern Bank"},
        "522156": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Bangladesh", "bank": "City Bank"},
        
        # New Zealand
        "462287": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "New Zealand", "bank": "ANZ NZ"},
        "519714": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "New Zealand", "bank": "BNZ"},
        
        # Greece
        "413081": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Greece", "bank": "Alpha Bank"},
        "528680": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Greece", "bank": "Piraeus Bank"},
        
        # Poland
        "417004": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Poland", "bank": "PKO Bank Polski"},
        "535294": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Poland", "bank": "Pekao SA"},
        
        # Czech Republic
        "416681": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Czech Republic", "bank": "Česká spořitelna"},
        "514212": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Czech Republic", "bank": "ČSOB"},
        
        # Hungary
        "474340": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Hungary", "bank": "OTP Bank"},
        "511103": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Hungary", "bank": "K&H Bank"},
        
        # Romania
        "455625": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Romania", "bank": "Banca Transilvania"},
        "525383": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Romania", "bank": "BCR"},
        
        # Bulgaria
        "447309": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Bulgaria", "bank": "DSK Bank"},
        "543785": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Bulgaria", "bank": "Postbank"},
        
        # Serbia
        "428964": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Serbia", "bank": "Banca Intesa"},
        "527863": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Serbia", "bank": "Raiffeisen Bank"},
        
        # Croatia
        "472163": {"brand": "Visa", "type": "Credit", "category": "Classic", "country": "Croatia", "bank": "Zagrebačka banka"},
        "529897": {"brand": "Mastercard", "type": "Credit", "category": "Gold", "country": "Croatia", "bank": "PBZ"}
    }
    
    # Merge the additional country BINs into combined_db
    combined_db.update(more_countries)
    
    # Save the comprehensive database to file
    try:
        with open(BIN_DATABASE_FILE, 'w') as f:
            json.dump(combined_db, f, indent=2)
        logger.info(f"Created and saved comprehensive BIN database with {len(combined_db)} entries")
    except IOError as e:
        logger.error(f"Error saving BIN database: {e}")
    
    return combined_db

# Load BIN database on module import
bin_database = load_bin_database()

def lookup_bin(bin_code: str) -> Dict:
    """
    Look up a BIN code in the database.
    
    Args:
        bin_code: The BIN code to look up (first 6 digits of a card number).
        
    Returns:
        A dictionary with BIN information.
    """
    # Clean the bin_code to ensure it's digits only
    bin_code = ''.join(c for c in bin_code if c.isdigit())
    
    if not bin_code:
        return {
            "brand": "Unknown",
            "type": "Unknown",
            "category": "Unknown",
            "country": "Unknown",
            "bank": "Unknown"
        }
    
    # Always look in the global database first, which may have been updated
    if bin_code in bin_database:
        return bin_database[bin_code]
    
    # Try exact 6-digit match first
    bin_6 = bin_code[:6] if len(bin_code) >= 6 else bin_code
    if bin_6 in bin_database:
        return bin_database[bin_6]
    
    # Try partial matches of different lengths
    for length in range(5, 0, -1):
        if len(bin_code) >= length:
            bin_prefix = bin_code[:length]
            
            # Look for exact match at this length
            if bin_prefix in bin_database:
                return bin_database[bin_prefix]
            
            # Look for keys starting with this prefix
            for key in bin_database:
                if key.startswith(bin_prefix) and len(key) >= length:
                    return bin_database[key]
    
    # Fallback to basic card network identification based on first digit
    # This ensures we always return some useful information
    first_digit = bin_code[0] if bin_code else ""
    basic_info = {
        "1": {"brand": "Various", "type": "Various", "category": "Various", "country": "International", "bank": "Various"},
        "2": {"brand": "Various", "type": "Various", "category": "Various", "country": "International", "bank": "Various"},
        "3": {"brand": "American Express/Diners Club", "type": "Credit", "category": "Premium", "country": "International", "bank": "Various"},
        "4": {"brand": "Visa", "type": "Credit/Debit", "category": "Various", "country": "International", "bank": "Various"},
        "5": {"brand": "Mastercard", "type": "Credit/Debit", "category": "Various", "country": "International", "bank": "Various"},
        "6": {"brand": "Discover/UnionPay", "type": "Credit/Debit", "category": "Various", "country": "International", "bank": "Various"},
        "7": {"brand": "Various", "type": "Various", "category": "Various", "country": "International", "bank": "Various"},
        "8": {"brand": "Various", "type": "Various", "category": "Various", "country": "International", "bank": "Various"},
        "9": {"brand": "Various", "type": "Various", "category": "Various", "country": "International", "bank": "Various"},
    }
    
    if first_digit in basic_info:
        return basic_info[first_digit]
    
    # Return a generic response if nothing found
    return {
        "brand": "Unknown",
        "type": "Unknown",
        "category": "Unknown",
        "country": "Unknown",
        "bank": "Unknown"
    }
