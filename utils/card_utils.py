"""
Credit card utilities for validation and generation.
"""
import re
import random
import string
from typing import Dict, Union, List, Optional

def validate_cc_format(cc_number: str, month: str, year: str, cvv: str) -> bool:
    """
    Validate credit card format.
    
    Args:
        cc_number: Credit card number.
        month: Expiry month.
        year: Expiry year.
        cvv: CVV code.
        
    Returns:
        True if the format is valid, False otherwise.
    """
    # Validate card number (digits only, length 13-19)
    if not re.match(r'^\d{13,19}$', cc_number):
        return False
    
    # Validate month (1-12)
    try:
        m = int(month)
        if m < 1 or m > 12:
            return False
    except ValueError:
        return False
    
    # Validate year (current year or future)
    import datetime
    current_year = datetime.datetime.now().year
    try:
        y = int(year)
        if len(year) == 2:
            y = 2000 + y
        if y < current_year:
            return False
    except ValueError:
        return False
    
    # Validate CVV (3-4 digits)
    if not re.match(r'^\d{3,4}$', cvv):
        return False
    
    return True

def generate_random_cc(bin_prefix: str = "") -> Dict[str, str]:
    """
    Generate a random credit card number with specified BIN prefix.
    
    Args:
        bin_prefix: The BIN prefix to use (optional).
        
    Returns:
        Dictionary with cc, month, year, and cvv.
    """
    # Generate card number
    if not bin_prefix:
        bin_prefix = random.choice(["4", "5", "3", "6"]) + "".join(random.choices(string.digits, k=5))
    
    # Ensure BIN prefix is digits only
    bin_prefix = re.sub(r'[^0-9]', '', bin_prefix)
    
    # Calculate the length needed
    remaining_length = 16 - len(bin_prefix)
    if remaining_length < 1:
        # Truncate if too long
        bin_prefix = bin_prefix[:15]
        remaining_length = 1
    
    # Generate the remaining digits
    cc_number = bin_prefix + "".join(random.choices(string.digits, k=remaining_length))
    
    # Generate expiry date
    import datetime
    current_year = datetime.datetime.now().year
    month = str(random.randint(1, 12)).zfill(2)
    year = str(random.randint(current_year + 1, current_year + 5))
    
    # Generate CVV
    cvv = "".join(random.choices(string.digits, k=3))
    
    return {
        "cc": cc_number,
        "month": month,
        "year": year,
        "cvv": cvv
    }

def generate_fake_address() -> Dict[str, str]:
    """
    Generate a fake US address.
    
    Returns:
        Dictionary with fake address details.
    """
    # Lists of common US names, streets, cities, states
    first_names = ["John", "Jane", "Robert", "Mary", "Michael", "Jennifer", "William", "Linda", "David", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
    
    street_names = ["Main", "Park", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington", "Lake", "Hill"]
    street_types = ["St", "Ave", "Blvd", "Rd", "Dr", "Ln", "Way", "Pl", "Ct", "Terrace"]
    
    cities = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", 
        "San Antonio", "San Diego", "Dallas", "San Jose"
    ]
    
    states = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", 
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", 
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", 
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", 
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York"
    }
    
    # Generate random components
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    full_name = f"{first_name} {last_name}"
    
    street_num = random.randint(100, 9999)
    street_name = random.choice(street_names)
    street_type = random.choice(street_types)
    street = f"{street_num} {street_name} {street_type}"
    
    city = random.choice(cities)
    state_abbr = random.choice(list(states.keys()))
    state = states[state_abbr]
    
    zip_code = f"{random.randint(10000, 99999)}"
    
    # Generate phone and email
    phone = f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
    
    return {
        "name": full_name,
        "street": street,
        "city": city,
        "state": f"{state} ({state_abbr})",
        "zip": zip_code,
        "phone": phone,
        "email": email
    }
