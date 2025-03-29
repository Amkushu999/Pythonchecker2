"""
Credit card utility functions for validation and generation.
Includes Luhn algorithm implementation for CC validation and generation.
"""
import random
import re
from typing import Dict, Any, List, Union, Tuple

from utils.bin_lookup import get_bin_info

def luhn_checksum(card_number: str) -> bool:
    """
    Validate a credit card number using the Luhn algorithm.
    
    Args:
        card_number: The credit card number to validate (string without spaces)
        
    Returns:
        True if valid per Luhn algorithm, False otherwise
    """
    # Remove any spaces or dashes
    card_number = card_number.replace(' ', '').replace('-', '')
    
    # Check if the card_number contains only digits
    if not card_number.isdigit():
        return False
        
    # Convert to list of integers
    digits = [int(digit) for digit in card_number]
    
    # Double every second digit from right to left
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
            
    # Sum all digits
    total = sum(digits)
    
    # Check if the sum is divisible by 10
    return total % 10 == 0

def generate_luhn_digit(partial_card_number: str) -> str:
    """
    Generate the Luhn check digit for a partial card number.
    
    Args:
        partial_card_number: The partial credit card number without the check digit
        
    Returns:
        The check digit as a string
    """
    # Remove any spaces or dashes
    partial_card_number = partial_card_number.replace(' ', '').replace('-', '')
    
    # Verify the partial card number contains only digits
    if not partial_card_number.isdigit():
        raise ValueError("Card number must contain only digits")
        
    # Convert to list of integers
    digits = [int(digit) for digit in partial_card_number]
    
    # Append a placeholder for the check digit
    digits.append(0)
    
    # Double every second digit from right to left
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
            
    # Calculate the check digit
    total = sum(digits)
    check_digit = (10 - (total % 10)) % 10
    
    return str(check_digit)

def validate_bin(bin_prefix: str) -> bool:
    """
    Validate if a BIN (Bank Identification Number) exists.
    
    Args:
        bin_prefix: The first 6 digits of a credit card number
        
    Returns:
        True if the BIN exists, False otherwise
    """
    # Clean up the bin prefix
    bin_prefix = bin_prefix.replace(' ', '').replace('-', '')
    
    # Check if the BIN has the correct length and contains only digits
    if not bin_prefix.isdigit() or len(bin_prefix) < 4 or len(bin_prefix) > 8:
        return False
        
    # Get BIN info to check if it exists
    bin_info = get_bin_info(bin_prefix[:6])
    
    # If the BIN lookup returns Unknown for both bank and brand, it probably doesn't exist
    if bin_info.get('bank') == 'Unknown' and bin_info.get('brand') == 'Unknown':
        # Try using hard-coded rules to validate the BIN
        return validate_bin_with_rules(bin_prefix)
    else:
        # BIN exists in our database
        return True

def validate_bin_with_rules(bin_prefix: str) -> bool:
    """
    Validate a BIN using hard-coded rules for major card networks.
    
    Args:
        bin_prefix: The first 6 digits of a credit card number
        
    Returns:
        True if the BIN is valid according to card network rules, False otherwise
    """
    # Visa - starts with 4
    if bin_prefix.startswith('4'):
        return True
        
    # Mastercard - starts with 51-55 or 2221-2720
    if bin_prefix.startswith('5') and '1' <= bin_prefix[1] <= '5':
        return True
    if bin_prefix.startswith('2') and (
        ('221' <= bin_prefix[1:4] <= '272' and len(bin_prefix) >= 4) or
        ('2' <= bin_prefix[1] <= '7' and bin_prefix[2] == '0')
    ):
        return True
        
    # American Express - starts with 34 or 37
    if bin_prefix.startswith('34') or bin_prefix.startswith('37'):
        return True
        
    # Discover - starts with 6011, 644-649, or 65
    if bin_prefix.startswith('6011') or \
       (bin_prefix.startswith('64') and '4' <= bin_prefix[2] <= '9') or \
       bin_prefix.startswith('65'):
        return True
        
    # JCB - starts with 35
    if bin_prefix.startswith('35'):
        return True
        
    # Diners Club - starts with 300-305, 36, or 38
    if bin_prefix.startswith('30') and '0' <= bin_prefix[2] <= '5':
        return True
    if bin_prefix.startswith('36') or bin_prefix.startswith('38'):
        return True
        
    # UnionPay - starts with 62
    if bin_prefix.startswith('62'):
        return True
        
    # Maestro - starts with 5018, 5020, 5038, 6304, 6759, 6761, 6762, 6763
    maestro_prefixes = ['5018', '5020', '5038', '6304', '6759', '6761', '6762', '6763']
    for prefix in maestro_prefixes:
        if bin_prefix.startswith(prefix):
            return True
            
    # If none of the above rules match, the BIN is probably invalid
    return False

def validate_credit_card(card: str, month: str = None, year: str = None, cvv: str = None) -> Tuple[bool, str]:
    """
    Validate a full credit card including Luhn check and optionally exp date and CVV.
    
    Args:
        card: The credit card number
        month: The expiration month (optional)
        year: The expiration year (optional)
        cvv: The card CVV (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Clean the card number
    card = card.replace(' ', '').replace('-', '')
    
    # Check if the card only has digits
    if not card.isdigit():
        return False, "Card number should contain only digits"
        
    # Check card length (most cards are 13-19 digits)
    if len(card) < 13 or len(card) > 19:
        return False, "Card number has invalid length"
        
    # Validate BIN
    if not validate_bin(card[:6]):
        return False, "Card has invalid BIN (bank identification number)"
        
    # Perform Luhn check
    if not luhn_checksum(card):
        return False, "Card failed Luhn algorithm validation"
        
    # Validate expiration date if provided
    if month and year:
        import datetime
        
        current_date = datetime.datetime.now()
        
        try:
            # Clean month and year
            month = month.strip().zfill(2)
            
            # Handle 2-digit or 4-digit year
            if len(year) == 2:
                year = f"20{year}"
            year = year.strip()
            
            # Parse as integers
            exp_month = int(month)
            exp_year = int(year)
            
            # Basic range validation
            if exp_month < 1 or exp_month > 12:
                return False, "Invalid expiration month"
                
            # Create expiration date (last day of the month)
            if exp_month == 12:
                exp_date = datetime.datetime(exp_year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                exp_date = datetime.datetime(exp_year, exp_month + 1, 1) - datetime.timedelta(days=1)
                
            # Check if card is expired
            if exp_date < current_date:
                return False, "Card is expired"
                
        except ValueError:
            return False, "Invalid expiration date format"
            
    # Validate CVV if provided
    if cvv:
        # Clean CVV
        cvv = cvv.strip()
        
        if not cvv.isdigit():
            return False, "CVV should contain only digits"
            
        # Get card brand to determine expected CVV length
        bin_info = get_bin_info(card[:6])
        brand = bin_info.get('brand', '').lower()
        
        # Amex requires 4-digit CVV, most others use 3 digits
        if brand == 'american express' and len(cvv) != 4:
            return False, "American Express cards require a 4-digit CVV"
        elif brand != 'american express' and len(cvv) != 3:
            return False, "Card requires a 3-digit CVV"
    
    # All validations passed
    return True, "Card is valid"

def bulk_validate_cards(card_list: List[str]) -> List[Dict[str, Any]]:
    """
    Validate a list of credit cards in bulk.
    
    Args:
        card_list: List of credit card numbers to validate
        
    Returns:
        List of dictionaries with validation results
    """
    results = []
    
    for card in card_list:
        # Clean card number
        clean_card = card.replace(' ', '').replace('-', '')
        
        # Parse card details if provided in format: CARD|MM|YY|CVV
        parts = card.split('|')
        
        if len(parts) >= 4:
            card_number = parts[0].strip()
            exp_month = parts[1].strip()
            exp_year = parts[2].strip()
            cvv = parts[3].strip()
            
            is_valid, message = validate_credit_card(card_number, exp_month, exp_year, cvv)
        else:
            # Just validate the card number
            is_valid, message = validate_credit_card(clean_card)
            
        results.append({
            'card': clean_card,
            'valid': is_valid,
            'message': message
        })
        
    return results

def generate_random_cc(bin_prefix: str = "", include_details: bool = True) -> Dict[str, str]:
    """
    Generate a random valid credit card number with optional additional details.
    The function validates that the BIN exists before generating a card.
    
    Args:
        bin_prefix: The BIN or prefix to use (default is empty, which uses a random valid BIN)
        include_details: Whether to include expiry and CVV details
        
    Returns:
        Dictionary with card details (number, expiry, cvv)
    """
    # Clean bin prefix
    bin_prefix = bin_prefix.replace(' ', '').replace('-', '')
    
    # If no BIN is provided, use a random valid BIN
    if not bin_prefix:
        # List of sample valid BINs for major card networks
        sample_bins = [
            '4', '51', '52', '53', '54', '55', '37', '34', '6011', '65', 
            '35', '30', '36', '38', '62'
        ]
        bin_prefix = random.choice(sample_bins)
    
    # Validate that the BIN exists
    if not validate_bin(bin_prefix):
        raise ValueError(f"Invalid BIN prefix: {bin_prefix}")
    
    # Generate a random card length based on the BIN
    card_length = 16  # Default for most cards
    
    # Adjust length based on card network
    if bin_prefix.startswith('34') or bin_prefix.startswith('37'):  # Amex
        card_length = 15
    elif bin_prefix.startswith('30') or bin_prefix.startswith('36') or bin_prefix.startswith('38'):  # Diners
        card_length = 14
    elif bin_prefix.startswith('35'):  # JCB
        card_length = 16
    
    # Generate random digits to fill the card number
    remaining_length = card_length - len(bin_prefix) - 1  # -1 for check digit
    if remaining_length <= 0:
        # If bin_prefix is already too long, truncate it
        bin_prefix = bin_prefix[:card_length-1]
        remaining_length = card_length - len(bin_prefix) - 1
    
    random_digits = ''.join([str(random.randint(0, 9)) for _ in range(remaining_length)])
    partial_card = bin_prefix + random_digits
    
    # Generate the check digit
    check_digit = generate_luhn_digit(partial_card)
    
    # Complete card number
    card_number = partial_card + check_digit
    
    # If details are requested, generate expiry and CVV
    result = {'cc': card_number}
    
    if include_details:
        # Generate random expiry date (1-5 years in the future)
        import datetime
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        
        # Random future year (1-5 years ahead)
        future_year = current_year + random.randint(1, 5)
        
        # Random month (if same year as current, ensure month is in the future)
        if future_year == current_year:
            future_month = random.randint(current_month, 12)
        else:
            future_month = random.randint(1, 12)
        
        # Determine CVV length (Amex uses 4 digits, others use 3)
        cvv_length = 4 if bin_prefix.startswith('34') or bin_prefix.startswith('37') else 3
        
        result['month'] = str(future_month).zfill(2)
        result['year'] = str(future_year)
        result['cvv'] = ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])
    
    return result

def generate_cards_with_bin(bin_prefix: str, count: int = 10, include_details: bool = True) -> List[Dict[str, str]]:
    """
    Generate multiple valid credit cards with the same BIN.
    
    Args:
        bin_prefix: The BIN to use for all generated cards
        count: Number of cards to generate
        include_details: Whether to include expiry and CVV details
        
    Returns:
        List of dictionaries with card details
    """
    if count < 1:
        raise ValueError("Count must be at least 1")
        
    if count > 100:
        raise ValueError("Cannot generate more than 100 cards at once")
    
    # Validate the BIN first
    if not validate_bin(bin_prefix):
        raise ValueError(f"Invalid BIN prefix: {bin_prefix}")
    
    cards = []
    for _ in range(count):
        cards.append(generate_random_cc(bin_prefix, include_details))
    
    return cards

def format_credit_card(card_number: str, format_type: str = 'default') -> str:
    """
    Format a credit card number according to the specified format.
    
    Args:
        card_number: The credit card number to format
        format_type: The type of formatting to apply ('default', 'dashed', 'spaced')
        
    Returns:
        Formatted card number string
    """
    # Clean the card number
    card_number = card_number.replace(' ', '').replace('-', '')
    
    if format_type == 'default':
        # Most cards use groups of 4 digits
        if len(card_number) == 15:  # AMEX
            return f"{card_number[:4]} {card_number[4:10]} {card_number[10:]}"
        else:
            parts = [card_number[i:i+4] for i in range(0, len(card_number), 4)]
            return ' '.join(parts)
    
    elif format_type == 'dashed':
        # Format with dashes between groups
        if len(card_number) == 15:  # AMEX
            return f"{card_number[:4]}-{card_number[4:10]}-{card_number[10:]}"
        else:
            parts = [card_number[i:i+4] for i in range(0, len(card_number), 4)]
            return '-'.join(parts)
    
    elif format_type == 'spaced':
        # Format with spaces between every 4 digits
        parts = [card_number[i:i+4] for i in range(0, len(card_number), 4)]
        return ' '.join(parts)
    
    elif format_type == 'none':
        # No formatting
        return card_number
    
    else:
        # Default to no formatting if an invalid format type is specified
        return card_number