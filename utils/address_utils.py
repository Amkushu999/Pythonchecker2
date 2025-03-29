"""
Utility functions for generating realistic fake addresses for different countries.
"""
import random
import string
from typing import Dict, Any

# Data for United States addresses
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
}

US_CITIES = {
    "NY": ["New York", "Buffalo", "Rochester", "Yonkers", "Syracuse"],
    "CA": ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "Fresno"],
    "TX": ["Houston", "San Antonio", "Dallas", "Austin", "Fort Worth"],
    "FL": ["Miami", "Jacksonville", "Tampa", "Orlando", "St. Petersburg"],
    "IL": ["Chicago", "Aurora", "Rockford", "Joliet", "Naperville"]
}

# Data for United Kingdom addresses
UK_COUNTIES = {
    "London": ["London"],
    "Lancashire": ["Manchester", "Liverpool", "Blackpool", "Preston", "Burnley"],
    "Yorkshire": ["Leeds", "Sheffield", "York", "Bradford", "Huddersfield"],
    "Essex": ["Chelmsford", "Southend-on-Sea", "Colchester", "Basildon", "Harlow"],
    "Kent": ["Canterbury", "Dover", "Maidstone", "Ashford", "Tunbridge Wells"]
}

UK_POSTCODES = {
    "London": ["E1 6AN", "SW1A 1AA", "W1A 0AX", "EC1A 1BB", "NW1 5TL"],
    "Lancashire": ["M1 1AA", "L1 8JQ", "PR1 2AB", "BL1 1DF", "BB11 1PF"],
    "Yorkshire": ["LS1 1UR", "S1 2BJ", "YO1 9QR", "BD1 1PT", "HD1 2TQ"],
    "Essex": ["CM1 1QH", "SS1 1PJ", "CO1 1NP", "SS13 1FE", "CM20 1XA"],
    "Kent": ["CT1 2HX", "CT17 9AZ", "ME14 1HH", "TN23 1QR", "TN1 1BT"]
}

# Data for Canada addresses
CA_PROVINCES = {
    "ON": "Ontario",
    "QC": "Quebec",
    "BC": "British Columbia",
    "AB": "Alberta",
    "MB": "Manitoba",
    "SK": "Saskatchewan",
    "NS": "Nova Scotia",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "PE": "Prince Edward Island"
}

CA_CITIES = {
    "ON": ["Toronto", "Ottawa", "Mississauga", "Hamilton", "London"],
    "QC": ["Montreal", "Quebec City", "Laval", "Gatineau", "Sherbrooke"],
    "BC": ["Vancouver", "Victoria", "Surrey", "Burnaby", "Richmond"],
    "AB": ["Calgary", "Edmonton", "Red Deer", "Lethbridge", "Fort McMurray"],
    "MB": ["Winnipeg", "Brandon", "Steinbach", "Thompson", "Portage la Prairie"]
}

# Data for Australian addresses
AU_STATES = {
    "NSW": "New South Wales",
    "VIC": "Victoria",
    "QLD": "Queensland",
    "WA": "Western Australia",
    "SA": "South Australia",
    "TAS": "Tasmania",
    "ACT": "Australian Capital Territory",
    "NT": "Northern Territory"
}

AU_CITIES = {
    "NSW": ["Sydney", "Newcastle", "Wollongong", "Coffs Harbour", "Wagga Wagga"],
    "VIC": ["Melbourne", "Geelong", "Ballarat", "Bendigo", "Shepparton"],
    "QLD": ["Brisbane", "Gold Coast", "Sunshine Coast", "Cairns", "Townsville"],
    "WA": ["Perth", "Fremantle", "Bunbury", "Geraldton", "Albany"],
    "SA": ["Adelaide", "Mount Gambier", "Whyalla", "Port Lincoln", "Port Augusta"]
}

# Data for German addresses
DE_STATES = {
    "BW": "Baden-Württemberg",
    "BY": "Bavaria",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hesse",
    "NI": "Lower Saxony",
    "MV": "Mecklenburg-Vorpommern",
    "NW": "North Rhine-Westphalia",
    "RP": "Rhineland-Palatinate",
    "SL": "Saarland",
    "SN": "Saxony",
    "ST": "Saxony-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thuringia"
}

DE_CITIES = {
    "BW": ["Stuttgart", "Karlsruhe", "Mannheim", "Freiburg", "Heidelberg"],
    "BY": ["Munich", "Nuremberg", "Augsburg", "Regensburg", "Würzburg"],
    "BE": ["Berlin"],
    "NW": ["Cologne", "Düsseldorf", "Dortmund", "Essen", "Duisburg"]
}

# Common street names for different countries
STREET_NAMES = {
    "US": ["Main St", "Oak St", "Maple Ave", "Washington Blvd", "Park Ave", 
           "Elm St", "Cedar Ln", "Pine St", "Broadway", "Highland Ave"],
    "UK": ["High Street", "Station Road", "Church Street", "Park Road", "London Road", 
           "Victoria Road", "Green Lane", "Manor Road", "Kings Road", "Queens Road"],
    "CA": ["Yonge St", "King St", "Queen St", "Bloor St", "Bay St", 
           "Dundas St", "College St", "Sherbrooke St", "Portage Ave", "Jasper Ave"],
    "AU": ["George St", "Pitt St", "Collins St", "Bourke St", "Elizabeth St", 
           "King St", "William St", "Queen St", "Market St", "Flinders St"],
    "DE": ["Hauptstraße", "Schulstraße", "Bahnhofstraße", "Gartenstraße", "Dorfstraße", 
           "Bergstraße", "Kirchstraße", "Waldstraße", "Parkstraße", "Lindenstraße"]
}

# Common first and last names
FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
    "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"
]

def generate_fake_address(country_code: str = "US") -> Dict[str, str]:
    """
    Generate a fake address for the specified country.
    
    Args:
        country_code: Two-letter country code (US, UK, CA, AU, DE)
        
    Returns:
        Dictionary containing fake address details
    """
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Common elements for all addresses
    address = {
        "name": f"{first_name} {last_name}",
        "email": f"{first_name.lower()}.{last_name.lower()}@example.com".replace(" ", ""),
    }
    
    if country_code == "US":
        state_code = random.choice(list(US_STATES.keys()))
        state = US_STATES[state_code]
        city = random.choice(US_CITIES.get(state_code, ["Springfield"]))
        
        house_number = random.randint(1, 9999)
        street = random.choice(STREET_NAMES["US"])
        zip_code = f"{random.randint(10000, 99999)}"
        phone = f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        address.update({
            "street": f"{house_number} {street}",
            "city": city,
            "state": state,
            "state_code": state_code,
            "zip": zip_code,
            "phone": phone,
            "country": "United States",
            "country_code": "US"
        })
    
    elif country_code == "UK" or country_code == "GB":
        county = random.choice(list(UK_COUNTIES.keys()))
        city = random.choice(UK_COUNTIES[county])
        postcode = random.choice(UK_POSTCODES.get(county, ["SW1A 1AA"]))
        
        house_number = random.randint(1, 200)
        street = random.choice(STREET_NAMES["UK"])
        phone = f"07{random.randint(100, 999)} {random.randint(100, 999)} {random.randint(100, 999)}"
        
        address.update({
            "street": f"{house_number} {street}",
            "city": city,
            "state": county,
            "state_code": "",
            "zip": postcode,
            "phone": phone,
            "country": "United Kingdom",
            "country_code": "GB"
        })
    
    elif country_code == "CA":
        province_code = random.choice(list(CA_PROVINCES.keys()))
        province = CA_PROVINCES[province_code]
        city = random.choice(CA_CITIES.get(province_code, ["Toronto"]))
        
        house_number = random.randint(1, 9999)
        street = random.choice(STREET_NAMES["CA"])
        
        # Canadian postal code format: A1A 1A1
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=3))
        postal_code = f"{letters[0]}{numbers[0]}{letters[1]} {numbers[1]}{letters[2]}{numbers[2]}"
        
        phone = f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        address.update({
            "street": f"{house_number} {street}",
            "city": city,
            "state": province,
            "state_code": province_code,
            "zip": postal_code,
            "phone": phone,
            "country": "Canada",
            "country_code": "CA"
        })
    
    elif country_code == "AU":
        state_code = random.choice(list(AU_STATES.keys()))
        state = AU_STATES[state_code]
        city = random.choice(AU_CITIES.get(state_code, ["Sydney"]))
        
        house_number = random.randint(1, 200)
        street = random.choice(STREET_NAMES["AU"])
        postcode = f"{random.randint(1000, 9999)}"
        phone = f"04{random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"
        
        address.update({
            "street": f"{house_number} {street}",
            "city": city,
            "state": state,
            "state_code": state_code,
            "zip": postcode,
            "phone": phone,
            "country": "Australia",
            "country_code": "AU"
        })
    
    elif country_code == "DE":
        state_code = random.choice(list(DE_STATES.keys()))
        state = DE_STATES[state_code]
        
        # For Berlin, use the same value
        if state_code == "BE":
            city = "Berlin"
        else:
            city = random.choice(DE_CITIES.get(state_code, ["Munich"]))
        
        house_number = random.randint(1, 200)
        street = random.choice(STREET_NAMES["DE"])
        postcode = f"{random.randint(10000, 99999)}"
        phone = f"0{random.randint(151, 179)} {random.randint(1000000, 9999999)}"
        
        address.update({
            "street": f"{street} {house_number}",  # In Germany, street name comes first
            "city": city,
            "state": state,
            "state_code": state_code,
            "zip": postcode,
            "phone": phone,
            "country": "Germany",
            "country_code": "DE"
        })
    
    else:
        # Default to US if country code is not recognized
        state_code = random.choice(list(US_STATES.keys()))
        state = US_STATES[state_code]
        city = random.choice(US_CITIES.get(state_code, ["Springfield"]))
        
        house_number = random.randint(1, 9999)
        street = random.choice(STREET_NAMES["US"])
        zip_code = f"{random.randint(10000, 99999)}"
        phone = f"({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        address.update({
            "street": f"{house_number} {street}",
            "city": city,
            "state": state,
            "state_code": state_code,
            "zip": zip_code,
            "phone": phone,
            "country": "United States",
            "country_code": "US"
        })
    
    return address