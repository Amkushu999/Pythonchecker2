"""
Credit card utilities for validation and generation.
"""
import re
import random
import string
from typing import Dict, Union, List, Optional

def luhn_check(card_number: str) -> bool:
    """
    Validate a card number using the Luhn algorithm.
    
    Args:
        card_number: The card number to validate.
        
    Returns:
        True if the card number is valid according to the Luhn algorithm, False otherwise.
    """
    # Remove any spaces or dashes
    card_number = card_number.replace(' ', '').replace('-', '')
    
    # Check if the card number contains only digits
    if not card_number.isdigit():
        return False
    
    # Convert to integers
    digits = [int(d) for d in card_number]
    
    # Double every second digit from right to left
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        # If doubling results in a number greater than 9, subtract 9
        if digits[i] > 9:
            digits[i] -= 9
    
    # Sum all digits
    total = sum(digits)
    
    # If the sum is divisible by 10, the card number is valid
    return total % 10 == 0

def validate_cc_format(cc_number: str, month: str, year: str, cvv: str) -> bool:
    """
    Validate credit card format and perform Luhn check.
    
    Args:
        cc_number: Credit card number.
        month: Expiry month.
        year: Expiry year.
        cvv: CVV code.
        
    Returns:
        True if the format is valid and passes Luhn check, False otherwise.
    """
    # Validate card number (digits only, length 13-19)
    if not re.match(r'^\d{13,19}$', cc_number):
        return False
    
    # Perform Luhn algorithm check
    if not luhn_check(cc_number):
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
    Generate a random credit card number with specified BIN prefix that passes Luhn check.
    
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
    
    # Calculate the length needed for a 16-digit card
    remaining_length = 16 - len(bin_prefix)
    if remaining_length < 1:
        # Truncate if too long
        bin_prefix = bin_prefix[:15]
        remaining_length = 1
    
    # Keep generating until we get a valid card number per Luhn algorithm
    while True:
        # Generate all but the last digit
        partial_number = bin_prefix
        if remaining_length > 1:
            partial_number += "".join(random.choices(string.digits, k=remaining_length - 1))
        
        # Calculate the check digit
        sum_digits = 0
        for i, digit in enumerate(reversed(partial_number)):
            d = int(digit)
            # Every second digit from the right is doubled
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            sum_digits += d
        
        # The check digit is the number that makes the sum divisible by 10
        check_digit = (10 - (sum_digits % 10)) % 10
        
        # Assemble the complete card number
        cc_number = partial_number + str(check_digit)
        
        # Verify the card passes Luhn check (defensive check)
        if luhn_check(cc_number):
            break
    
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

# Global data for address generation
COUNTRY_DATA = {
    "US": {
        "name": "United States",
        "first_names": ["John", "Jane", "Robert", "Mary", "Michael", "Jennifer", "William", "Linda", "David", "Elizabeth"],
        "last_names": ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"],
        "street_names": ["Main", "Park", "Oak", "Pine", "Maple", "Cedar", "Elm", "Washington", "Lake", "Hill"],
        "street_types": ["St", "Ave", "Blvd", "Rd", "Dr", "Ln", "Way", "Pl", "Ct", "Terrace"],
        "cities": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"],
        "states": {
            "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", 
            "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
            "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", 
            "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
            "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", 
            "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
            "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", 
            "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York"
        },
        "zip_format": "#####",
        "phone_format": "###-###-####"
    },
    "UK": {
        "name": "United Kingdom",
        "first_names": ["James", "Emma", "Harry", "Olivia", "George", "Sophie", "William", "Charlotte", "Thomas", "Amelia"],
        "last_names": ["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson", "Thomas", "Johnson"],
        "street_names": ["High", "Church", "Main", "Park", "Mill", "Station", "London", "Victoria", "Queens", "Kings"],
        "street_types": ["Street", "Road", "Avenue", "Lane", "Drive", "Place", "Way", "Close", "Grove", "Crescent"],
        "cities": ["London", "Birmingham", "Manchester", "Glasgow", "Liverpool", "Edinburgh", "Bristol", "Leeds", "Sheffield", "Newcastle"],
        "states": {
            "LDN": "London", "GLCS": "Gloucestershire", "ESSEX": "Essex", "SURY": "Surrey", 
            "KENT": "Kent", "HERTS": "Hertfordshire", "YORKS": "Yorkshire", "LANCS": "Lancashire",
            "MANC": "Manchester", "BUCKS": "Buckinghamshire"
        },
        "zip_format": "?# #??",  # UK Postcode format (e.g., M1 1AA)
        "phone_format": "0#### ######"
    },
    "CA": {
        "name": "Canada",
        "first_names": ["Liam", "Emma", "Noah", "Olivia", "William", "Ava", "Benjamin", "Sophia", "Lucas", "Charlotte"],
        "last_names": ["Smith", "Brown", "Tremblay", "Martin", "Roy", "Wilson", "Johnson", "MacDonald", "Gagnon", "Lee"],
        "street_names": ["Maple", "Oak", "Pine", "Cedar", "Birch", "Elm", "Main", "Queen", "King", "Victoria"],
        "street_types": ["Street", "Avenue", "Road", "Drive", "Boulevard", "Crescent", "Place", "Court", "Lane", "Way"],
        "cities": ["Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa", "Edmonton", "Winnipeg", "Quebec City", "Hamilton", "Halifax"],
        "states": {
            "ON": "Ontario", "QC": "Quebec", "BC": "British Columbia", "AB": "Alberta", 
            "MB": "Manitoba", "SK": "Saskatchewan", "NS": "Nova Scotia", "NB": "New Brunswick",
            "NL": "Newfoundland and Labrador", "PE": "Prince Edward Island"
        },
        "zip_format": "?#? #?#",  # Canadian Postal Code format (e.g., M5V 2A1)
        "phone_format": "###-###-####"
    },
    "AU": {
        "name": "Australia",
        "first_names": ["Oliver", "Charlotte", "Jack", "Ava", "William", "Mia", "Noah", "Olivia", "Lucas", "Amelia"],
        "last_names": ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Johnson", "White", "Martin", "Anderson"],
        "street_names": ["High", "Church", "Main", "Park", "George", "Victoria", "Albert", "Queen", "King", "Beach"],
        "street_types": ["Street", "Road", "Avenue", "Drive", "Court", "Place", "Lane", "Way", "Close", "Parade"],
        "cities": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Newcastle", "Canberra", "Wollongong", "Hobart"],
        "states": {
            "NSW": "New South Wales", "VIC": "Victoria", "QLD": "Queensland", "WA": "Western Australia",
            "SA": "South Australia", "TAS": "Tasmania", "ACT": "Australian Capital Territory", "NT": "Northern Territory"
        },
        "zip_format": "####",  # Australian Postal Code format
        "phone_format": "0# #### ####"
    },
    "DE": {
        "name": "Germany",
        "first_names": ["Maximilian", "Sophie", "Alexander", "Maria", "Paul", "Anna", "Leon", "Emma", "Felix", "Hannah"],
        "last_names": ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Hoffmann", "Schulz"],
        "street_names": ["Haupt", "Schul", "Garten", "Kirch", "Wald", "Berg", "Bach", "Wiesen", "Dorf", "Park"],
        "street_types": ["straße", "weg", "allee", "platz", "gasse", "ring", "damm", "ufer", "hof", "promenade"],
        "cities": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen"],
        "states": {
            "BW": "Baden-Württemberg", "BY": "Bavaria", "BE": "Berlin", "BB": "Brandenburg",
            "HB": "Bremen", "HH": "Hamburg", "HE": "Hesse", "NI": "Lower Saxony",
            "MV": "Mecklenburg-Vorpommern", "NW": "North Rhine-Westphalia", "RP": "Rhineland-Palatinate", "SL": "Saarland",
            "SN": "Saxony", "ST": "Saxony-Anhalt", "SH": "Schleswig-Holstein", "TH": "Thuringia"
        },
        "zip_format": "#####",  # German Postal Code format
        "phone_format": "0### ########"
    },
    "FR": {
        "name": "France",
        "first_names": ["Lucas", "Emma", "Gabriel", "Léa", "Louis", "Manon", "Jules", "Jade", "Hugo", "Chloé"],
        "last_names": ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau"],
        "street_names": ["Grande", "Petit", "Principal", "Église", "Moulin", "Château", "École", "Gare", "Paris", "Mairie"],
        "street_types": ["Rue", "Avenue", "Boulevard", "Place", "Chemin", "Impasse", "Allée", "Route", "Quai", "Cours"],
        "cities": ["Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille"],
        "states": {
            "IDF": "Île-de-France", "ARA": "Auvergne-Rhône-Alpes", "HDF": "Hauts-de-France", "PACA": "Provence-Alpes-Côte d'Azur",
            "GES": "Grand Est", "OCC": "Occitanie", "NOR": "Normandie", "NVA": "Nouvelle-Aquitaine",
            "BFC": "Bourgogne-Franche-Comté", "PDL": "Pays de la Loire", "BRE": "Bretagne", "COR": "Corse"
        },
        "zip_format": "#####",  # French Postal Code format
        "phone_format": "0# ## ## ## ##"
    },
    "JP": {
        "name": "Japan",
        "first_names": ["Haruto", "Yui", "Sota", "Aoi", "Yuito", "Hina", "Aoto", "Himari", "Ritsu", "Akari"],
        "last_names": ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura", "Kobayashi", "Kato"],
        "street_names": ["Sakura", "Fuji", "Higashi", "Nishi", "Minami", "Kita", "Chuo", "Heiwa", "Asahi", "Midori"],
        "street_types": ["dori", "koji", "oji", "kaido", "namiki", "suji", "guchi", "bashi"],
        "cities": ["Tokyo", "Yokohama", "Osaka", "Nagoya", "Sapporo", "Fukuoka", "Kobe", "Kyoto", "Kawasaki", "Saitama"],
        "states": {
            "TKY": "Tokyo", "OSK": "Osaka", "KNG": "Kanagawa", "AIC": "Aichi", "HKD": "Hokkaido",
            "FKO": "Fukuoka", "HYG": "Hyogo", "KYO": "Kyoto", "STM": "Saitama", "CHB": "Chiba"
        },
        "zip_format": "###-####",  # Japanese Postal Code format
        "phone_format": "0#-####-####"
    },
    "CN": {
        "name": "China",
        "first_names": ["Wei", "Jing", "Xin", "Yu", "Ming", "Hui", "Hao", "Li", "Yan", "Yong"],
        "last_names": ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou"],
        "street_names": ["Zhongshan", "Jianguo", "Renmin", "Xinhua", "Beijing", "Shanghai", "Huanghe", "Yangtze", "Guangming", "Changjiang"],
        "street_types": ["Lu", "Jie", "Dao", "Xiang", "Hutong"],
        "cities": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu", "Hangzhou", "Wuhan", "Xi'an", "Nanjing", "Tianjin"],
        "states": {
            "BJ": "Beijing", "SH": "Shanghai", "GD": "Guangdong", "JS": "Jiangsu", "ZJ": "Zhejiang",
            "SD": "Shandong", "HN": "Henan", "SC": "Sichuan", "HB": "Hubei", "HE": "Hebei"
        },
        "zip_format": "######",  # Chinese Postal Code format
        "phone_format": "1## #### ####"
    },
    "IN": {
        "name": "India",
        "first_names": ["Aarav", "Aadhya", "Arjun", "Ananya", "Vihaan", "Aanya", "Vivaan", "Diya", "Reyansh", "Aditi"],
        "last_names": ["Sharma", "Singh", "Kumar", "Patel", "Gupta", "Jain", "Shah", "Verma", "Rao", "Mehta"],
        "street_names": ["Gandhi", "Nehru", "Patel", "Tagore", "Shastri", "Bose", "Tilak", "Ambedkar", "Subhash", "Azad"],
        "street_types": ["Road", "Street", "Marg", "Nagar", "Chowk", "Galli", "Lane", "Colony", "Bagh", "Enclave"],
        "cities": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad", "Pune", "Jaipur", "Lucknow"],
        "states": {
            "MH": "Maharashtra", "DL": "Delhi", "KA": "Karnataka", "TG": "Telangana", "TN": "Tamil Nadu",
            "WB": "West Bengal", "GJ": "Gujarat", "RJ": "Rajasthan", "UP": "Uttar Pradesh", "MP": "Madhya Pradesh"
        },
        "zip_format": "######",  # Indian Postal Code format
        "phone_format": "+91 ## #### ####"
    },
    "BR": {
        "name": "Brazil",
        "first_names": ["Miguel", "Sophia", "Davi", "Alice", "Arthur", "Julia", "Pedro", "Isabella", "Gabriel", "Manuela"],
        "last_names": ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Ferreira", "Costa", "Rodrigues", "Almeida"],
        "street_names": ["Brasil", "São Paulo", "Rio", "Bahia", "Minas", "Santos", "Paulista", "Amazonas", "Getúlio Vargas", "Santos Dumont"],
        "street_types": ["Rua", "Avenida", "Alameda", "Praça", "Travessa", "Estrada", "Rodovia", "Viela", "Largo", "Boulevard"],
        "cities": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza", "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Porto Alegre"],
        "states": {
            "SP": "São Paulo", "RJ": "Rio de Janeiro", "DF": "Distrito Federal", "BA": "Bahia", "CE": "Ceará",
            "MG": "Minas Gerais", "AM": "Amazonas", "PR": "Paraná", "PE": "Pernambuco", "RS": "Rio Grande do Sul"
        },
        "zip_format": "#####-###",  # Brazilian Postal Code format
        "phone_format": "(##) ####-####"
    },
    "RU": {
        "name": "Russia",
        "first_names": ["Alexander", "Anastasia", "Dmitry", "Maria", "Ivan", "Olga", "Mikhail", "Anna", "Sergey", "Ekaterina"],
        "last_names": ["Ivanov", "Smirnov", "Kuznetsov", "Popov", "Vasiliev", "Petrov", "Sokolov", "Mikhailov", "Novikov", "Fedorov"],
        "street_names": ["Leninskiy", "Pushkin", "Gagarin", "Sovetskaya", "Moskovskaya", "Oktyabrskaya", "Mira", "Sadovaya", "Zelenaya", "Centralnaya"],
        "street_types": ["Prospekt", "Ulitsa", "Pereulok", "Ploshchad", "Shosse", "Naberezhnaya", "Bulvar", "Proyezd", "Tupik", "Alleya"],
        "cities": ["Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan", "Nizhny Novgorod", "Chelyabinsk", "Omsk", "Samara", "Rostov-on-Don"],
        "states": {
            "MOS": "Moscow", "SPB": "Saint Petersburg", "NSO": "Novosibirsk Oblast", "SVE": "Sverdlovsk Oblast", "TA": "Tatarstan",
            "NIZ": "Nizhny Novgorod Oblast", "CHE": "Chelyabinsk Oblast", "OMS": "Omsk Oblast", "SAM": "Samara Oblast", "ROS": "Rostov Oblast"
        },
        "zip_format": "######",  # Russian Postal Code format
        "phone_format": "+7 ### ###-##-##"
    }
}

def generate_fake_address(country_code: str = "US") -> Dict[str, str]:
    """
    Generate a fake address for the specified country.
    
    Args:
        country_code: Two-letter country code (e.g., US, UK, CA, etc.)
        
    Returns:
        Dictionary with fake address details.
    """
    # Clean and validate country code
    country_code = country_code.upper().strip()
    
    # Handle any country code not in our database
    if country_code not in COUNTRY_DATA:
        # If specific country data is not available, try to find a regional substitute
        regional_map = {
            # European countries defaulting to UK, DE, or FR
            "ES": "UK", "IT": "FR", "NL": "DE", "BE": "FR", "PT": "UK", 
            "AT": "DE", "CH": "DE", "SE": "UK", "NO": "UK", "DK": "UK", 
            "FI": "UK", "IE": "UK", "GR": "UK", "PL": "DE", "CZ": "DE",
            "HU": "DE", "RO": "UK", "BG": "UK", "HR": "DE", "SI": "DE",
            "SK": "DE", "LT": "UK", "LV": "UK", "EE": "UK", "LU": "DE",
            "MT": "UK", "CY": "UK", "RS": "DE", "UA": "RU", "BY": "RU",
            
            # Asian countries defaulting to JP, CN, or IN
            "KR": "JP", "TW": "CN", "HK": "CN", "SG": "JP", "MY": "JP",
            "TH": "JP", "VN": "JP", "PH": "JP", "ID": "JP", "PK": "IN",
            "BD": "IN", "NP": "IN", "LK": "IN", "MM": "IN", "KH": "JP",
            "LA": "JP", "MN": "CN", "KZ": "RU", "UZ": "RU", "KG": "RU",
            
            # Middle East defaulting to UK or IN
            "AE": "UK", "SA": "UK", "QA": "UK", "KW": "UK", "BH": "UK",
            "OM": "UK", "JO": "UK", "LB": "FR", "IL": "UK", "IR": "UK",
            "IQ": "UK", "SY": "UK", "YE": "UK",
            
            # African countries defaulting to UK or FR
            "ZA": "UK", "NG": "UK", "KE": "UK", "EG": "UK", "MA": "FR",
            "DZ": "FR", "TN": "FR", "GH": "UK", "CI": "FR", "SN": "FR",
            "CM": "FR", "AO": "PT", "MZ": "PT", "ZW": "UK", "UG": "UK",
            "TZ": "UK", "ET": "UK", "SD": "UK", "LY": "UK",
            
            # North American countries defaulting to US or CA
            "MX": "US", "GT": "US", "CR": "US", "PA": "US", "DO": "US",
            "JM": "UK", "TT": "UK", "BS": "US", "HN": "US", "SV": "US",
            "NI": "US", "CU": "US", "HT": "FR",
            
            # South American countries defaulting to BR
            "AR": "BR", "CL": "BR", "CO": "BR", "PE": "BR", "VE": "BR",
            "EC": "BR", "BO": "BR", "PY": "BR", "UY": "BR", "GY": "BR",
            "SR": "BR", "GF": "FR",
            
            # Oceania defaulting to AU
            "NZ": "AU", "FJ": "AU", "PG": "AU", "SB": "AU", "VU": "AU",
            "WS": "AU", "TO": "AU", "KI": "AU", "NC": "FR", "PF": "FR"
        }
        
        # Use regional substitute if available, otherwise default to US
        country_code = regional_map.get(country_code, "US")
    
    country_data = COUNTRY_DATA[country_code]
    
    # Generate random components
    first_name = random.choice(country_data["first_names"])
    last_name = random.choice(country_data["last_names"])
    full_name = f"{first_name} {last_name}"
    
    street_num = random.randint(1, 999)
    street_name = random.choice(country_data["street_names"])
    street_type = random.choice(country_data["street_types"])
    
    # Adjust format based on country conventions
    if country_code in ["JP", "CN", "KR", "TW"]:
        # East Asian format (street/block first, then number)
        street = f"{street_name} {street_type} {street_num}"
    elif country_code in ["RU", "UA", "BY", "KZ"]:
        # Russian style format
        street = f"{street_type} {street_name}, {street_num}"
    elif country_code in ["DE", "AT", "CH", "PL", "CZ", "SK", "HU"]:
        # German/Central European style
        street = f"{street_name}{street_type} {street_num}"
    else:
        # Default Western format (number first, then street)
        street = f"{street_num} {street_name} {street_type}"
    
    city = random.choice(country_data["cities"])
    state_abbr = random.choice(list(country_data["states"].keys()))
    state = country_data["states"][state_abbr]
    
    # Generate postal code using format
    zip_code = ""
    for char in country_data["zip_format"]:
        if char == "#":
            zip_code += str(random.randint(0, 9))
        elif char == "?":
            zip_code += random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        else:
            zip_code += char
    
    # Generate phone number using format
    phone = ""
    for char in country_data["phone_format"]:
        if char == "#":
            phone += str(random.randint(0, 9))
        else:
            phone += char
    
    # Generate email with locale-appropriate domain TLDs
    domain_tlds = {
        "US": ".com", "UK": ".co.uk", "CA": ".ca", "AU": ".com.au", 
        "DE": ".de", "FR": ".fr", "JP": ".jp", "CN": ".cn", 
        "IN": ".in", "BR": ".com.br", "RU": ".ru"
    }
    
    tld = domain_tlds.get(country_code, ".com")
    email_providers = ["gmail.com", "yahoo.com", "outlook.com", f"mail{tld}", f"example{tld}"]
    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{random.choice(email_providers)}"
    
    return {
        "name": full_name,
        "street": street,
        "city": city,
        "state": f"{state} ({state_abbr})",
        "zip": zip_code,
        "phone": phone,
        "email": email,
        "country": country_data["name"]
    }
